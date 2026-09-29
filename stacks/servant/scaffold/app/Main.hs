module Main (main) where

import Data.Aeson (Value, object, (.=))
import Network.Wai.Handler.Warp (run)
import Servant (Get, JSON, Proxy (Proxy), serve, type (:>))
import System.Environment (lookupEnv)
import Text.Read (readMaybe)

type HealthApi = "health" :> Get '[JSON] Value

main :: IO ()
main = do
  port <- maybe 4105 id . (>>= readMaybe) <$> lookupEnv "PORT"
  run port (serve (Proxy @HealthApi) (pure (object ["status" .= ("ok" :: String)])))
