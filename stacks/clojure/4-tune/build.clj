(ns build
  (:require [clojure.data.json :as json]
            [clojure.java.io :as io]
            [clojure.tools.build.api :as b])
  (:import [java.security MessageDigest]
           [java.util HexFormat]))

(def class-dir "target/classes")
(def basis (delay (b/create-basis {:project "deps.edn"})))

(defn- sha256 [path]
  (let [digest (MessageDigest/getInstance "SHA-256")]
    (with-open [input (io/input-stream path)]
      (let [buffer (byte-array 65536)]
        (loop []
          (let [n (.read input buffer)]
            (when (pos? n)
              (.update digest buffer 0 n)
              (recur))))))
    (.formatHex (HexFormat/of) (.digest digest))))

(defn inventory
  "Record the exact runtime basis and resolved artifacts; emit OSV's custom lock input."
  [_]
  (let [libs (sort-by (comp str key) (:libs @basis))
        packages (for [[lib {:keys [mvn/version]}] libs :when version]
                   {:package {:name (str (namespace lib) ":" (name lib))
                              :version version :ecosystem "Maven"}})
        unscanned (for [[lib coordinates] libs :when (not (:mvn/version coordinates))]
                    {:library (str lib) :coordinates (dissoc coordinates :paths)})
        artifacts (for [[lib {:keys [mvn/version paths]}] libs
                        path paths :when (.isFile (io/file path))]
                    {:library (str lib) :version version
                     :file (.getName (io/file path)) :sha256 (sha256 path)})]
    (.mkdirs (io/file "target"))
    (spit "target/resolved-basis.edn" (pr-str @basis))
    (spit "target/resolved-artifacts.json"
          (json/write-str {:scope "production runtime" :artifacts artifacts :unscanned unscanned}))
    (spit "target/resolved-osv.json" (json/write-str {:results [{:packages packages}]}))))

(defn uber [_]
  (b/delete {:path "target"})
  (b/copy-dir {:src-dirs ["src" "resources"] :target-dir class-dir})
  (b/compile-clj {:basis @basis :src-dirs ["src"] :class-dir class-dir})
  (b/uber {:class-dir class-dir :uber-file "target/conduit.jar"
           :basis @basis :main 'conduit.main}))
