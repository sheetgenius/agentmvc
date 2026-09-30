(ns conduit.queue
  (:require [proletarian.worker :as worker]))

(defn create-worker
  "Create an unstarted durable worker. Register an application handler of [job-type payload]."
  [data-source handler]
  (worker/create-queue-worker data-source handler
                              {:proletarian/polling-interval-ms 250
                               :proletarian/worker-threads 2
                               :proletarian/log (fn [event _data]
                                                  (when-not (= event :proletarian.worker/polling-for-jobs)
                                                    (println (str event))))}))

(defn start! [queue-worker]
  (worker/start! queue-worker)
  queue-worker)

(defn stop! [queue-worker]
  (worker/stop! queue-worker))
