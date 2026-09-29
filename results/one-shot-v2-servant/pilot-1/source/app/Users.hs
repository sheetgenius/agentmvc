module Users (register, login, current, updateUser, profile, follow) where

import Auth (hashPassword, requireUser, userFromHeader, userResponse, verifyPassword)
import Control.Monad (when)
import Control.Monad.IO.Class (liftIO)
import Data.Aeson (Value (..), object, (.=))
import Data.Maybe (isJust)
import Data.Text (Text)
import Data.Text qualified as T
import Db (Db, runSql)
import Domain (failure, field, intField, objectField, requiredText, textField, wrap)
import Servant (Handler)

register :: Db -> Text -> Value -> Handler Value
register db secret input = do
    let body = objectField "user" input
    username <- requiredText "username" body
    email <- requiredText "email" body
    password <- requiredText "password" body
    whenInvalidEmail email
    duplicate <- liftIO $ runSql db "SELECT jsonb_build_object('username', EXISTS(SELECT 1 FROM users WHERE username=$1->>'username'), 'email', EXISTS(SELECT 1 FROM users WHERE email=$1->>'email'))" (object ["username" .= username, "email" .= email])
    when (field "username" duplicate == Just (Bool True)) $ failure 409 "username" "has already been taken"
    when (field "email" duplicate == Just (Bool True)) $ failure 409 "email" "has already been taken"
    hashed <- liftIO (hashPassword password)
    user <- liftIO $ runSql db "WITH u AS (INSERT INTO users(username,email,password_hash) VALUES ($1->>'username',$1->>'email',$1->>'hash') RETURNING *) SELECT to_jsonb(u) FROM u" (object ["username" .= username, "email" .= email, "hash" .= hashed])
    liftIO (userResponse secret user)

whenInvalidEmail :: Text -> Handler ()
whenInvalidEmail email = if T.any (== '@') email then pure () else failure 422 "email" "is invalid"

login :: Db -> Text -> Value -> Handler Value
login db secret input = do
    let body = objectField "user" input
    email <- requiredText "email" body
    password <- requiredText "password" body
    attempts <- liftIO $ runSql db "SELECT to_jsonb(COALESCE((SELECT failures FROM login_failures WHERE email=$1->>'email' AND updated_at > now()-interval '15 minutes'),0))" (object ["email" .= email])
    case attempts of Number n | n >= 20 -> failure 429 "credentials" "rate limited"; _ -> pure ()
    user <- liftIO $ runSql db "SELECT COALESCE((SELECT to_jsonb(u) FROM users u WHERE email=$1->>'email'),'null'::jsonb)" (object ["email" .= email])
    if user /= Null && maybe False (verifyPassword password) (textField "password_hash" user)
        then do
            _ <- liftIO $ runSql db "WITH d AS (DELETE FROM login_failures WHERE email=$1->>'email' RETURNING email) SELECT 'null'::jsonb" (object ["email" .= email])
            liftIO (userResponse secret user)
        else do
            _ <- liftIO $ runSql db "WITH f AS (INSERT INTO login_failures(email,failures) VALUES ($1->>'email',1) ON CONFLICT(email) DO UPDATE SET failures=login_failures.failures+1,updated_at=now() RETURNING failures) SELECT to_jsonb(failures) FROM f" (object ["email" .= email])
            failure 401 "credentials" "invalid"

current :: Db -> Text -> Maybe Text -> Handler Value
current db secret auth = do
    user <- requireUser db secret auth
    liftIO (userResponse secret user)

updateUser :: Db -> Text -> Maybe Text -> Value -> Handler Value
updateUser db secret auth input = do
    user <- requireUser db secret auth
    let body = objectField "user" input
    username <- optionalRequired "username" body
    email <- optionalRequired "email" body
    password <- optionalRequired "password" body
    case password of Just p | T.length p < 8 -> failure 422 "password" "is too short"; _ -> pure ()
    maybe (pure ()) whenInvalidEmail email
    hashed <- liftIO (traverse hashPassword password)
    let uid = intField "id" user
    duplicate <- liftIO $ runSql db "SELECT jsonb_build_object('username', EXISTS(SELECT 1 FROM users WHERE username=$1->>'username' AND id<>($1->>'id')::bigint), 'email', EXISTS(SELECT 1 FROM users WHERE email=$1->>'email' AND id<>($1->>'id')::bigint))" (object ["username" .= username, "email" .= email, "id" .= uid])
    when (isJust username && field "username" duplicate == Just (Bool True)) $ failure 409 "username" "has already been taken"
    when (isJust email && field "email" duplicate == Just (Bool True)) $ failure 409 "email" "has already been taken"
    updated <- liftIO $ runSql db "WITH u AS (UPDATE users SET username=COALESCE($1->>'username',username), email=COALESCE($1->>'email',email), password_hash=COALESCE($1->>'hash',password_hash), bio=CASE WHEN ($1->>'hasBio')::boolean THEN NULLIF($1->>'bio','') ELSE bio END, image=CASE WHEN ($1->>'hasImage')::boolean THEN NULLIF($1->>'image','') ELSE image END WHERE id=($1->>'id')::bigint RETURNING *) SELECT to_jsonb(u) FROM u" (object ["id" .= uid, "username" .= username, "email" .= email, "hash" .= hashed, "bio" .= field "bio" body, "image" .= field "image" body, "hasBio" .= isJust (field "bio" body), "hasImage" .= isJust (field "image" body)])
    liftIO (userResponse secret updated)
  where
    optionalRequired key body = case field key body of Nothing -> pure Nothing; _ -> Just <$> requiredText key body

profile :: Db -> Text -> Maybe Text -> Text -> Handler Value
profile db secret auth username = do
    viewer <- liftIO (userFromHeader db secret auth)
    value <- liftIO $ runSql db "SELECT COALESCE((SELECT profile_payload(u,($1->>'viewer')::bigint) FROM users u WHERE u.username=$1->>'username'),'null'::jsonb)" (object ["username" .= username, "viewer" .= (viewer >>= intField "id")])
    if value == Null then failure 404 "profile" "not found" else pure (wrap "profile" value)

follow :: Db -> Text -> Maybe Text -> Text -> Bool -> Handler Value
follow db secret auth username adding = do
    caller <- requireUser db secret auth
    target <- liftIO $ runSql db "SELECT COALESCE((SELECT to_jsonb(u) FROM users u WHERE u.username=$1->>'username'),'null'::jsonb)" (object ["username" .= username])
    when (target == Null) $ failure 404 "profile" "not found"
    let uid = intField "id" caller; tid = intField "id" target
    when (uid == tid && adding) $ failure 422 "profile" "cannot follow yourself"
    _ <- liftIO $ runSql db (if adding then "WITH f AS (INSERT INTO follows(follower_id,followed_id) VALUES (($1->>'uid')::bigint,($1->>'tid')::bigint) ON CONFLICT DO NOTHING RETURNING 1) SELECT 'null'::jsonb" else "WITH f AS (DELETE FROM follows WHERE follower_id=($1->>'uid')::bigint AND followed_id=($1->>'tid')::bigint RETURNING 1) SELECT 'null'::jsonb") (object ["uid" .= uid, "tid" .= tid])
    profile db secret auth username
