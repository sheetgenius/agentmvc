(ns conduit.users
  (:require [buddy.hashers :as hashers]
            [buddy.sign.jwt :as jwt]
            [clojure.string :as str]
            [conduit.domain :as domain]
            [conduit.store :as store]
            [honey.sql :as sql]))

(defn user-by-id [db id]
  (store/one db "SELECT * FROM users WHERE id = ?" id))

(defn token [secret user]
  (jwt/sign {:id (:id user) :exp (+ (quot (System/currentTimeMillis) 1000) (* 60 60 24 30))}
            secret))

(defn current [db secret authorization]
  (when (and authorization (str/starts-with? authorization "Token "))
    (try
      (when-let [id (:id (jwt/unsign (subs authorization 6) secret))]
        (user-by-id db id))
      (catch Exception _ nil))))

(defn require-user [request]
  (or (:current-user request) (domain/fail 401 :token "is missing")))

(defn public [secret user]
  {:email (:email user) :username (:username user) :bio (:bio user)
   :image (:image user) :token (token secret user)})

(defn- password! [password]
  (when (< (count password) 8)
    (domain/fail 422 :password "is too short")))

(defn- available! [db field value id]
  (when (store/one db (str "SELECT id FROM users WHERE " (name field) " = ? AND id <> ?")
                   value (or id -1))
    (domain/fail 409 field "has already been taken")))

(defn register! [db input]
  (domain/required input [:username :email :password])
  (password! (:password input))
  (doseq [field [:username :email]]
    (available! db field (get input field) nil))
  (store/one db "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?) RETURNING *"
             (:username input) (:email input) (hashers/derive (:password input))))

(defn login! [db input]
  (domain/required input [:email :password])
  (let [user (store/one db "SELECT * FROM users WHERE email = ?" (:email input))]
    (if (and user (hashers/check (:password input) (:password_hash user)))
      user
      (domain/fail 401 :credentials "invalid"))))

(defn update! [db user input]
  (doseq [field [:username :email :password]]
    (when (contains? input field)
      (domain/required input [field])))
  (when (contains? input :password)
    (password! (:password input)))
  (doseq [field [:username :email]]
    (when-let [value (get input field)]
      (available! db field value (:id user))))
  (let [changes (cond-> (select-keys input [:username :email :bio :image])
                  (contains? input :password) (assoc :password_hash (hashers/derive (:password input))))
        changes (reduce (fn [m field]
                          (if (= "" (get m field)) (assoc m field nil) m))
                        changes [:bio :image])]
    (if (empty? changes)
      user
      (store/statement-one db (sql/format {:update :users :set changes
                                           :where [:= :id (:id user)] :returning :*})))))

(defn- profile-user [db username]
  (domain/found (store/one db "SELECT * FROM users WHERE username = ?" username) :profile))

(defn profile [db viewer user]
  {:username (:username user) :bio (:bio user) :image (:image user)
   :following (boolean (and viewer (store/one db "SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?"
                                              (:id viewer) (:id user))))})

(defn get-profile [db viewer username]
  (profile db viewer (profile-user db username)))

(defn follow! [db viewer username follow?]
  (let [user (profile-user db username)]
    (if follow?
      (store/execute! db "INSERT INTO follows (follower_id, followed_id) VALUES (?, ?) ON CONFLICT DO NOTHING"
                      (:id viewer) (:id user))
      (store/execute! db "DELETE FROM follows WHERE follower_id = ? AND followed_id = ?"
                      (:id viewer) (:id user)))
    (profile db viewer user)))
