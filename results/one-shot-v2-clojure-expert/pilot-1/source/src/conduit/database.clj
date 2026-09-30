(ns conduit.database
  (:require [clojure.string :as str]
            [next.jdbc.connection :as connection])
  (:import [com.zaxxer.hikari HikariDataSource]
           [java.net URI URLDecoder]
           [java.nio.charset StandardCharsets]))

(defn- decode [s]
  (URLDecoder/decode s StandardCharsets/UTF_8))

(defn open-pool [database-url]
  (let [uri (URI. database-url)
        [username password] (some-> (.getRawUserInfo uri) (str/split #":" 2))
        port (if (neg? (.getPort uri)) 5432 (.getPort uri))
        jdbc-url (str "jdbc:postgresql://" (.getHost uri) ":" port (.getRawPath uri)
                      (when-let [query (.getRawQuery uri)] (str "?" query)))]
    (connection/->pool HikariDataSource
                       (cond-> {:jdbcUrl jdbc-url :maximumPoolSize 10
                                :connectionTimeout 5000 :poolName "conduit"}
                         username (assoc :username (decode username))
                         password (assoc :password (decode password))))))
