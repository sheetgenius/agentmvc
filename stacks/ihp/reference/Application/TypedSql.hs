{-# LANGUAGE ImplicitParams      #-}
{-# LANGUAGE NoImplicitPrelude   #-}
{-# LANGUAGE OverloadedRecordDot #-}
{-# LANGUAGE RecordWildCards     #-}
module Application.TypedSql (typedSql, sqlQueryTyped, sqlExecTyped) where

import qualified Hasql.Decoders as Decoders
import qualified Hasql.DynamicStatements.Snippet as Snippet
import IHP.ModelSupport (sqlStatementHasql)
import IHP.Prelude
import IHP.TypedSql (TypedQuery (..), typedSql)

-- IHP's pool can retain a client prepared-statement cache after PostgreSQL
-- drops the server statement (SQLSTATE 26000). Hasql's unprepared statement
-- path keeps the quasiquoter's inferred types and avoids that cache.
sqlQueryTyped :: (?modelContext :: ModelContext) => TypedQuery result -> IO [result]
sqlQueryTyped TypedQuery {..} =
    sqlStatementHasql ?modelContext.hasqlPool () (Snippet.toStatement tqSnippet (Decoders.rowList tqResultDecoder))

sqlExecTyped :: (?modelContext :: ModelContext) => TypedQuery result -> IO Int64
sqlExecTyped TypedQuery {..} =
    sqlStatementHasql ?modelContext.hasqlPool () (Snippet.toStatement tqSnippet Decoders.rowsAffected)
