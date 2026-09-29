module Domain (
    field,
    optionalText,
    requiredText,
    optionalInt,
    optionalTags,
    statusField,
    validateArticle,
    validateShareEdit,
    slugBase,
    problem,
    failure,
    wrap,
    objectField,
    textField,
    intField,
    boolField,
    articleVisibility,
) where

import Control.Monad (when)
import Data.Aeson (Value (..), object, (.=))
import Data.Aeson qualified as Aeson
import Data.Aeson.Key qualified as Key
import Data.Aeson.KeyMap qualified as KM
import Data.ByteString.Lazy qualified as BL
import Data.Char (isAlphaNum, toLower)
import Data.Maybe (fromMaybe)
import Data.Scientific (toBoundedInteger)
import Data.Text (Text)
import Data.Text qualified as T
import Servant (Handler, ServerError (..), throwError)

field :: Text -> Value -> Maybe Value
field key (Object o) = KM.lookup (Key.fromText key) o
field _ _ = Nothing

objectField :: Text -> Value -> Value
objectField key value = fromMaybe Null (field key value)

textField :: Text -> Value -> Maybe Text
textField key value = case field key value of Just (String t) -> Just t; _ -> Nothing

intField :: Text -> Value -> Maybe Int
intField key value = case field key value of Just (Number n) -> toBoundedInteger n; _ -> Nothing

boolField :: Text -> Value -> Bool
boolField key value = field key value == Just (Bool True)

problem :: Text -> Text -> Value
problem key msg = object ["errors" .= object [Key.fromText key .= [msg]]]

failure :: Int -> Text -> Text -> Handler a
failure code key msg = throwError (ServerError code "error" (Aeson.encode (problem key msg)) [("Content-Type", "application/json")])

wrap :: Text -> Value -> Value
wrap key value = object [Key.fromText key .= value]

optionalText :: Text -> Value -> Handler (Maybe Text)
optionalText key value = case field key value of
    Nothing -> pure Nothing
    Just (String t)
        | not (T.null (T.strip t)) -> pure (Just t)
        | otherwise -> failure 422 key "can't be blank"
    _ -> failure 422 key "is invalid"

requiredText :: Text -> Value -> Handler Text
requiredText key value = maybe (failure 422 key "can't be blank") pure =<< optionalText key value

optionalInt :: Text -> Value -> Handler (Maybe Int)
optionalInt key value = case field key value of
    Nothing -> pure Nothing
    Just (Number n) -> maybe (failure 422 key "is invalid") (pure . Just) (toBoundedInteger n)
    _ -> failure 422 key "is invalid"

optionalTags :: Value -> Handler [Text]
optionalTags value = case field "tagList" value of
    Nothing -> pure []
    Just (Array xs) -> traverse asTag (toList xs)
    _ -> failure 422 "tagList" "is invalid"
  where
    asTag (String t) = pure t
    asTag _ = failure 422 "tagList" "is invalid"
    toList = foldr (:) []

statusField :: Value -> Handler Text
statusField value = case field "status" value of
    Nothing -> pure "published"
    Just (String "draft") -> pure "draft"
    Just (String "published") -> pure "published"
    _ -> failure 422 "status" "is invalid"

validateArticle :: Value -> Handler (Text, Text, Text, [Text], Text)
validateArticle value = do
    title <- requiredText "title" value
    description <- requiredText "description" value
    body <- requiredText "body" value
    tags <- optionalTags value
    status <- statusField value
    pure (title, description, body, tags, status)

validateShareEdit :: Value -> Handler (Text, Text, Int)
validateShareEdit value = do
    case value of
        Object o | any ((`KM.member` o) . Key.fromText) ["description", "status", "tagList", "slug", "author", "publishedAt"] -> failure 422 "article" "is invalid"
        _ -> pure ()
    title <- requiredText "title" value
    body <- requiredText "body" value
    revision <- maybe (failure 422 "revision" "is invalid") pure =<< optionalInt "revision" value
    pure (title, body, revision)

slugBase :: Text -> Text
slugBase = T.dropWhileEnd (== '-') . T.intercalate "-" . filter (not . T.null) . T.split (== '-') . T.map normalize . T.toLower
  where
    normalize c | isAlphaNum c = c | otherwise = '-'

articleVisibility :: Maybe Int -> Value -> Handler ()
articleVisibility viewer article =
    when (textField "status" article == Just "draft" && intField "authorId" article /= viewer) $
        failure 404 "article" "not found"
