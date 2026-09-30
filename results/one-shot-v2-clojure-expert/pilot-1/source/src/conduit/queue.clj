(ns conduit.queue
  (:require [proletarian.worker :as worker]
            [conduit.exports :as exports]))

(defn create-worker
  "Create an unstarted durable worker. Register an application handler of [job-type payload]."
  [data-source handler]
  (worker/create-queue-worker data-source handler
                              {:proletarian/polling-interval-ms 250
                               :proletarian/worker-threads 2
                               :proletarian/log (fn [event _data]
                                                  (when-not (= event :proletarian.worker/polling-for-jobs)
                                                    (println (str event))))}))

(defn handle [source job-type payload]
  (case job-type
    :conduit/export (exports/snapshot! source payload)
    (throw (ex-info "Unknown job type" {:job-type job-type}))))

(defn start! [queue-worker]
  (worker/start! queue-worker)
  queue-worker)

(defn stop! [queue-worker]
  (worker/stop! queue-worker))
