module Articles (
    listArticles,
    tags,
    createArticle,
    getArticle,
    updateArticle,
    deleteArticle,
    publishArticle,
    comments,
    addComment,
    deleteComment,
    favorite,
    visibleArticle,
    ownedArticle,
    updateChecked,
    pageParams,
) where

import Auth (requireUser, userFromHeader)
import Control.Monad (when)
import Control.Monad.IO.Class (liftIO)
import Data.Aeson (Value (..), object, (.=))
import Data.Aeson qualified as Aeson
import Data.Maybe (fromMaybe, isJust, isNothing)
import Data.Text (Text)
import Data.Text qualified as T
import Data.UUID qualified as UUID
import Data.UUID.V4 qualified as UUID
import Db (Db, runSql)
import Domain (articleVisibility, failure, field, intField, objectField, optionalInt, optionalTags, optionalText, requiredText, slugBase, statusField, textField, validateArticle, wrap)
import Servant (Handler)
import Servant qualified
import Text.Read (readMaybe)

type Notify = Value -> IO ()

pageParams :: Maybe Text -> Maybe Text -> Handler (Int, Int)
pageParams rawLimit rawOffset = do
    limit <- parse 20 rawLimit
    offset <- parse 0 rawOffset
    pure (min 100 (max 0 limit), max 0 offset)
  where
    parse fallback = maybe (pure fallback) (maybe (failure 422 "pagination" "is invalid") pure . readMaybe . T.unpack)

visibleArticle :: Db -> Maybe Int -> Text -> Handler Value
visibleArticle db viewer slug = do
    item <- liftIO $ runSql db "SELECT COALESCE((SELECT jsonb_build_object('id',a.id,'authorId',a.author_id,'status',a.status,'article',article_payload(a,($1->>'viewer')::bigint,true)) FROM articles a WHERE a.slug=$1->>'slug'),'null'::jsonb)" (object ["slug" .= slug, "viewer" .= viewer])
    if item == Null then failure 404 "article" "not found" else articleVisibility viewer item
    pure item

ownedArticle :: Db -> Int -> Text -> Handler Value
ownedArticle db uid slug = do
    item <- visibleArticle db (Just uid) slug
    if intField "authorId" item /= Just uid then failure 403 "article" "forbidden" else pure item

listArticles :: Db -> Text -> Maybe Text -> Text -> Maybe Text -> Maybe Text -> Maybe Text -> Maybe Text -> Maybe Text -> Maybe Text -> Handler Value
listArticles db secret auth mode tag author favorited rawLimit rawOffset _unused = do
    viewer <- liftIO (userFromHeader db secret auth)
    uid <- if mode == "feed" || mode == "drafts" then Just . fromMaybe 0 . intField "id" <$> requireUser db secret auth else pure (viewer >>= intField "id")
    (limit, offset) <- pageParams rawLimit rawOffset
    liftIO $ runSql db "WITH filtered AS (SELECT a.* FROM articles a WHERE ((($1->>'mode')='drafts' AND a.status='draft' AND a.author_id=($1->>'viewer')::bigint) OR (($1->>'mode')<>'drafts' AND a.status='published' AND (($1->>'mode')<>'feed' OR EXISTS (SELECT 1 FROM follows f WHERE f.follower_id=($1->>'viewer')::bigint AND f.followed_id=a.author_id)))) AND (($1->>'tag') IS NULL OR EXISTS (SELECT 1 FROM article_tags t WHERE t.article_id=a.id AND t.tag=$1->>'tag')) AND (($1->>'author') IS NULL OR EXISTS (SELECT 1 FROM users u WHERE u.id=a.author_id AND u.username=$1->>'author')) AND (($1->>'favorited') IS NULL OR EXISTS (SELECT 1 FROM favorites f JOIN users u ON u.id=f.user_id WHERE f.article_id=a.id AND u.username=$1->>'favorited'))), page AS (SELECT * FROM filtered ORDER BY id DESC LIMIT ($1->>'limit')::int OFFSET ($1->>'offset')::int) SELECT jsonb_build_object('articles',COALESCE((SELECT jsonb_agg(article_payload(p,($1->>'viewer')::bigint,false) ORDER BY p.id DESC) FROM page p),'[]'::jsonb),'articlesCount',(SELECT count(*) FROM filtered))" (object ["mode" .= mode, "viewer" .= uid, "tag" .= tag, "author" .= author, "favorited" .= favorited, "limit" .= limit, "offset" .= offset])

tags :: Db -> Handler Value
tags db = liftIO $ runSql db "SELECT jsonb_build_object('tags',COALESCE((SELECT jsonb_agg(tag ORDER BY tag) FROM (SELECT DISTINCT t.tag FROM article_tags t JOIN articles a ON a.id=t.article_id WHERE a.status='published') x),'[]'::jsonb))" Null

