{-# OPTIONS_GHC -fplugin=LiquidHaskell #-}
module Proof.Invariant where

import Prelude

{-@ nonNegative :: Int -> {v:Int | v >= 0} @-}
nonNegative :: Int -> Int
nonNegative x | x < 0 = 0
              | otherwise = x
