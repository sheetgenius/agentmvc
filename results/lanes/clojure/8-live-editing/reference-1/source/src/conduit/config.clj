(ns conduit.config)

(defn- required [key]
  (or (not-empty (System/getenv key))
      (throw (ex-info (str "Missing required environment setting: " key) {:setting key}))))

(defn environment []
  {:database-url (required "DATABASE_URL")
   :secret-key-base (required "SECRET_KEY_BASE")
   :port (Long/parseLong (or (System/getenv "PORT") "4112"))})
