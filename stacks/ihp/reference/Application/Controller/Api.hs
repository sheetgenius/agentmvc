{-# LANGUAGE DataKinds                 #-}
{-# LANGUAGE ImplicitParams            #-}
{-# LANGUAGE LambdaCase                #-}
{-# LANGUAGE NoImplicitPrelude         #-}
{-# LANGUAGE NoMonomorphismRestriction #-}
{-# LANGUAGE OverloadedRecordDot       #-}
{-# LANGUAGE OverloadedStrings         #-}
{-# LANGUAGE PackageImports            #-}
{-# LANGUAGE QuasiQuotes               #-}
{-# LANGUAGE ScopedTypeVariables       #-}
{-# LANGUAGE TypeApplications          #-}
module Application.Controller.Api where

import qualified Application.Live as Live
import Application.TypedSql
import Control.Monad (join, (>=>))
import "cryptonite" Crypto.Hash (Digest, SHA256 (..), hashWith)
import "cryptonite" Crypto.KDF.PBKDF2 (Parameters (..), fastPBKDF2_SHA256)
import "cryptonite" Crypto.MAC.HMAC (HMAC, hmac)
import qualified Data.Aeson as J
import qualified Data.Aeson.Key as K
import qualified Data.Aeson.KeyMap as KM
import qualified Data.ByteArray as BA
import qualified Data.ByteString as B
import qualified Data.ByteString.Base64.URL as B64
import qualified Data.ByteString.Lazy as LBS
import Data.Char (isAlphaNum)
import Data.Coerce (coerce)
import Data.Foldable (toList)
import Data.Int (Int)
import Data.Maybe (fromMaybe, isJust, isNothing, listToMaybe)
import qualified Data.Text as T
import qualified Data.Text.Encoding as TE
import Data.Traversable (traverse)
import qualified Data.UUID as UUID
import qualified Data.UUID.V4 as UUID
import Generated.ActualTypes.PrimaryKeys ()
import IHP.ControllerPrelude
import IHP.ModelSupport.Types (Id' (..))
import qualified Network.HTTP.Types.Status as H
import Network.Wai (pathInfo, queryString, requestHeaders, requestMethod,
                    responseLBS)
import System.Environment (lookupEnv)
import Text.Read (readMaybe)

withCreated ids action' = case listToMaybe ids of
    Just value -> action' (coerce value :: Int)
    Nothing    -> failure H.status500 "database" "write failed"

-- IHP owns routing and requests; typed SQL owns persistence.
data ApiAction = ApiAction deriving (Eq, Show)
instance Controller ApiAction where
    action _ = do
        viewer <- viewerId
        let path = drop 1 (pathInfo ?request)
            method = requestMethod ?request
        case (method, path) of
            ("POST", ["users"]) -> register
            ("POST", ["users", "login"]) -> loginUser
            ("GET", ["user"]) -> withUser viewer getUser
            ("PUT", ["user"]) -> withUser viewer updateUser
            ("GET", ["user", "drafts"]) -> withUser viewer (\uid -> listArticles uid True False)
            ("POST", ["user", "exports"]) -> withUser viewer startExport
            ("GET", ["user", "exports", eid]) -> withUser viewer (`getExport` eid)
            ("GET", ["profiles", name]) -> profile viewer name
            ("POST", ["profiles", name, "follow"]) -> withUser viewer (\uid -> follow uid name True)
            ("DELETE", ["profiles", name, "follow"]) -> withUser viewer (\uid -> follow uid name False)
            ("GET", ["articles"]) -> listArticles viewer False False
            ("GET", ["articles", "feed"]) -> withUser viewer (\uid -> listArticles uid False True)
            ("POST", ["articles"]) -> withUser viewer createArticle
            ("GET", ["articles", slug]) -> articleEndpoint viewer slug "read"
            ("PUT", ["articles", slug]) -> withUser viewer (\uid -> articleEndpoint uid slug "update")
            ("DELETE", ["articles", slug]) -> withUser viewer (\uid -> articleEndpoint uid slug "delete")
            ("POST", ["articles", slug, "publish"]) -> withUser viewer (\uid -> articleEndpoint uid slug "publish")
            ("POST", ["articles", slug, "share"]) -> withUser viewer (\uid -> articleEndpoint uid slug "share")
            ("DELETE", ["articles", slug, "share"]) -> withUser viewer (\uid -> articleEndpoint uid slug "unshare")
            ("GET", ["articles", slug, "comments"]) -> articleEndpoint viewer slug "comments"
            ("POST", ["articles", slug, "comments"]) -> withUser viewer (\uid -> articleEndpoint uid slug "comment")
            ("DELETE", ["articles", slug, "comments", cid]) -> withUser viewer (\uid -> articleEndpoint uid slug ("delete-comment:" <> cid))
            ("POST", ["articles", slug, "favorite"]) -> withUser viewer (\uid -> articleEndpoint uid slug "favorite")
            ("DELETE", ["articles", slug, "favorite"]) -> withUser viewer (\uid -> articleEndpoint uid slug "unfavorite")
            ("GET", ["tags"]) -> tags
            ("GET", ["shares", sid, "article"]) -> sharedEndpoint sid False
            ("PUT", ["shares", sid, "article"]) -> sharedEndpoint sid True
            _ -> failure H.status404 "route" "not found"
reply status value = respondWith (responseLBS status [("Content-Type", "application/json"), ("X-Content-Type-Options", "nosniff")] (J.encode value))
failure status name message = reply status (J.object ["errors" J..= J.object [K.fromText name J..= [message :: T.Text]]])
conflict article = reply H.status409 (J.object ["errors" J..= J.object ["revision" J..= ["is stale" :: T.Text]], "article" J..= article])
noContent = respondWith (responseLBS H.status204 [("X-Content-Type-Options", "nosniff")] "")
wrap name value = J.object [K.fromText name J..= value]
field name (J.Object obj) = KM.lookup (K.fromText name) obj
field _ _                 = Nothing
objectField name value = fromMaybe J.Null (field name value)
textField name value = case field name value of Just (J.String t) -> Just t; _ -> Nothing
blank name value = case field name value of
    Nothing                                -> Just "can't be blank"
    Just (J.String t) | T.null (T.strip t) -> Just "can't be blank"
    Just (J.String _)                      -> Nothing
    _                                      -> Just "is invalid"
validRequired names value = listToMaybe [(name, message) | name <- names, Just message <- [blank name value]]
invalid (name, message) = failure H.status422 name message
payload name = objectField name <$> requestBodyJSON
withUser uid action' = if uid == 0 then failure H.status401 "token" "is missing" else action' uid
viewerId = do
    let token = case lookup "Authorization" (requestHeaders ?request) of
            Just header -> TE.decodeUtf8 <$> B.stripPrefix "Token " header
            Nothing     -> Nothing
    case token of
        Nothing -> pure 0
        Just value -> do
            valid <- validToken value
            if not valid then pure 0 else do
                rows <- sqlQueryTyped [typedSql| SELECT id FROM users WHERE token = ${value} |]
                pure (maybe 0 (\userId -> coerce userId :: Int) (listToMaybe rows))
newKey = do
    a <- UUID.nextRandom
    b <- UUID.nextRandom
    pure (UUID.toText a <> UUID.toText b)
jwtHeader = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" :: T.Text
signingKey = do
    production <- lookupEnv "SECRET_KEY_BASE"
    development <- lookupEnv "IHP_SESSION_SECRET"
    pure (TE.encodeUtf8 (T.pack (fromMaybe "ihp-local-development-secret" (production <|> development))))
signature key signing = B64.encodeUnpadded (BA.convert (hmac key (TE.encodeUtf8 signing) :: HMAC SHA256) :: B.ByteString)
newToken = do
    key <- signingKey
    nonce <- newKey
    let claims = B64.encodeUnpadded (LBS.toStrict (J.encode (J.object ["jti" J..= nonce])))
        signing = jwtHeader <> "." <> TE.decodeUtf8 claims
    pure (signing <> "." <> TE.decodeUtf8 (signature key signing))
validToken token = case T.splitOn "." token of
    [header, claims, supplied] | header == jwtHeader && not (T.null claims) && not (T.null supplied) -> do
        key <- signingKey
        pure (BA.constEq (TE.encodeUtf8 supplied) (signature key (header <> "." <> claims)))
    _ -> pure False
sha value = show (hashWith SHA256 (TE.encodeUtf8 value) :: Digest SHA256)
passwordHash password = do
    salt <- newKey
    pure (salt <> ":" <> TE.decodeUtf8 (passwordDigest salt password))
passwordDigest salt password = B64.encodeUnpadded (fastPBKDF2_SHA256 (Parameters 120000 32) (TE.encodeUtf8 password) (TE.encodeUtf8 salt) :: B.ByteString)
passwordMatches password stored = case T.splitOn ":" stored of
    [salt, digest] -> BA.constEq (TE.encodeUtf8 digest) (passwordDigest salt password)
    _ -> False

userJson uid = do
    values <- sqlQueryTyped [typedSql| SELECT user_json(${uid}::integer) |]
    pure (fromMaybe J.Null (join (listToMaybe values)))
profileJson uid viewer = do
    values <- sqlQueryTyped [typedSql| SELECT profile_json(${uid}::integer, ${viewer}::integer) |]
    pure (fromMaybe J.Null (join (listToMaybe values)))
articleJson aid viewer body = do
    values <- sqlQueryTyped [typedSql| SELECT article_json(${aid}::integer, ${viewer}::integer, ${body}) |]
    pure (fromMaybe J.Null (join (listToMaybe values)))
sharedJson aid = do
    values <- sqlQueryTyped [typedSql| SELECT shared_article_json(${aid}::integer) |]
    pure (fromMaybe J.Null (join (listToMaybe values)))
commentJson cid viewer = do
    values <- sqlQueryTyped [typedSql| SELECT comment_json(${cid}::integer, ${viewer}::integer) |]
    pure (fromMaybe J.Null (join (listToMaybe values)))

register = do
    body <- payload "user"
    case validRequired ["username", "email", "password"] body of
        Just problem -> invalid problem
        Nothing -> do
            let username = fromMaybe "" (textField "username" body)
                email = fromMaybe "" (textField "email" body)
                password = fromMaybe "" (textField "password" body)
            names <- sqlQueryTyped [typedSql| SELECT id FROM users WHERE username = ${username} |]
            emails <- sqlQueryTyped [typedSql| SELECT id FROM users WHERE email = ${email} |]
            if not (null names) then failure H.status409 "username" "has already been taken"
            else if not (null emails) then failure H.status409 "email" "has already been taken"
            else do
                hashed <- passwordHash password
                token <- newToken
                ids <- sqlQueryTyped [typedSql| INSERT INTO users (username, email, password_hash, token) VALUES (${username}, ${email}, ${hashed}, ${token}) RETURNING id |]
                withCreated ids (userJson >=> reply H.status201 . wrap "user")

loginUser = do
    body <- payload "user"
    case validRequired ["email", "password"] body of
        Just problem -> invalid problem
        Nothing -> do
            let email = fromMaybe "" (textField "email" body)
                password = fromMaybe "" (textField "password" body)
            rows <- sqlQueryTyped [typedSql| SELECT id, password_hash, failed_logins FROM users WHERE email = ${email} |]
            case listToMaybe rows of
                Just row | row.failed_logins >= 20 -> failure H.status429 "credentials" "rate limited"
                Just row | passwordMatches password row.password_hash -> do
                    let uid = row.id
                    _ <- sqlExecTyped [typedSql| UPDATE users SET failed_logins = 0 WHERE id = ${uid} |]
                    userJson uid >>= reply H.status200 . wrap "user"
                Just row -> do
                    let uid = row.id
                    _ <- sqlExecTyped [typedSql| UPDATE users SET failed_logins = failed_logins + 1 WHERE id = ${uid} |]
                    failure H.status401 "credentials" "invalid"
                Nothing -> failure H.status401 "credentials" "invalid"

getUser uid = userJson uid >>= reply H.status200 . wrap "user"
updateUser (uid :: Int) = do
    body <- payload "user"
    let required = [name | name <- ["username", "email", "password"], isJust (field name body)]
    case validRequired required body of
        Just problem -> invalid problem
        Nothing | Just password <- textField "password" body, T.length password < 8 -> failure H.status422 "password" "is too short"
        Nothing -> do
            let username = textField "username" body
                email = textField "email" body
                bio = fmap (\t -> if T.null t then Nothing else Just t) (textField "bio" body)
                image = fmap (\t -> if T.null t then Nothing else Just t) (textField "image" body)
            pw <- case textField "password" body of Nothing -> pure Nothing; Just value -> Just <$> passwordHash value
            let usernameValue = fromMaybe "" username
                emailValue = fromMaybe "" email
                bioValue = fromMaybe "" (join bio)
                imageValue = fromMaybe "" (join image)
                passwordValue = fromMaybe "" pw
            _ <- sqlExecTyped [typedSql| UPDATE users SET
                username = CASE WHEN ${isJust username} THEN ${usernameValue} ELSE username END,
                email = CASE WHEN ${isJust email} THEN ${emailValue} ELSE email END,
                bio = CASE WHEN ${isJust (field "bio" body)} THEN NULLIF(${bioValue}, '') ELSE bio END,
                image = CASE WHEN ${isJust (field "image" body)} THEN NULLIF(${imageValue}, '') ELSE image END,
                password_hash = CASE WHEN ${isJust pw} THEN ${passwordValue} ELSE password_hash END
                WHERE id = ${uid} |]
            getUser uid

profile (viewer :: Int) (username :: T.Text) = do
    users <- sqlQueryTyped [typedSql| SELECT id FROM users WHERE username = ${username} |]
    case listToMaybe users of
        Nothing -> failure H.status404 "profile" "not found"
        Just uid -> profileJson (coerce uid :: Int) viewer >>= reply H.status200 . wrap "profile"
follow (uid :: Int) (username :: T.Text) adding = do
    users <- sqlQueryTyped [typedSql| SELECT id FROM users WHERE username = ${username} |]
    case listToMaybe users of
        Nothing -> failure H.status404 "profile" "not found"
        Just target -> do
            if adding then do
                _ <- sqlExecTyped [typedSql| INSERT INTO follows (follower_id, followed_id) VALUES (${uid}, ${target}) ON CONFLICT DO NOTHING |]
                pure ()
            else do
                _ <- sqlExecTyped [typedSql| DELETE FROM follows WHERE follower_id = ${uid} AND followed_id = ${target} |]
                pure ()
            profileJson (coerce target :: Int) uid >>= reply H.status200 . wrap "profile"

slugFor title = do
    suffix <- T.take 8 <$> newKey
    let stem = T.intercalate "-" (filter (not . T.null) (T.split (== '-') (T.map (\c -> if isAlphaNum c then c else '-') (T.toLower title))))
    pure (stem <> "-" <> suffix)
articleVisible viewer slug = do
    rows <- sqlQueryTyped [typedSql| SELECT id, author_id, status, revision FROM articles WHERE slug = ${slug} AND (status = 'published' OR author_id = ${viewer}) |]
    pure (listToMaybe rows)

queryArg name = maybe "" (TE.decodeUtf8 . fromMaybe "") (lookup name (queryString ?request))
page name defaultValue = case readMaybe (T.unpack (queryArg name)) of
    Just n | n >= 0 -> min 1000 n
    _               -> defaultValue
listArticles viewer drafts feed = do
    let tag = queryArg "tag"
        author = queryArg "author"
        favorited = queryArg "favorited"
        limit = page "limit" 20
        offset = page "offset" 0
    ids <- sqlQueryTyped [typedSql|
        SELECT a.id FROM articles a WHERE
            ((${drafts} AND a.status = 'draft' AND a.author_id = ${viewer}) OR
             (NOT ${drafts} AND a.status = 'published'))
            AND (NOT ${feed} OR EXISTS (SELECT 1 FROM follows f WHERE f.follower_id = ${viewer} AND f.followed_id = a.author_id))
            AND (${tag} = '' OR ${tag} = ANY(a.tags))
            AND (${author} = '' OR EXISTS (SELECT 1 FROM users u WHERE u.id = a.author_id AND u.username = ${author}))
            AND (${favorited} = '' OR EXISTS (SELECT 1 FROM favorites f JOIN users u ON u.id = f.user_id WHERE f.article_id = a.id AND u.username = ${favorited}))
        ORDER BY a.created_at DESC, a.id DESC |]
    articles <- mapM (\aid -> articleJson (coerce aid :: Int) viewer False) (take limit (drop offset ids))
    reply H.status200 (J.object ["articles" J..= articles, "articlesCount" J..= length ids])

tags = do
    names <- sqlQueryTyped [typedSql| SELECT DISTINCT tag FROM articles a CROSS JOIN LATERAL unnest(a.tags) tag WHERE a.status = 'published' ORDER BY tag |]
    reply H.status200 (wrap "tags" names)

tagsInput body = case field "tagList" body of
    Nothing -> Right Nothing
    Just (J.Array xs) -> case traverse (\case J.String value -> Just value; _ -> Nothing) (toList xs) of
        Just values -> Right (Just values)
        Nothing     -> Left ("tagList", "is invalid")
    _ -> Left ("tagList", "is invalid")
revisionInput body = case field "revision" body of
    Nothing -> Right Nothing
    Just value -> case J.fromJSON value of
        J.Success revision -> Right (Just (revision :: Int))
        J.Error _          -> Left ("revision", "is invalid")

createArticle (uid :: Int) = do
    body <- payload "article"
    let status = fromMaybe "published" (textField "status" body)
    case validRequired ["title", "description", "body"] body of
        Just problem -> invalid problem
        Nothing | status /= "published" && status /= "draft" -> failure H.status422 "status" "is invalid"
        Nothing -> case tagsInput body of
            Left problem -> invalid problem
            Right tagsValue -> do
                let title = fromMaybe "" (textField "title" body)
                    description = fromMaybe "" (textField "description" body)
                    articleBody = fromMaybe "" (textField "body" body)
                    tagList = fromMaybe [] tagsValue
                slug <- slugFor title
                ids <- sqlQueryTyped [typedSql| INSERT INTO articles (author_id, slug, title, description, body, tags, status, published_at)
                    VALUES (${uid}, ${slug}, ${title}, ${description}, ${articleBody}, ${tagList}, ${status},
                      CASE WHEN ${status} = 'published' THEN now() ELSE NULL END) RETURNING id |]
                withCreated ids (\aid -> articleJson aid uid True >>= reply H.status201 . wrap "article")

articleEndpoint (viewer :: Int) (slug :: T.Text) operation = do
    found <- articleVisible viewer slug
    case found of
        Nothing -> failure H.status404 "article" "not found"
        Just article -> do
            let aid = coerce article.id :: Int
                owned = (coerce article.author_id :: Int) == viewer
                draft = article.status == "draft"
            if operation `elem` ["update", "delete", "publish", "share", "unshare"] && not owned
                then failure H.status403 "article" "forbidden"
            else case operation of
                "read" -> articleJson aid viewer True >>= reply H.status200 . wrap "article"
                "update" -> updateArticle aid viewer (Just article.revision) False
                "delete" -> do
                    _ <- sqlExecTyped [typedSql| DELETE FROM articles WHERE id = ${aid} |]
                    noContent
                "publish" -> do
                    when draft $ do
                        _ <- sqlExecTyped [typedSql| UPDATE articles SET status = 'published', published_at = now(), updated_at = now(), revision = revision + 1 WHERE id = ${aid} |]
                        pure ()
                    articleJson aid viewer True >>= reply H.status200 . wrap "article"
                "comments" -> do
                    ids <- sqlQueryTyped [typedSql| SELECT id FROM comments WHERE article_id = ${aid} ORDER BY created_at ASC, id ASC |]
                    values <- mapM (\cid -> commentJson (coerce cid :: Int) viewer) ids
                    reply H.status200 (wrap "comments" values)
                "comment" | draft -> failure H.status422 "article" "is a draft"
                "comment" -> do
                    body <- payload "comment"
                    case validRequired ["body"] body of
                        Just problem -> invalid problem
                        Nothing -> do
                            let content = fromMaybe "" (textField "body" body)
                            ids <- sqlQueryTyped [typedSql| INSERT INTO comments (article_id, author_id, body) VALUES (${aid}, ${viewer}, ${content}) RETURNING id |]
                            withCreated ids (\cid -> commentJson cid viewer >>= reply H.status201 . wrap "comment")
                "favorite" | draft -> failure H.status422 "article" "is a draft"
                "favorite" -> do
                    _ <- sqlExecTyped [typedSql| INSERT INTO favorites (user_id, article_id) VALUES (${viewer}, ${aid}) ON CONFLICT DO NOTHING |]
                    articleJson aid viewer True >>= reply H.status200 . wrap "article"
                "unfavorite" | draft -> failure H.status422 "article" "is a draft"
                "unfavorite" -> do
                    _ <- sqlExecTyped [typedSql| DELETE FROM favorites WHERE user_id = ${viewer} AND article_id = ${aid} |]
                    articleJson aid viewer True >>= reply H.status200 . wrap "article"
                "share" -> createShare aid
                "unshare" -> revokeShare aid
                _ | Just rawId <- T.stripPrefix "delete-comment:" operation ->
                    case readMaybe (T.unpack rawId) of
                        Nothing -> failure H.status404 "comment" "not found"
                        Just (cid :: Int) -> deleteComment aid viewer cid
                _ -> failure H.status404 "route" "not found"

deleteComment aid (viewer :: Int) (cid :: Int) = do
    rows <- sqlQueryTyped [typedSql| SELECT author_id FROM comments WHERE id = ${cid} AND article_id = ${aid} |]
    case listToMaybe rows of
        Nothing -> failure H.status404 "comment" "not found"
        Just owner | (coerce owner :: Int) /= viewer -> failure H.status403 "comment" "forbidden"
        Just _ -> do
            _ <- sqlExecTyped [typedSql| DELETE FROM comments WHERE id = ${cid} |]
            noContent

-- One revision check and mutation rule serves normal updates and capability edits.
updateArticle aid (viewer :: Int) current shared = do
    body <- payload "article"
    case revisionInput body of
        Left problem -> invalid problem
        Right expected | Just old <- expected, Just now <- current, old /= now -> do
            present <- if shared then sharedJson aid else articleJson aid viewer True
            conflict present
        Right expected -> do
            let required = if shared then ["title", "body"] else [name | name <- ["title", "description", "body"], isJust (field name body)]
                extras = case body of J.Object obj -> filter (`notElem` map K.fromText ["title", "body", "revision"]) (KM.keys obj); _ -> []
            case validRequired required body of
                Just problem -> invalid problem
                Nothing | shared && (not (null extras) || isNothing expected) -> failure H.status422 "article" "is invalid"
                Nothing -> case tagsInput body of
                    Left problem -> invalid problem
                    Right tagList -> do
                        let title = textField "title" body
                            description = textField "description" body
                            articleBody = textField "body" body
                        slug <- traverse slugFor title
                        let titleValue = fromMaybe "" title
                            descriptionValue = fromMaybe "" description
                            bodyValue = fromMaybe "" articleBody
                            slugValue = fromMaybe "" slug
                            tagsValue = fromMaybe [] tagList
                            hasRevision = isJust expected
                            expectedValue = fromMaybe 0 expected
                        changed <- sqlQueryTyped [typedSql| UPDATE articles SET
                            title = CASE WHEN ${isJust title} THEN ${titleValue} ELSE title END,
                            description = CASE WHEN ${isJust description} THEN ${descriptionValue} ELSE description END,
                            body = CASE WHEN ${isJust articleBody} THEN ${bodyValue} ELSE body END,
                            slug = CASE WHEN ${isJust slug} THEN ${slugValue} ELSE slug END,
                            tags = CASE WHEN ${isJust tagList} THEN ${tagsValue} ELSE tags END,
                            revision = revision + 1, updated_at = now()
                            WHERE id = ${aid} AND (NOT ${hasRevision} OR revision = ${expectedValue}) RETURNING id |]
                        if null changed then do
                            present <- if shared then sharedJson aid else articleJson aid viewer True
                            conflict present
                        else do
                            present <- if shared then sharedJson aid else articleJson aid viewer True
                            Live.broadcastUpdate (Id aid :: Id' "articles") present
                            reply H.status200 (wrap "article" present)

createShare aid = do
    sid <- newKey
    key <- newKey
    let digest = sha key
    old <- sqlQueryTyped [typedSql| DELETE FROM shares WHERE article_id = ${aid} RETURNING id |]
    mapM_ (Live.revoke . (coerce :: Id' "shares" -> T.Text)) old
    _ <- sqlExecTyped [typedSql| INSERT INTO shares (id, article_id, key_hash) VALUES (${sid}, ${aid}, ${digest}) |]
    reply H.status201 (wrap "share" (J.object ["id" J..= sid, "key" J..= key]))

revokeShare aid = do
    old <- sqlQueryTyped [typedSql| DELETE FROM shares WHERE article_id = ${aid} RETURNING id |]
    mapM_ (Live.revoke . (coerce :: Id' "shares" -> T.Text)) old
    noContent

sharedAccess sid key = do
    let digest = sha key
    rows <- sqlQueryTyped [typedSql| SELECT article_id FROM shares WHERE id = ${sid} AND key_hash = ${digest} |]
    pure (fmap (\value -> coerce value :: Int) (listToMaybe rows))
sharedEndpoint (sid :: T.Text) editing = do
    let key = maybe "" TE.decodeUtf8 (lookup "X-Share-Key" (requestHeaders ?request))
    access <- sharedAccess sid key
    case access of
        Nothing -> failure H.status404 "share" "not found"
        Just aid -> if editing then do
            rows <- sqlQueryTyped [typedSql| SELECT revision FROM articles WHERE id = ${aid} |]
            updateArticle aid 0 (listToMaybe rows) True
        else sharedJson aid >>= reply H.status200 . wrap "article"

exportJson eid = do
    rows <- sqlQueryTyped [typedSql| SELECT export_json(${eid}::integer) |]
    pure (fromMaybe J.Null (join (listToMaybe rows)))
startExport (uid :: Int) = do
    ids <- sqlQueryTyped [typedSql| INSERT INTO exports (user_id) VALUES (${uid}) RETURNING id |]
    withCreated ids $ \eid -> do
        _ <- sqlExecTyped [typedSql| INSERT INTO export_jobs (export_id) VALUES (${eid}) |]
        exportJson eid >>= reply H.status202 . wrap "export"
getExport (uid :: Int) (raw :: T.Text) = case readMaybe (T.unpack raw) of
    Nothing -> failure H.status404 "export" "not found"
    Just (eid :: Int) -> do
        rows <- sqlQueryTyped [typedSql| SELECT id FROM exports WHERE id = ${eid} AND user_id = ${uid} |]
        case listToMaybe rows of
            Nothing -> failure H.status404 "export" "not found"
            Just _  -> exportJson eid >>= reply H.status200 . wrap "export"
