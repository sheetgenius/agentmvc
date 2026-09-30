(ns conduit.system
  (:require [conduit.config :as config]
            [conduit.database :as database]
            [conduit.http :as http]
            [conduit.migrations :as migrations]
            [conduit.queue :as queue]
            [integrant.core :as ig]
            [ring.adapter.jetty :as jetty])
  (:import [com.zaxxer.hikari HikariDataSource]
           [org.eclipse.jetty.server Server]))

(defn configuration []
  (let [{:keys [database-url port secret-key-base]} (config/environment)]
    {::database {:url database-url}
     ::migrations {:database (ig/ref ::database)}
     ::worker {:database (ig/ref ::database) :migrations (ig/ref ::migrations)}
     ::handler {:database (ig/ref ::database) :migrations (ig/ref ::migrations) :secret secret-key-base}
     ::server {:handler (ig/ref ::handler) :port port}}))

(defmethod ig/init-key ::database [_ {:keys [url]}]
  (database/open-pool url))

(defmethod ig/halt-key! ::database [_ data-source]
  (.close ^HikariDataSource data-source))

(defmethod ig/init-key ::migrations [_ {:keys [database]}]
  (migrations/migrate! database))

(defmethod ig/init-key ::worker [_ {:keys [database]}]
  (queue/start! (queue/create-worker database (partial queue/handle database))))

(defmethod ig/halt-key! ::worker [_ worker]
  (queue/stop! worker))

(defmethod ig/init-key ::handler [_ {:keys [database secret]}]
  (http/handler database secret))

(defmethod ig/init-key ::server [_ {:keys [handler port]}]
  (jetty/run-jetty handler {:host "0.0.0.0" :port port :join? false
                            :configurator (fn [^Server server] (.setStopTimeout server 5000))}))

(defmethod ig/halt-key! ::server [_ server]
  (.stop ^Server server))
