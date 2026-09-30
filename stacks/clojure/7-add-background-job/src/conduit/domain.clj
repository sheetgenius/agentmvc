(ns conduit.domain
  (:require [clojure.string :as str]))

(defn fail [status field message]
  (throw (ex-info message {:status status :errors {(keyword field) [message]}})))

(defn required [values fields]
  (doseq [field fields]
    (when (or (not (string? (get values field)))
              (str/blank? (get values field)))
      (fail 422 field "can't be blank")))
  values)

(defn found [value field]
  (or value (fail 404 field "not found")))

(defn owned [owner-id user-id field]
  (when (not= owner-id user-id)
    (fail 403 field "forbidden")))
