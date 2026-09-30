(ns conduit.users
  (:require [buddy.hashers :as hashers]
            [buddy.sign.jwt :as jwt]
            [clojure.string :as str]
            [conduit.db :as db]
            [conduit.rules :as rules])
  (:import [org.postgresql.util PSQLException]))

(defonce login-failures (atom {}))

(defn user-by-id [source id]
  (db/one source "SELECT * FROM users WHERE id=?" id))

(defn token [secret user]
  (jwt/sign {:sub (str (:id user)) :exp (+ (quot (System/currentTimeMillis) 1000) (* 60 60 24 30))} secret {:alg :hs256}))

(defn from-token [source secret credential]
  (when credential
    (try
      (let [claims (jwt/unsign credential secret {:alg :hs256})
            id (some-> (:sub claims) Long/parseLong)]
        (when (and (number? (:exp claims)) id) (user-by-id source id)))
      (catch Exception _ nil))))

(defn authenticate [source secret request]
  (when-let [header (get-in request [:headers "authorization"])]
    (if-let [[_ credential] (re-matches #"Token (.+)" header)]
      (or (from-token source secret credential) (rules/fail 401 :token "is invalid"))
      (rules/fail 401 :token "is invalid"))))

(defn required! [request]
  (or (:viewer request) (rules/fail 401 :token "is missing")))

(defn public [secret user]
  {:email (:email user) :token (token secret user) :username (:username user)
   :bio (:bio user) :image (:image user)})

(defn profile [source viewer-id user]
  {:username (:username user) :bio (:bio user) :image (:image user)
   :following (boolean (and viewer-id
                            (db/one source "SELECT 1 FROM follows WHERE follower_id=? AND followed_id=?" viewer-id (:id user))))})

(defn by-username [source username]
  (db/one source "SELECT * FROM users WHERE username=?" username))

(defn profile! [source username viewer-id]
  (let [user (by-username source username)]
    (when-not user (rules/fail 404 :profile "not found"))
    (profile source viewer-id user)))

(defn duplicate! [source fields except-id]
  (doseq [field [:username :email] :when (contains? fields field)]
    (when (db/one source (str "SELECT id FROM users WHERE " (name field) "=? AND id<>?")
                  (get fields field) (or except-id -1))
      (rules/fail 409 field "has already been taken"))))

(defn register! [source input]
  (doseq [field [:username :email :password]]
    (rules/nonblank! field (get input field)))
  (duplicate! source input nil)
  (try
    (db/one source "INSERT INTO users(username,email,password_hash) VALUES (?,?,?) RETURNING *"
            (:username input) (:email input) (hashers/derive (:password input) {:alg :argon2id}))
    (catch PSQLException e
      (if (= "23505" (.getSQLState e))
        (do (duplicate! source input nil) (rules/fail 409 :user "has already been taken"))
        (throw e)))))

(defn login! [source input]
  (doseq [field [:email :password]] (rules/nonblank! field (get input field)))
  (let [email (:email input)
        now (System/currentTimeMillis)
        {:keys [count since]} (get @login-failures email)]
    (when (and since (< (- now since) 60000) (>= count 20))
      (rules/fail 429 :credentials "rate limited"))
    (let [user (db/one source "SELECT * FROM users WHERE email=?" email)]
      (if (and user (:valid (hashers/verify (:password input) (:password_hash user))))
        (do (swap! login-failures dissoc email) user)
        (do (swap! login-failures update email
                   (fn [entry]
                     (if (and entry (< (- now (:since entry)) 60000))
                       (update entry :count inc)
                       {:since now :count 1})))
            (rules/fail 401 :credentials "invalid"))))))

(defn update! [source id input]
  (doseq [field [:username :email :password] :when (contains? input field)]
    (rules/nonblank! field (get input field)))
  (when (and (contains? input :password) (< (count (:password input)) 8))
    (rules/fail 422 :password "is too short"))
  (doseq [field [:bio :image] :when (contains? input field)]
    (when-not (or (nil? (get input field)) (string? (get input field)))
      (rules/fail 422 field "is invalid")))
  (duplicate! source input id)
  (let [existing (user-by-id source id)
        next-user (merge (select-keys existing [:username :email :bio :image])
                         (reduce (fn [acc field]
                                   (if (and (contains? acc field) (str/blank? (get acc field)))
                                     (assoc acc field nil) acc))
                                 (select-keys input [:username :email :bio :image]) [:bio :image]))
        hash (if (contains? input :password)
               (hashers/derive (:password input) {:alg :argon2id})
               (:password_hash existing))]
    (db/one source "UPDATE users SET username=?,email=?,bio=?,image=?,password_hash=? WHERE id=? RETURNING *"
            (:username next-user) (:email next-user) (:bio next-user) (:image next-user) hash id)))

(defn follow! [source viewer-id username follow?]
  (let [target (by-username source username)]
    (when-not target (rules/fail 404 :profile "not found"))
    (if follow?
      (when (not= viewer-id (:id target))
        (db/run source "INSERT INTO follows(follower_id,followed_id) VALUES (?,?) ON CONFLICT DO NOTHING"
                viewer-id (:id target)))
      (db/run source "DELETE FROM follows WHERE follower_id=? AND followed_id=?" viewer-id (:id target)))
    (profile source viewer-id target)))
