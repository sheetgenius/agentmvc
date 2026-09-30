(ns conduit.store
  (:require [next.jdbc :as jdbc]
            [next.jdbc.result-set :as rs]))

(defn one [db sql & args]
  (jdbc/execute-one! db (into [sql] args) {:builder-fn rs/as-unqualified-lower-maps}))

(defn all [db sql & args]
  (jdbc/execute! db (into [sql] args) {:builder-fn rs/as-unqualified-lower-maps}))

(defn execute! [db sql & args]
  (jdbc/execute-one! db (into [sql] args)))

(defn statement-one [db statement]
  (jdbc/execute-one! db statement {:builder-fn rs/as-unqualified-lower-maps}))
