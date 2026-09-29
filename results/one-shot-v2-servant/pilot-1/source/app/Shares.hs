module Shares (Live, newLive, createShare, deleteShare, readShare, updateShare, broadcastUpdate, socketServer) where

import Articles (ownedArticle, updateChecked)
import Auth (requireUser)
import Control.Concurrent (forkIO, killThread)
import Control.Concurrent.STM (STM, TQueue, TVar, atomically, modifyTVar', newTQueue, newTVarIO, readTQueue, readTVar, writeTQueue, writeTVar)
import Control.Exception (SomeException, catch, finally)
import Control.Monad (forM_, forever, void)
import Control.Monad.IO.Class (liftIO)
import Crypto.Hash (Digest, SHA256, hash)
import Crypto.Random (getRandomBytes)
import Data.Aeson (Value (..), object, (.=))
import Data.Aeson qualified as Aeson
import Data.Aeson.Key qualified as Key
import Data.Aeson.KeyMap qualified as KM
import Data.ByteString qualified as BS
import Data.ByteString.Base64.URL qualified as B64
import Data.Map.Strict (Map)
import Data.Map.Strict qualified as Map
import Data.Maybe (fromMaybe)
import Data.Text (Text)
import Data.Text qualified as T
import Data.Text.Encoding qualified as TE
import Data.UUID qualified as UUID
import Data.UUID.V4 qualified as UUID
import Db (Db, runSql)
import Domain (failure, field, intField, objectField, requiredText, textField, validateShareEdit, wrap)
import Network.WebSockets (Connection, PendingConnection, ServerApp)
import Network.WebSockets qualified as WS
import Servant (Handler)
import System.Timeout (timeout)

data Live = Live {rooms :: TVar (Map Text (Map Int (TQueue Value))), nextClient :: TVar Int, database :: Db}

newLive :: Db -> IO Live
newLive db = Live <$> newTVarIO Map.empty <*> newTVarIO 0 <*> pure db

keyDigest :: Text -> Text
keyDigest = T.pack . show . (hash :: BS.ByteString -> Digest SHA256) . TE.encodeUtf8

shareRecord :: Live -> Text -> Maybe Text -> IO Value
shareRecord live ident key = runSql (database live) "SELECT COALESCE((SELECT jsonb_build_object('id',a.id,'article',article_payload(a,NULL,true),'shared',shared_payload(a)) FROM shares s JOIN articles a ON a.id=s.article_id WHERE s.id=$1->>'id' AND s.key_hash=$1->>'hash'),'null'::jsonb)" (object ["id" .= ident, "hash" .= fmap keyDigest key])

validShare :: Live -> Text -> Maybe Text -> Handler Value
validShare live ident key = do
    row <- liftIO (shareRecord live ident key)
    if row == Null then failure 404 "share" "not found" else pure row

createShare :: Live -> Text -> Maybe Text -> Text -> Handler Value
createShare live secret auth slug = do
    user <- requireUser (database live) secret auth
    item <- ownedArticle (database live) (fromMaybe 0 (intField "id" user)) slug
    old <- liftIO $ runSql (database live) "SELECT COALESCE((SELECT to_jsonb(s.id) FROM shares s WHERE s.article_id=($1->>'id')::bigint),'null'::jsonb)" (object ["id" .= intField "id" item])
    ident <- liftIO (UUID.toText <$> UUID.nextRandom)
    bytes <- liftIO (getRandomBytes 32 :: IO BS.ByteString)
    let secretKey = TE.decodeUtf8 (B64.encodeUnpadded bytes)
    _ <- liftIO $ runSql (database live) "WITH s AS (INSERT INTO shares(id,article_id,key_hash) VALUES ($1->>'id',($1->>'articleId')::bigint,$1->>'hash') ON CONFLICT(article_id) DO UPDATE SET id=EXCLUDED.id,key_hash=EXCLUDED.key_hash,created_at=now() RETURNING id) SELECT to_jsonb(s.id) FROM s" (object ["id" .= ident, "articleId" .= intField "id" item, "hash" .= keyDigest secretKey])
    case old of String previous -> liftIO (revoke live previous); _ -> pure ()
    pure (wrap "share" (object ["id" .= ident, "key" .= secretKey]))

deleteShare :: Live -> Text -> Maybe Text -> Text -> Handler ()
deleteShare live secret auth slug = do
    user <- requireUser (database live) secret auth
    item <- ownedArticle (database live) (fromMaybe 0 (intField "id" user)) slug
    old <- liftIO $ runSql (database live) "WITH d AS (DELETE FROM shares WHERE article_id=($1->>'id')::bigint RETURNING id) SELECT COALESCE((SELECT to_jsonb(id) FROM d),'null'::jsonb)" (object ["id" .= intField "id" item])
    case old of String previous -> liftIO (revoke live previous); _ -> pure ()

readShare :: Live -> Text -> Maybe Text -> Handler Value
readShare live ident key = do
    row <- validShare live ident key
    pure (wrap "article" (objectField "shared" row))

updateShare :: Live -> Text -> Maybe Text -> Value -> Handler Value
updateShare live ident key input = do
    row <- validShare live ident key
    let body = objectField "article" input
    case body of
        Object o | Map.fromList [(Key.toText k, ()) | k <- KM.keys o] == Map.fromList [(k, ()) | k <- ["title", "body", "revision"]] -> pure ()
        _ -> failure 422 "article" "is invalid"
    (title, content, revision) <- validateShareEdit body
    let item = object ["id" .= intField "id" row, "article" .= objectField "article" row]
    updateChecked (database live) 0 item (Just revision) (Just title) Nothing (Just content) Nothing (broadcastUpdate live) True

broadcastUpdate :: Live -> Value -> IO ()
broadcastUpdate live event = do
    active <- runSql (database live) "SELECT COALESCE((SELECT to_jsonb(s.id) FROM shares s WHERE s.article_id=($1->>'articleId')::bigint),'null'::jsonb)" event
    case active of
        String ident -> atomically $ sendRoom live ident (object ["type" .= ("updated" :: Text), "article" .= shared (objectField "article" event)])
        _ -> pure ()
  where
    shared a = object ["slug" .= textField "slug" a, "title" .= textField "title" a, "body" .= textField "body" a, "revision" .= intField "revision" a]

sendRoom :: Live -> Text -> Value -> STM ()
sendRoom live ident value = do
    allRooms <- readTVar (rooms live)
    forM_ (Map.elems (Map.findWithDefault Map.empty ident allRooms)) (`writeTQueue` value)

revoke :: Live -> Text -> IO ()
revoke live ident = atomically (sendRoom live ident (object ["type" .= ("revoked" :: Text)]))

admit :: Live -> Text -> STM (Maybe (Int, TQueue Value, Int))
admit live ident = do
    allRooms <- readTVar (rooms live)
    let room = Map.findWithDefault Map.empty ident allRooms
    if Map.size room >= 100
        then pure Nothing
        else do
            identNum <- readTVar (nextClient live)
            writeTVar (nextClient live) (identNum + 1)
            queue <- newTQueue
            let count = Map.size room + 1
            writeTVar (rooms live) (Map.insert ident (Map.insert identNum queue room) allRooms)
            sendRoom live ident (object ["type" .= ("presence" :: Text), "count" .= count])
            pure (Just (identNum, queue, count))

depart :: Live -> Text -> Int -> IO ()
depart live ident client = atomically $ do
    allRooms <- readTVar (rooms live)
    let room = Map.delete client (Map.findWithDefault Map.empty ident allRooms)
    writeTVar (rooms live) (if Map.null room then Map.delete ident allRooms else Map.insert ident room allRooms)
    sendRoom live ident (object ["type" .= ("presence" :: Text), "count" .= Map.size room])

socketServer :: Live -> ServerApp
socketServer live pending = do
    let parts = T.splitOn "/" (TE.decodeUtf8 (WS.requestPath (WS.pendingRequest pending)))
    connection <- WS.acceptRequest pending
    case parts of
        ["", "api", "shares", ident, "live"] -> serveRoom ident connection
        _ -> WS.sendClose connection ("invalid path" :: Text)
  where
    serveRoom ident connection = do
        first <- timeout 5000000 (WS.receiveData connection :: IO BS.ByteString)
        case first >>= Aeson.decodeStrict' of
            Just message | textField "type" message == Just "subscribe" -> do
                row <- shareRecord live ident (textField "key" message)
                if row == Null
                    then reject connection "invalid_link"
                    else do
                        admission <- atomically (admit live ident)
                        case admission of
                            Nothing -> do
                                WS.sendTextData connection (Aeson.encode (object ["type" .= ("room_full" :: Text), "limit" .= (100 :: Int)]))
                                WS.sendClose connection ("full" :: Text)
                            Just (client, queue, count) -> do
                                latest <- shareRecord live ident (textField "key" message)
                                if latest == Null
                                    then do
                                        depart live ident client
                                        reject connection "revoked"
                                    else do
                                        let initial = objectField "shared" latest
                                        WS.sendTextData connection (Aeson.encode (object ["type" .= ("ready" :: Text), "article" .= initial, "presence" .= count]))
                                        sender <- forkIO (sendLoop connection queue (fromMaybe 0 (intField "revision" initial)))
                                        (forever (void (WS.receiveData connection :: IO BS.ByteString)) `catch` ignore) `finally` (killThread sender >> depart live ident client)
            _ -> reject connection "invalid_link"
    reject connection kind = do
        WS.sendTextData connection (Aeson.encode (object ["type" .= (kind :: Text)]))
        WS.sendClose connection kind
    sendLoop connection queue lastRev = do
        value <- atomically (readTQueue queue)
        let revision = intField "revision" (objectField "article" value)
        if textField "type" value == Just "updated" && maybe False (<= lastRev) revision
            then sendLoop connection queue lastRev
            else do
                WS.sendTextData connection (Aeson.encode value)
                if textField "type" value == Just "revoked"
                    then WS.sendClose connection ("revoked" :: Text)
                    else sendLoop connection queue (fromMaybe lastRev revision)
    ignore :: SomeException -> IO ()
    ignore _ = pure ()
