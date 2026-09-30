(ns conduit.rules
  (:require [clojure.string :as str]))

(defn fail
  ([status field message] (fail status field message nil))
  ([status field message extra]
   (throw (ex-info message (merge {:status status :errors {(name field) [message]}} extra)))))

(defn nonblank! [field value]
  (when-not (and (string? value) (not (str/blank? value)))
    (fail 422 field (if (= value "") "can't be blank" "can't be empty")))
  value)

(defn revision! [given current article]
  (when (some? given)
    (when-not (integer? given) (fail 422 :revision "is invalid"))
    (when (not= given current) (fail 409 :revision "is stale" {:article article}))))

(defn visible-article! [article viewer-id]
  (when (or (nil? article)
            (and (= "draft" (:status article)) (not= viewer-id (:author_id article))))
    (fail 404 :article "not found"))
  article)

(defn author! [article viewer-id]
  (when (not= viewer-id (:author_id article)) (fail 403 :article "forbidden"))
  article)

(defn published! [article]
  (when (= "draft" (:status article)) (fail 422 :article "is a draft"))
  article)

(defn slug-base [title]
  (let [base (-> title str/lower-case (str/replace #"[^a-z0-9]+" "-") (str/replace #"(^-|-$)" ""))]
    (if (str/blank? base) "article" base)))
