module Auth (signToken, userFromHeader, requireUser, userResponse, hashPassword, verifyPassword) where

import Control.Lens ((.~), (^.))
import Control.Monad.IO.Class (liftIO)
import Crypto.JOSE.Compact (decodeCompact, encodeCompact)
import Crypto.JOSE.Error (runJOSE)
import Crypto.JOSE.Header (RequiredProtection (RequiredProtection))
import Crypto.JOSE.JWA.JWS (Alg (HS256))
import Crypto.JOSE.JWK (JWK, fromOctets)
import Crypto.JOSE.JWS (newJWSHeader)
import Crypto.JWT (SignedJWT, defaultJWTValidationSettings, emptyClaimsSet, signClaims, unregisteredClaims, verifyClaims)
import Crypto.JWT qualified as JWT
import Data.Aeson (Value (..), object, (.=))
import Data.Aeson qualified as Aeson
import Data.ByteString.Lazy qualified as BL
import Data.Map.Strict qualified as Map
import Data.Maybe (fromMaybe, isNothing)
import Data.Password.Bcrypt (Bcrypt, checkPassword, hashPasswordWithParams)
import Data.Password.Types (PasswordHash (..), mkPassword)
import Data.Scientific qualified as Scientific
import Data.Text (Text)
import Data.Text qualified as T
import Data.Text.Encoding qualified as TE
import Db (Db, runSql)
import Domain (failure, intField, textField)
import Domain qualified
import Servant (Handler)

key :: Text -> JWK
key = fromOctets . TE.encodeUtf8

signToken :: Text -> Int -> IO Text
signToken secret uid = do
    let claims = (unregisteredClaims .~ Map.singleton "uid" (Aeson.toJSON uid)) emptyClaimsSet
    signed <- runJOSE (signClaims (key secret) (newJWSHeader (RequiredProtection, HS256)) claims) :: IO (Either JWT.JWTError SignedJWT)
    case signed of
        Left err -> fail (show err)
        Right jwt -> pure (TE.decodeUtf8 (BL.toStrict (encodeCompact jwt)))

verifyToken :: Text -> Text -> IO (Maybe Int)
verifyToken secret token = case (decodeCompact (BL.fromStrict (TE.encodeUtf8 token)) :: Either JWT.JWTError SignedJWT) of
    Left _ -> pure Nothing
    Right jwt -> do
        result <- runJOSE (verifyClaims (defaultJWTValidationSettings (const True)) (key secret) jwt) :: IO (Either JWT.JWTError JWT.ClaimsSet)
        pure $ case result of
            Left _ -> Nothing
            Right claims -> case Map.lookup "uid" (claims ^. unregisteredClaims) of
                Just (Number n) -> Scientific.toBoundedInteger n
                _ -> Nothing

userFromHeader :: Db -> Text -> Maybe Text -> IO (Maybe Value)
userFromHeader db secret header = case header >>= T.stripPrefix "Token " of
    Nothing -> pure Nothing
    Just token -> do
        uid <- verifyToken secret token
        case uid of
            Nothing -> pure Nothing
            Just ident -> do
                row <- runSql db "SELECT COALESCE((SELECT to_jsonb(u) FROM users u WHERE u.id=($1->>'id')::bigint),'null'::jsonb)" (object ["id" .= ident])
                pure $ if row == Null then Nothing else Just row

requireUser :: Db -> Text -> Maybe Text -> Handler Value
requireUser db secret header = do
    user <- liftIO (userFromHeader db secret header)
    maybe (failure 401 "token" (if isNothing header then "is missing" else "is invalid")) pure user

userResponse :: Text -> Value -> IO Value
userResponse secret user = do
    token <- signToken secret (fromMaybe 0 (intField "id" user))
    pure
        ( object
            [ "user"
                .= object
                    [ "email" .= textField "email" user
                    , "username" .= textField "username" user
                    , "bio" .= Domain.objectField "bio" user
                    , "image" .= Domain.objectField "image" user
                    , "token" .= token
                    ]
            ]
        )

hashPassword :: Text -> IO Text
hashPassword password = unPasswordHash <$> hashPasswordWithParams 10 (mkPassword password)

verifyPassword :: Text -> Text -> Bool
verifyPassword password stored = show (checkPassword (mkPassword password) (PasswordHash stored :: PasswordHash Bcrypt)) == "PasswordCheckSuccess"
