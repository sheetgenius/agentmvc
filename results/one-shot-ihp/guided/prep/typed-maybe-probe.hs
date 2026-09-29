{-# LANGUAGE ImplicitParams #-}
{-# LANGUAGE QuasiQuotes #-}
{-# LANGUAGE OverloadedStrings #-}
module Application.TypedMaybeProbe where
import IHP.ControllerPrelude
import IHP.TypedSql
import qualified Data.Text as Text
probe :: (?modelContext :: ModelContext) => Maybe Text.Text -> IO ()
probe title = do
  _ <- sqlQueryTyped [typedSql| SELECT COALESCE(${title}, 'fallback'::text) AS title |]
  pure ()
