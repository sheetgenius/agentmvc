(ns conduit.db
  (:require [next.jdbc :as jdbc]
            [next.jdbc.result-set :as rs]))

(def options {:builder-fn rs/as-unqualified-lower-maps})
(defn one [db sql & params]
  (jdbc/execute-one! db (into [sql] params) options))
(defn all [db sql & params]
  (jdbc/execute! db (into [sql] params) options))
(defn run [db sql & params]
  (jdbc/execute-one! db (into [sql] params) options))
