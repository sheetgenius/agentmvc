module Exports (createExport, getExport, worker) where

import Auth (requireUser)
import Control.Concurrent (threadDelay)
import Control.Monad (forever)
import Control.Monad.IO.Class (liftIO)
import Data.Aeson (Value (..), object, (.=))
import Data.Text (Text)
import Db (Db, runSql)
import Domain (failure, intField, wrap)
import Servant (Handler)

createExport :: Db -> Text -> Maybe Text -> Handler Value
createExport db secret auth = do
    user <- requireUser db secret auth
    value <- liftIO $ runSql db "WITH e AS (INSERT INTO exports(user_id) VALUES (($1->>'uid')::bigint) RETURNING *) SELECT jsonb_build_object('id',e.id,'status',e.status,'createdAt',e.created_at,'completedAt',e.completed_at,'articles',e.articles) FROM e" (object ["uid" .= intField "id" user])
    pure (wrap "export" value)

getExport :: Db -> Text -> Maybe Text -> Text -> Handler Value
getExport db secret auth ident = do
    user <- requireUser db secret auth
    value <- liftIO $ runSql db "SELECT COALESCE((SELECT jsonb_build_object('id',e.id,'status',e.status,'createdAt',e.created_at,'completedAt',e.completed_at,'articles',e.articles) FROM exports e WHERE e.id::text=$1->>'id' AND e.user_id=($1->>'uid')::bigint),'null'::jsonb)" (object ["id" .= ident, "uid" .= intField "id" user])
    if value == Null then failure 404 "export" "not found" else pure (wrap "export" value)

worker :: Db -> IO ()
worker db = forever $ do
    _ <- runSql db "WITH next AS (SELECT id,user_id FROM exports WHERE status='pending' ORDER BY id LIMIT 1 FOR UPDATE SKIP LOCKED), snapshot AS (SELECT n.id, COALESCE((SELECT jsonb_agg(jsonb_build_object('slug',a.slug,'title',a.title,'description',a.description,'body',a.body,'tagList',COALESCE((SELECT jsonb_agg(t.tag ORDER BY t.tag) FROM article_tags t WHERE t.article_id=a.id),'[]'::jsonb),'status',a.status,'commentsCount',(SELECT count(*) FROM comments c WHERE c.article_id=a.id)) ORDER BY a.id) FROM articles a WHERE a.author_id=n.user_id),'[]'::jsonb) AS articles FROM next n), done AS (UPDATE exports e SET status='done',completed_at=now(),articles=s.articles FROM snapshot s WHERE e.id=s.id RETURNING e.id) SELECT to_jsonb(count(*)) FROM done" Null
    threadDelay 200000