createArticle :: Db -> Text -> Maybe Text -> Value -> Handler Value
createArticle db secret auth input = do
    user <- requireUser db secret auth
    let body = objectField "article" input
    (title, description, content, tagList, status) <- validateArticle body
    nonce <- liftIO UUID.nextRandom
    let slug = slugBase title <> "-" <> T.take 8 (UUID.toText nonce)
        uid = intField "id" user
    article <- liftIO $ runSql db "WITH a AS (INSERT INTO articles(slug,title,description,body,author_id,status,published_at) VALUES ($1->>'slug',$1->>'title',$1->>'description',$1->>'body',($1->>'uid')::bigint,$1->>'status',CASE WHEN $1->>'status'='published' THEN now() ELSE NULL END) RETURNING *) SELECT jsonb_set(article_payload(a,($1->>'uid')::bigint,true),'{tagList}',$1->'tags') FROM a, LATERAL replace_article_tags(a.id,$1->'tags')" (object ["slug" .= slug, "title" .= title, "description" .= description, "body" .= content, "uid" .= uid, "status" .= status, "tags" .= tagList])
    pure (wrap "article" article)

getArticle :: Db -> Text -> Maybe Text -> Text -> Handler Value
getArticle db secret auth slug = do
    viewer <- liftIO (userFromHeader db secret auth)
    item <- visibleArticle db (viewer >>= intField "id") slug
    pure (wrap "article" (objectField "article" item))

updateChecked :: Db -> Int -> Value -> Maybe Int -> Maybe Text -> Maybe Text -> Maybe Text -> Maybe [Text] -> Notify -> Bool -> Handler Value
updateChecked db uid item expected title description body tags notify shared = do
    let current = objectField "article" item
        revision = intField "revision" current
    case expected of Just n | Just n /= revision -> stale current; _ -> pure ()
    nonce <- liftIO UUID.nextRandom
    let slug = fmap (\t -> slugBase t <> "-" <> T.take 8 (UUID.toText nonce)) title
        ident = intField "id" item
    result <- liftIO $ runSql db "WITH a AS (UPDATE articles SET title=COALESCE($1->>'title',title),description=COALESCE($1->>'description',description),body=COALESCE($1->>'body',body),slug=COALESCE($1->>'slug',slug),revision=revision+1,updated_at=now() WHERE id=($1->>'id')::bigint AND revision=($1->>'revision')::int RETURNING *) SELECT COALESCE((SELECT CASE WHEN ($1->>'replaceTags')::boolean THEN jsonb_set(article_payload(a,($1->>'uid')::bigint,true),'{tagList}',$1->'tags') ELSE article_payload(a,($1->>'uid')::bigint,true) END FROM a, LATERAL (SELECT CASE WHEN ($1->>'replaceTags')::boolean THEN replace_article_tags(a.id,$1->'tags') ELSE true END) x),'null'::jsonb)" (object ["id" .= ident, "uid" .= uid, "revision" .= revision, "title" .= title, "description" .= description, "body" .= body, "slug" .= slug, "replaceTags" .= isJust tags, "tags" .= fromMaybe [] tags])
    if result == Null
        then do
            latest <- liftIO $ runSql db "SELECT article_payload(a,($1->>'uid')::bigint,true) FROM articles a WHERE a.id=($1->>'id')::bigint" (object ["id" .= ident, "uid" .= uid])
            stale latest
        else do
            liftIO (notify (object ["articleId" .= ident, "article" .= result]))
            pure (if shared then sharedView result else wrap "article" result)
  where
    stale current = failureWithArticle (if shared then sharedViewValue current else current)

failureWithArticle :: Value -> Handler a
failureWithArticle current = Servant.throwError (Servant.ServerError 409 "conflict" (Aeson.encode (object ["errors" .= object ["revision" .= ["is stale" :: Text]], "article" .= current])) [("Content-Type", "application/json")])

sharedViewValue :: Value -> Value
sharedViewValue value = object ["slug" .= textField "slug" value, "title" .= textField "title" value, "body" .= textField "body" value, "revision" .= intField "revision" value]

sharedView :: Value -> Value
sharedView = wrap "article" . sharedViewValue

updateArticle :: Db -> Text -> Notify -> Maybe Text -> Text -> Value -> Handler Value
updateArticle db secret notify auth slug input = do
    user <- requireUser db secret auth
    let uid = fromMaybe 0 (intField "id" user)
    item <- ownedArticle db uid slug
    let body = objectField "article" input
    expected <- optionalInt "revision" body
    case expected of Just n | Just n /= intField "revision" (objectField "article" item) -> failureWithArticle (objectField "article" item); _ -> pure ()
    title <- optionalText "title" body
    description <- optionalText "description" body
    content <- optionalText "body" body
    tagList <- if isNothing (field "tagList" body) then pure Nothing else Just <$> optionalTags body
    updateChecked db uid item expected title description content tagList notify False

