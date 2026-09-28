{-# LANGUAGE TypeApplications #-}
module Main where
import IHP.Prelude
import Proof.Invariant ()

import Application.Controller.Api
import Application.Live (LiveSocket (..))
import Config
import Data.Attoparsec.ByteString.Char8 (endOfInput, string, takeByteString,
                                         takeTill)
import Data.Functor (($>))
import qualified Data.Text.Encoding as Text
import IHP.ControllerSupport (InitControllerContext,
                              startWebSocketAppAndFailOnHTTP)
import IHP.FrameworkConfig
import IHP.Router.Types (ControllerRoute (..))
import IHP.RouterSupport
import qualified IHP.Server

instance InitControllerContext RootApplication

instance FrontController RootApplication where
    controllers =
        [ ControllerRouteParser $ do
            string "/api/shares/"
            sid <- takeTill (== '/')
            string "/live"
            endOfInput
            pure (withImplicits (startWebSocketAppAndFailOnHTTP @LiveSocket @RootApplication (LiveSocket (Text.decodeUtf8 sid))))
        , ControllerRouteParser ((string "/api/" *> takeByteString) $> runAction' @RootApplication ApiAction)
        ]

main :: IO ()
main = IHP.Server.run config
