{-# LANGUAGE DataKinds                 #-}
{-# LANGUAGE ImplicitParams            #-}
{-# LANGUAGE NoImplicitPrelude         #-}
{-# LANGUAGE NoMonomorphismRestriction #-}
{-# LANGUAGE OverloadedRecordDot       #-}
{-# LANGUAGE OverloadedStrings         #-}
{-# LANGUAGE QuasiQuotes               #-}
{-# LANGUAGE TypeApplications          #-}
module Application.Job.Export where

import Application.TypedSql
import qualified Data.Aeson as J
import Data.Coerce (coerce)
import Data.Int (Int)
import Data.Maybe (fromMaybe, listToMaybe)
import Generated.ActualTypes.ExportJob (ExportJob, ExportJob' (..))
import IHP.Job.Types (Job (..))
import IHP.ModelSupport.Types (Id' (..))
import IHP.Prelude

-- IHP's PostgreSQL job runner locks and retries this durable queue row.
instance Job ExportJob where
    perform job = do
        let eid = job.exportId :: Int
        owners <- sqlQueryTyped [typedSql| SELECT user_id FROM exports WHERE id = ${eid} |]
        case listToMaybe owners of
            Nothing -> pure ()
            Just uid -> do
                snapshots <- sqlQueryTyped [typedSql|
                    SELECT COALESCE(jsonb_agg(jsonb_build_object(
                        'slug', a.slug, 'title', a.title, 'description', a.description, 'body', a.body,
                        'tagList', a.tags, 'status', a.status,
                        'commentsCount', (SELECT count(*) FROM comments c WHERE c.article_id = a.id))
                        ORDER BY a.created_at ASC, a.id ASC), '[]'::jsonb)
                    FROM articles a WHERE a.author_id = ${uid} |]
                let snapshot = fromMaybe (J.Array mempty) (listToMaybe snapshots)
                _ <- sqlExecTyped [typedSql| UPDATE exports SET status = 'done', completed_at = now(), articles = ${snapshot} WHERE id = ${eid} |]
                pure ()
