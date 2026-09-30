(ns conduit.main
  (:gen-class)
  (:require [conduit.system :as system]
            [integrant.core :as ig]))

(defn -main [& _]
  (let [running (ig/init (system/configuration))]
    (.addShutdownHook (Runtime/getRuntime)
                      (Thread. ^Runnable #(ig/halt! running)))))
