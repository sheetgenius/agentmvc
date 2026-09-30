(ns conduit.migrations
  (:require [migratus.core :as migratus]))

(defn migrate! [data-source]
  (migratus/migrate {:store :database
                     :migration-dir "migrations"
                     :db {:datasource data-source}}))
