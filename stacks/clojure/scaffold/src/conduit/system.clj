(ns conduit.system
  (:require [conduit.config :as config]
            [conduit.database :as database]
            [conduit.http :as http]
            [conduit.migrations :as migrations]
            [integrant.core :as ig]
            [ring.adapter.jetty :as jetty])
  (:import [com.zaxxer.hikari HikariDataSource]
           [org.eclipse.jetty.server Server]))

(defn configuration []
  (let [{:keys [database-url port]} (config/environment)]
    {::database {:url database-url}
     ::migrations {:database (ig/ref ::database)}
     ::handler {:database (ig/ref ::database) :migrations (ig/ref ::migrations)}
     ::server {:handler (ig/ref ::handler) :port port}}))

(defmethod ig/init-key ::database [_ {:keys [url]}]
  (database/open-pool url))

(defmethod ig/halt-key! ::database [_ data-source]
  (.close ^HikariDataSource data-source))

(defmethod ig/init-key ::migrations [_ {:keys [database]}]
  (migrations/migrate! database))

(defmethod ig/init-key ::handler [_ {:keys [database]}]
  (http/handler database))

(defmethod ig/init-key ::server [_ {:keys [handler port]}]
  (jetty/run-jetty handler {:host "0.0.0.0" :port port :join? false
                            :configurator (fn [^Server server] (.setStopTimeout server 5000))}))

(defmethod ig/halt-key! ::server [_ server]
  (.stop ^Server server))
