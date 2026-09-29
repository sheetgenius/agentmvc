module Db (Db, openDb, runSql) where

import Control.Concurrent.MVar (MVar, newMVar, withMVar)
import Control.Monad (forM_, unless)
import Data.Aeson (Value (..), object, (.=))
import Data.ByteString (ByteString)
import Data.List (sort)
import Data.Text (pack)
import Data.Text qualified as Text
import Data.Text.Encoding qualified as TE
import Data.Text.IO qualified as T
import Hasql.Connection qualified as C
import Hasql.Connection.Settings qualified as Settings
import Hasql.Decoders qualified as D
import Hasql.Encoders qualified as E
import Hasql.Session qualified as S
import Hasql.Statement qualified as Statement
import System.Directory (listDirectory)
import System.FilePath (takeExtension, (</>))

newtype Db = Db (MVar C.Connection)

openDb :: String -> IO Db
openDb url = do
    result <- C.acquire (Settings.connectionString (pack url))
    connection <- either (fail . show) pure result
    setup <- C.use connection (S.script "CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY, applied_at timestamptz NOT NULL DEFAULT now())")
    either (fail . show) pure setup
    db <- Db <$> newMVar connection
    files <- sort . filter ((== ".sql") . takeExtension) <$> listDirectory "migrations"
    forM_ files $ \name -> do
        applied <- runSql db "SELECT to_jsonb(EXISTS(SELECT 1 FROM schema_migrations WHERE name=$1->>'name'))" (object ["name" .= name])
        unless (applied == Bool True) $ do
            schema <- T.readFile ("migrations" </> name)
            let quoted = Text.replace "'" "''" (pack name)
            migration <- C.use connection (S.script ("BEGIN;\n" <> schema <> "\nINSERT INTO schema_migrations(name) VALUES ('" <> quoted <> "');\nCOMMIT;"))
            either (fail . show) pure migration
    pure db

runSql :: Db -> ByteString -> Value -> IO Value
runSql (Db lock) sql input = withMVar lock $ \connection -> do
    result <- C.use connection (S.statement input statement)
    either (fail . show) pure result
  where
    statement = Statement.preparable (TE.decodeUtf8 sql) (E.param (E.nonNullable E.jsonb)) (D.singleRow (D.column (D.nonNullable D.jsonb)))
