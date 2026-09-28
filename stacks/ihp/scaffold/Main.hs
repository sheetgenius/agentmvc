module Main where
import Proof.Invariant ()
import IHP.Prelude

import Config
import qualified IHP.Server
import IHP.RouterSupport
import IHP.FrameworkConfig

instance FrontController RootApplication where
    controllers = []

main :: IO ()
main = IHP.Server.run config
