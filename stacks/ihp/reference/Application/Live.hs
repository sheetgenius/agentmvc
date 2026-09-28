{-# LANGUAGE DataKinds                 #-}
{-# LANGUAGE ImplicitParams            #-}
{-# LANGUAGE NoImplicitPrelude         #-}
{-# LANGUAGE NoMonomorphismRestriction #-}
{-# LANGUAGE OverloadedRecordDot       #-}
{-# LANGUAGE OverloadedStrings         #-}
{-# LANGUAGE PackageImports            #-}
{-# LANGUAGE QuasiQuotes               #-}
{-# LANGUAGE TypeApplications          #-}
module Application.Live (LiveSocket (..), broadcastUpdate, revoke, keyHash) where

import Application.TypedSql
import Control.Concurrent.MVar
import Control.Exception (finally)
import Control.Monad (join)
import "cryptonite" Crypto.Hash (Digest, SHA256 (..), hashWith)
import qualified Data.Aeson as J
import qualified Data.Aeson.Key as K
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteString.Lazy as LBS
import Data.Coerce (coerce)
import Data.Int (Int)
import Data.IORef
import qualified Data.Map.Strict as Map
import Data.Maybe (fromMaybe, listToMaybe)
import qualified Data.Text as T
import qualified Data.Text.Encoding as TE
import Generated.ActualTypes.PrimaryKeys ()
import IHP.ModelSupport.Types (Id' (..))
import IHP.Prelude
import IHP.WebSocket (WSApp (..))
import qualified Network.WebSockets as WS
import System.IO.Unsafe (unsafePerformIO)
import System.Timeout (timeout)

newtype LiveSocket = LiveSocket T.Text deriving (Eq, Show)
type Room = Map.Map Int WS.Connection
rooms :: MVar (Map.Map T.Text Room)
rooms = unsafePerformIO (newMVar Map.empty)
{-# NOINLINE rooms #-}
sequenceId :: IORef Int
sequenceId = unsafePerformIO (newIORef 0)
{-# NOINLINE sequenceId #-}

keyHash value = show (hashWith SHA256 (TE.encodeUtf8 value) :: Digest SHA256)
shareArticle sid key = do
    let digest = keyHash key
    rows <- sqlQueryTyped [typedSql| SELECT article_id::integer AS value FROM shares WHERE id::text = ${sid} AND key_hash = ${digest} |]
    pure (listToMaybe rows)
sharedJson aid = do
    rows <- sqlQueryTyped [typedSql| SELECT shared_article_json(${aid}::integer) |]
    pure (fromMaybe J.Null (join (listToMaybe rows)))
send connection value = WS.sendTextData connection (J.encode value)
announce sid value = withMVar rooms $ \allRooms -> mapM_ (`send` value) (Map.elems (Map.findWithDefault Map.empty sid allRooms))
presence sid count = announce sid (J.object ["type" J..= ("presence" :: T.Text), "count" J..= count])

instance WSApp LiveSocket where
    initialState = LiveSocket ""
    run = do
        LiveSocket sid <- readIORef ?state
        first <- timeout 5000000 (WS.receiveData ?connection :: IO LBS.ByteString)
        let subscription = first >>= J.decode
            key = case subscription of
                Just (J.Object obj) | KM.lookup "type" obj == Just (J.String "subscribe") ->
                    case KM.lookup "key" obj of Just (J.String value) -> Just value; _ -> Nothing
                _ -> Nothing
        case key of
            Nothing -> send ?connection (J.object ["type" J..= ("invalid_link" :: T.Text)])
            Just value -> do
                access <- shareArticle sid value
                case access of
                    Nothing -> send ?connection (J.object ["type" J..= ("invalid_link" :: T.Text)])
                    Just aid -> do
                        ident <- atomicModifyIORef' sequenceId (\n -> let next = n + 1 in (next, next))
                        admitted <- modifyMVar rooms $ \allRooms -> do
                            stillValid <- shareArticle sid value
                            let room = Map.findWithDefault Map.empty sid allRooms
                            if stillValid /= Just aid then do
                                send ?connection (J.object ["type" J..= ("invalid_link" :: T.Text)])
                                pure (allRooms, False)
                            else if Map.size room >= 100 then do
                                send ?connection (J.object ["type" J..= ("room_full" :: T.Text), "limit" J..= (100 :: Int)])
                                pure (allRooms, False)
                            else do
                                article <- sharedJson (coerce aid :: Int)
                                let count = Map.size room + 1
                                send ?connection (J.object ["type" J..= ("ready" :: T.Text), "article" J..= article, "presence" J..= count])
                                mapM_ (\connection -> send connection (J.object ["type" J..= ("presence" :: T.Text), "count" J..= count])) (Map.elems room)
                                pure (Map.insert sid (Map.insert ident ?connection room) allRooms, True)
                        when admitted $ let waitLoop = WS.receiveDataMessage ?connection >> waitLoop
                            in waitLoop `finally` leave sid ident
        WS.sendClose ?connection ("closed" :: T.Text)

leave sid ident = modifyMVar_ rooms $ \allRooms -> do
    let room = Map.findWithDefault Map.empty sid allRooms
        remaining = Map.delete ident room
    when (Map.member ident room) $ do
        let count = Map.size remaining
        mapM_ (\connection -> send connection (J.object ["type" J..= ("presence" :: T.Text), "count" J..= count])) (Map.elems remaining)
    pure (if Map.null remaining then Map.delete sid allRooms else Map.insert sid remaining allRooms)

broadcastUpdate aid article = do
    ids <- sqlQueryTyped [typedSql| SELECT id FROM shares WHERE article_id = ${aid} |]
    mapM_ (\sid -> announce (coerce sid) (J.object ["type" J..= ("updated" :: T.Text), "article" J..= article])) ids

revoke sid = modifyMVar_ rooms $ \allRooms -> do
    let room = Map.findWithDefault Map.empty sid allRooms
    mapM_ (\connection -> do
        send connection (J.object ["type" J..= ("revoked" :: T.Text)])
        WS.sendClose connection ("revoked" :: T.Text)) (Map.elems room)
    pure (Map.delete sid allRooms)
