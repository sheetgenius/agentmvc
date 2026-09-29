module Main (main) where

import Articles qualified
import Control.Concurrent (forkIO)
import Data.Aeson (Value, object, (.=))
import Data.Maybe (fromMaybe)
import Data.Text (Text)
import Data.Text qualified as T
import Db (Db, openDb)
import Exports qualified
import Network.HTTP.Types (status204)
import Network.Wai qualified as Wai
import Network.Wai.Handler.Warp (defaultSettings, runSettings, setHost, setPort)
import Network.Wai.Handler.WebSockets (websocketsOr)
import Network.WebSockets qualified as WS
import Servant
import Shares qualified
import System.Environment (lookupEnv)
import Text.Read (readMaybe)
import Users qualified

type AuthHeader = Header "Authorization" Text
type JsonBody = ReqBody '[JSON] Value
type JsonGet = Get '[JSON] Value
type JsonPut = Put '[JSON] Value
type JsonPost = Post '[JSON] Value
type JsonCreated = PostCreated '[JSON] Value
type JsonAccepted = PostAccepted '[JSON] Value

type UserRoutes =
    "users" :> (JsonBody :> JsonCreated :<|> "login" :> JsonBody :> JsonPost)
        :<|> "user"
            :> ( AuthHeader :> JsonGet
                    :<|> AuthHeader :> JsonBody :> JsonPut
                    :<|> "drafts" :> AuthHeader :> QueryParam "limit" Text :> QueryParam "offset" Text :> JsonGet
                    :<|> "exports" :> (AuthHeader :> JsonAccepted :<|> Capture "id" Text :> AuthHeader :> JsonGet)
               )

type ProfileRoutes =
    "profiles"
        :> Capture "username" Text
        :> (AuthHeader :> JsonGet :<|> "follow" :> (AuthHeader :> JsonPost :<|> AuthHeader :> Delete '[JSON] Value))

type ArticleRoutes =
    "articles"
        :> ( AuthHeader :> QueryParam "tag" Text :> QueryParam "author" Text :> QueryParam "favorited" Text :> QueryParam "limit" Text :> QueryParam "offset" Text :> JsonGet
                :<|> AuthHeader :> JsonBody :> JsonCreated
                :<|> "feed" :> AuthHeader :> QueryParam "limit" Text :> QueryParam "offset" Text :> JsonGet
                :<|> Capture "slug" Text
                    :> ( AuthHeader :> JsonGet
                            :<|> AuthHeader :> JsonBody :> JsonPut
                            :<|> AuthHeader :> DeleteNoContent
                            :<|> "publish" :> AuthHeader :> JsonPost
                            :<|> "share" :> (AuthHeader :> JsonCreated :<|> AuthHeader :> DeleteNoContent)
                            :<|> "favorite" :> (AuthHeader :> JsonPost :<|> AuthHeader :> Delete '[JSON] Value)
                            :<|> "comments" :> (AuthHeader :> JsonGet :<|> AuthHeader :> JsonBody :> JsonCreated :<|> Capture "id" Int :> AuthHeader :> DeleteNoContent)
                       )
           )

type ShareRoutes =
    "shares"
        :> Capture "id" Text
        :> "article"
        :> (Header "X-Share-Key" Text :> JsonGet :<|> Header "X-Share-Key" Text :> JsonBody :> JsonPut)

type Api = "health" :> JsonGet :<|> "api" :> (UserRoutes :<|> ProfileRoutes :<|> ArticleRoutes :<|> ShareRoutes :<|> "tags" :> JsonGet)

main :: IO ()
main = do
    dbUrl <- maybe (fail "DATABASE_URL is required") pure =<< lookupEnv "DATABASE_URL"
    secret <- maybe (fail "SECRET_KEY_BASE is required") (pure . T.pack) =<< lookupEnv "SECRET_KEY_BASE"
    port <- fromMaybe 4105 . (>>= readMaybe) <$> lookupEnv "PORT"
    db <- openDb dbUrl
    live <- Shares.newLive db
    _ <- forkIO (Exports.worker db)
    let handler = health :<|> (userHandlers db secret :<|> profileHandlers db secret :<|> articleHandlers db secret live :<|> shareHandlers live :<|> Articles.tags db)
        application = serve (Proxy @Api) handler
    runSettings (setHost "0.0.0.0" (setPort port defaultSettings)) (headers (websocketsOr WS.defaultConnectionOptions (Shares.socketServer live) application))
  where
    health = pure (object ["status" .= ("ok" :: Text)])

userHandlers :: Db -> Text -> Server UserRoutes
userHandlers db secret =
    (Users.register db secret :<|> Users.login db secret)
        :<|> ( Users.current db secret
                :<|> Users.updateUser db secret
                :<|> (\auth limit offset -> Articles.listArticles db secret auth "drafts" Nothing Nothing Nothing limit offset Nothing)
                :<|> (Exports.createExport db secret :<|> flip (Exports.getExport db secret))
             )

profileHandlers :: Db -> Text -> Server ProfileRoutes
profileHandlers db secret username =
    (\auth -> Users.profile db secret auth username)
        :<|> ( (\auth -> Users.follow db secret auth username True)
                :<|> (\auth -> Users.follow db secret auth username False)
             )

articleHandlers :: Db -> Text -> Shares.Live -> Server ArticleRoutes
articleHandlers db secret live =
    (\auth tag author favorited limit offset -> Articles.listArticles db secret auth "list" tag author favorited limit offset Nothing)
        :<|> Articles.createArticle db secret
        :<|> (\auth limit offset -> Articles.listArticles db secret auth "feed" Nothing Nothing Nothing limit offset Nothing)
        :<|> ( \slug ->
                (\auth -> Articles.getArticle db secret auth slug)
                    :<|> (\auth input -> Articles.updateArticle db secret (Shares.broadcastUpdate live) auth slug input)
                    :<|> (\auth -> Articles.deleteArticle db secret auth slug >> pure NoContent)
                    :<|> (\auth -> Articles.publishArticle db secret auth slug)
                    :<|> ((\auth -> Shares.createShare live secret auth slug) :<|> (\auth -> Shares.deleteShare live secret auth slug >> pure NoContent))
                    :<|> ((\auth -> Articles.favorite db secret auth slug True) :<|> (\auth -> Articles.favorite db secret auth slug False))
                    :<|> ((\auth -> Articles.comments db secret auth slug) :<|> (\auth input -> Articles.addComment db secret auth slug input) :<|> (\cid auth -> Articles.deleteComment db secret auth slug cid >> pure NoContent))
             )

shareHandlers :: Shares.Live -> Server ShareRoutes
shareHandlers live ident = Shares.readShare live ident :<|> Shares.updateShare live ident

headers :: Wai.Middleware
headers next request sendResponse =
    if Wai.requestMethod request == "OPTIONS"
        then sendResponse (Wai.responseLBS status204 cors "")
        else next request (sendResponse . Wai.mapResponseHeaders (cors ++))
  where
    cors =
        [ ("X-Content-Type-Options", "nosniff")
        , ("Access-Control-Allow-Origin", "*")
        , ("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Share-Key")
        , ("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        ]
