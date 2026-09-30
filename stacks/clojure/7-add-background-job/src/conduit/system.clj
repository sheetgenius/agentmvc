(ns conduit.system
  (:require [conduit.config :as config]
            [conduit.database :as database]
            [conduit.exports :as exports]
            [conduit.http :as http]
            [conduit.migrations :as migrations]
            [integrant.core :as ig]
            [proletarian.worker :as worker]
            [ring.adapter.jetty :as jetty])
  (:import [com.zaxxer.hikari HikariDataSource]
           [org.eclipse.jetty.server Server]))

(defn configuration []
  (let [{:keys [database-url port secret-key-base]} (config/environment)]
    {::database {:url database-url}
     ::migrations {:database (ig/ref ::database)}
     ::worker {:database (ig/ref ::database) :migrations (ig/ref ::migrations)}
     ::handler {:database (ig/ref ::database) :migrations (ig/ref ::migrations)
                :secret secret-key-base}
     ::server {:handler (ig/ref ::handler) :worker (ig/ref ::worker) :port port}}))

(defmethod ig/init-key ::database [_ {:keys [url]}]
  (database/open-pool url))

(defmethod ig/halt-key! ::database [_ data-source]
  (.close ^HikariDataSource data-source))

(defmethod ig/init-key ::migrations [_ {:keys [database]}]
  (migrations/migrate! database))

(defmethod ig/init-key ::worker [_ {:keys [database]}]
  (doto (worker/create-queue-worker
         database
         (fn [job-type export-id]
           (case job-type
             :conduit.exports/build (exports/build! database export-id)
             (throw (ex-info "Unknown job type" {:job-type job-type}))))
         {:proletarian/polling-interval-ms 250
          :proletarian/retry-strategy-fn (fn [_ _] {:retries 3 :delays [1000 5000 30000]})
          :proletarian/log (fn [event data]
                             (when-not (= event :proletarian.worker/polling-for-jobs)
                               (println event data)))})
    worker/start!))

(defmethod ig/halt-key! ::worker [_ queue-worker]
  (worker/stop! queue-worker))

(defmethod ig/init-key ::handler [_ {:keys [database secret]}]
  (http/handler database secret))

(defmethod ig/init-key ::server [_ {:keys [handler port]}]
  (jetty/run-jetty handler {:host "0.0.0.0" :port port :join? false
                            :configurator (fn [^Server server] (.setStopTimeout server 5000))}))

(defmethod ig/halt-key! ::server [_ server]
  (.stop ^Server server))
