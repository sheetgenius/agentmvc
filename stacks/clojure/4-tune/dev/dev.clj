(ns dev
  (:require [clojure.java.io :as io]
            [clojure.tools.namespace.repl :as refresh]
            [conduit.system :as system]
            [integrant.repl :as repl]))

(refresh/set-refresh-dirs "src")
(repl/set-prep! #(system/configuration))

(defn- source-state []
  (into {} (for [root ["src" "resources"]
                 file (file-seq (io/file root))
                 :when (.isFile file)]
             [(.getPath file) [(.lastModified file) (.length file)]])))

(defn -main [& _]
  (repl/go)
  (.addShutdownHook (Runtime/getRuntime) (Thread. ^Runnable repl/halt))
  (println "Development server ready; watching src/ and resources/.")
  (loop [seen (source-state)]
    (Thread/sleep 300)
    (let [current (source-state)]
      (when (not= seen current)
        (try
          (repl/reset)
          (println "Development system refreshed.")
          (catch Exception _
            (binding [*out* *err*]
              (println "Development refresh failed; fix the source and save again.")))))
      (recur current))))
