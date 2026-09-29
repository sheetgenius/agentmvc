-- This file is auto generated and will be overriden regulary. Please edit `Application/Schema.sql` to change the Types\n"
module Generated.Enums where
import CorePrelude
import IHP.ModelSupport
import Database.PostgreSQL.Simple
import Database.PostgreSQL.Simple.FromField hiding (Field, name)
import Database.PostgreSQL.Simple.ToField hiding (Field)
import qualified IHP.Controller.Param
import Data.Default
import qualified IHP.QueryBuilder as QueryBuilder
import qualified Data.String.Conversions
import qualified Data.Text.Encoding
import qualified Control.DeepSeq as DeepSeq
import qualified Hasql.Encoders
import qualified Hasql.Decoders
import qualified Hasql.Implicits.Encoders
import qualified Hasql.Mapping.IsScalar as Mapping
import qualified Data.HashMap.Strict as HashMap
data ArticleStatus = Draft | Published deriving (Eq, Show, Read, Enum, Bounded, Ord)
instance FromField ArticleStatus where
    fromField field (Just value) | value == (Data.Text.Encoding.encodeUtf8 "draft") = pure Draft
    fromField field (Just value) | value == (Data.Text.Encoding.encodeUtf8 "published") = pure Published
    fromField field (Just value) = returnError ConversionFailed field ("Unexpected value for enum value. Got: " <> Data.String.Conversions.cs value)
    fromField field Nothing = returnError UnexpectedNull field "Unexpected null for enum value"
instance Default ArticleStatus where def = Draft
instance ToField ArticleStatus where
    toField Draft = toField ("draft" :: Text)
    toField Published = toField ("published" :: Text)
instance InputValue ArticleStatus where
    inputValue Draft = "draft" :: Text
    inputValue Published = "published" :: Text
instance DeepSeq.NFData ArticleStatus where rnf a = seq a ()
instance IHP.Controller.Param.ParamReader ArticleStatus where readParameter = IHP.Controller.Param.enumParamReader; readParameterJSON = IHP.Controller.Param.enumParamReaderJSON
textToEnumArticleStatusMap :: HashMap.HashMap Text ArticleStatus
textToEnumArticleStatusMap = HashMap.fromList [("draft", Draft), ("published", Published)]
textToEnumArticleStatus :: Text -> Maybe ArticleStatus
textToEnumArticleStatus t = HashMap.lookup t textToEnumArticleStatusMap
instance Hasql.Implicits.Encoders.DefaultParamEncoder ArticleStatus where
    defaultParam = Hasql.Encoders.nonNullable (Hasql.Encoders.enum (Just "public") "article_status" inputValue)
instance Hasql.Implicits.Encoders.DefaultParamEncoder (Maybe ArticleStatus) where
    defaultParam = Hasql.Encoders.nullable (Hasql.Encoders.enum (Just "public") "article_status" inputValue)
instance Hasql.Implicits.Encoders.DefaultParamEncoder [ArticleStatus] where
    defaultParam = Hasql.Encoders.nonNullable $ Hasql.Encoders.foldableArray $ Hasql.Encoders.nonNullable (Hasql.Encoders.enum (Just "public") "article_status" inputValue)
instance Mapping.IsScalar ArticleStatus where
    encoder = Hasql.Encoders.enum (Just "public") "article_status" inputValue
    decoder = Hasql.Decoders.enum (Just "public") "article_status" textToEnumArticleStatus

