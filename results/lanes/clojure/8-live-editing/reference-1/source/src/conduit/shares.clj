(ns conduit.shares
  (:require [conduit.articles :as articles]
            [conduit.domain :as domain]
            [conduit.store :as store]
            [next.jdbc :as jdbc])
  (:import [java.nio.charset StandardCharsets]
           [java.security MessageDigest SecureRandom]
           [java.util Base64 HexFormat UUID]))

(def ^:private random (SecureRandom.))

(defn- secret []
  (let [bytes (byte-array 32)]
    (.nextBytes random bytes)
    (.encodeToString (.withoutPadding (Base64/getUrlEncoder)) bytes)))

(defn- key-hash [key]
  (.formatHex (HexFormat/of)
              (.digest (MessageDigest/getInstance "SHA-256")
                       (.getBytes ^String key StandardCharsets/UTF_8))))

(defn- valid-key? [stored candidate]
  (and (string? candidate)
       (MessageDigest/isEqual (.getBytes ^String stored StandardCharsets/UTF_8)
                              (.getBytes ^String (key-hash candidate) StandardCharsets/UTF_8))))

(defn- owned-article [db viewer slug]
  (let [article (articles/find-article db viewer slug)]
    (domain/owned (:author_id article) (:id viewer) :article)
    article))

(defn create! [db viewer slug]
  (jdbc/with-transaction [tx db]
    (let [article (owned-article tx viewer slug)
          _ (store/one tx "SELECT id FROM articles WHERE id = ? FOR UPDATE" (:id article))
          old (store/one tx "DELETE FROM article_shares WHERE article_id = ? RETURNING id" (:id article))
          id (str (UUID/randomUUID))
          key (secret)]
      (store/execute! tx "INSERT INTO article_shares (id, article_id, key_hash) VALUES (?, ?, ?)"
                      id (:id article) (key-hash key))
      {:share {:id id :key key} :revoked-id (:id old)})))

(defn revoke! [db viewer slug]
  (jdbc/with-transaction [tx db]
    (let [article (owned-article tx viewer slug)
          _ (store/one tx "SELECT id FROM articles WHERE id = ? FOR UPDATE" (:id article))]
      (:id (store/one tx "DELETE FROM article_shares WHERE article_id = ? RETURNING id" (:id article))))))

(defn- lookup [db id key]
  (let [row (store/one db (str "SELECT a.*, s.key_hash FROM article_shares s "
                               "JOIN articles a ON a.id = s.article_id WHERE s.id = ?") id)]
    (when-not (and row (valid-key? (:key_hash row) key))
      (domain/fail 404 :share "not found"))
    row))

(defn shared-article [article]
  (select-keys article [:slug :title :body :revision]))

(defn read-article [db id key]
  (shared-article (lookup db id key)))

(defn- stale! [article]
  (throw (ex-info "is stale" {:status 409 :errors {:revision ["is stale"]}
                              :article (shared-article article)})))

(defn save! [db id key payload]
  (jdbc/with-transaction [tx db]
    (let [candidate (lookup tx id key)
          _ (store/one tx "SELECT id FROM articles WHERE id = ? FOR UPDATE" (:id candidate))
          article (lookup tx id key)
          input (:article payload)]
      (when-not (and (map? payload) (= #{:article} (set (keys payload)))
                     (map? input)
                     (= #{:title :body :revision} (set (keys input))))
        (domain/fail 422 :article "is invalid"))
      (domain/required input [:title :body])
      (when-not (integer? (:revision input))
        (domain/fail 422 :revision "is invalid"))
      (when-not (= (:revision input) (:revision article))
        (stale! article))
      (if-let [updated (articles/update-row! tx article input)]
        (shared-article updated)
        (stale! (store/one tx "SELECT * FROM articles WHERE id = ?" (:id article)))))))

(defn active-id [db slug]
  (:id (store/one db "SELECT s.id FROM article_shares s JOIN articles a ON a.id = s.article_id WHERE a.slug = ?" slug)))
