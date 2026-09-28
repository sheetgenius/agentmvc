{-# LANGUAGE TypeApplications #-}
module WorkerMain () where

import Application.Job.Export ()
import Generated.ActualTypes.ExportJob (ExportJob, ExportJob' (..))
import Generated.ExportJob ()
import IHP.FrameworkConfig (RootApplication (..))
import IHP.Job.Runner (worker)
import IHP.Job.Types (Worker (..))
import IHP.Prelude

instance Worker RootApplication where
    workers _ =
        [worker @ExportJob]
        -- Generator Marker