deleteArticle :: Db -> Text -> Maybe Text -> Text -> Handler ()
deleteArticle db secret auth slug = do
    user <- requireUser db secret auth
    item <- ownedArticle db (fromMaybe 0 (intField "id" user)) slug
    _ <- liftIO $ runSql db "WITH d AS (DELETE FROM articles WHERE id=($1->>'id')::bigint RETURNING id) SELECT 'null'::jsonb" (object ["id" .= intField "id" item])
    pure ()

publishArticle :: Db -> Text -> Maybe Text -> Text -> Handler Value
publishArticle db secret auth slug = do
    user <- requireUser db secret auth
    let uid = fromMaybe 0 (intField "id" user)
    item <- ownedArticle db uid slug
    if textField "status" item == Just "published"
        then pure (wrap "article" (objectField "article" item))
        else do
            article <- liftIO $ runSql db "WITH a AS (UPDATE articles SET status='published',published_at=now(),revision=revision+1,updated_at=now() WHERE id=($1->>'id')::bigint RETURNING *) SELECT article_payload(a,($1->>'uid')::bigint,true) FROM a" (object ["id" .= intField "id" item, "uid" .= uid])
            pure (wrap "article" article)

publicAction :: Db -> Maybe Int -> Text -> Handler Value
publicAction db viewer slug = do
    item <- visibleArticle db viewer slug
    if textField "status" item == Just "draft" then failure 422 "article" "is a draft" else pure item

comments :: Db -> Text -> Maybe Text -> Text -> Handler Value
comments db secret auth slug = do
    viewer <- liftIO (userFromHeader db secret auth)
    item <- visibleArticle db (viewer >>= intField "id") slug
    liftIO $ runSql db "SELECT jsonb_build_object('comments',COALESCE((SELECT jsonb_agg(jsonb_build_object('id',c.id,'body',c.body,'createdAt',c.created_at,'updatedAt',c.updated_at,'author',profile_payload(u,($1->>'viewer')::bigint)) ORDER BY c.id) FROM comments c JOIN users u ON u.id=c.author_id WHERE c.article_id=($1->>'id')::bigint),'[]'::jsonb))" (object ["id" .= intField "id" item, "viewer" .= (viewer >>= intField "id")])

addComment :: Db -> Text -> Maybe Text -> Text -> Value -> Handler Value
addComment db secret auth slug input = do
    user <- requireUser db secret auth
    let uid = fromMaybe 0 (intField "id" user)
    item <- publicAction db (Just uid) slug
    body <- requiredText "body" (objectField "comment" input)
    comment <- liftIO $ runSql db "WITH c AS (INSERT INTO comments(article_id,author_id,body) VALUES (($1->>'id')::bigint,($1->>'uid')::bigint,$1->>'body') RETURNING *) SELECT jsonb_build_object('id',c.id,'body',c.body,'createdAt',c.created_at,'updatedAt',c.updated_at,'author',profile_payload(u,($1->>'uid')::bigint)) FROM c JOIN users u ON u.id=c.author_id" (object ["id" .= intField "id" item, "uid" .= uid, "body" .= body])
    pure (wrap "comment" comment)

deleteComment :: Db -> Text -> Maybe Text -> Text -> Int -> Handler ()
deleteComment db secret auth slug cid = do
    user <- requireUser db secret auth
    let uid = fromMaybe 0 (intField "id" user)
    item <- visibleArticle db (Just uid) slug
    comment <- liftIO $ runSql db "SELECT COALESCE((SELECT to_jsonb(c) FROM comments c WHERE c.id=($1->>'cid')::bigint AND c.article_id=($1->>'id')::bigint),'null'::jsonb)" (object ["cid" .= cid, "id" .= intField "id" item])
    when (comment == Null) $ failure 404 "comment" "not found"
    when (intField "author_id" comment /= Just uid) $ failure 403 "comment" "forbidden"
    _ <- liftIO $ runSql db "WITH d AS (DELETE FROM comments WHERE id=($1->>'cid')::bigint RETURNING id) SELECT 'null'::jsonb" (object ["cid" .= cid])
    pure ()

favorite :: Db -> Text -> Maybe Text -> Text -> Bool -> Handler Value
favorite db secret auth slug adding = do
    user <- requireUser db secret auth
    let uid = fromMaybe 0 (intField "id" user)
    item <- publicAction db (Just uid) slug
    let payload = object ["id" .= intField "id" item, "uid" .= uid]
    _ <- liftIO $ runSql db (if adding then "WITH f AS (INSERT INTO favorites(user_id,article_id) VALUES (($1->>'uid')::bigint,($1->>'id')::bigint) ON CONFLICT DO NOTHING RETURNING 1) SELECT 'null'::jsonb" else "WITH f AS (DELETE FROM favorites WHERE user_id=($1->>'uid')::bigint AND article_id=($1->>'id')::bigint RETURNING 1) SELECT 'null'::jsonb") payload
    article <- liftIO $ runSql db "SELECT article_payload(a,($1->>'uid')::bigint,true) FROM articles a WHERE a.id=($1->>'id')::bigint" payload
    pure (wrap "article" article)
