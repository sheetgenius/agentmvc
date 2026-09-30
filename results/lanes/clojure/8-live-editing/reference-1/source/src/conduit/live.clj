(ns conduit.live
  (:require [conduit.shares :as shares]
            [muuntaja.core :as muuntaja]
            [ring.websocket :as ws])
  (:import [java.util.concurrent Executors ScheduledExecutorService TimeUnit]))

(defn start []
  {:lock (Object.)
   :rooms (atom {})
   :scheduler (Executors/newSingleThreadScheduledExecutor)})

(defn stop! [{:keys [^ScheduledExecutorService scheduler]}]
  (.shutdownNow scheduler))

(defn- send! [socket message]
  (try
    (ws/send socket (slurp (muuntaja/encode muuntaja/instance "application/json" message)))
    true
    (catch Exception _
      (try (ws/close socket) (catch Exception _))
      false)))

(defn- presence! [members count]
  (doseq [socket (keys members)]
    (send! socket {:type "presence" :count count})))

(defn updated! [{:keys [lock rooms]} id article]
  (when id
    (locking lock
      (doseq [[socket revision] (get @rooms id)]
        (when (< revision (:revision article))
          (when (and (send! socket {:type "updated" :article article})
                     (contains? (get @rooms id) socket))
            (swap! rooms assoc-in [id socket] (:revision article))))))))

(defn revoked! [{:keys [lock rooms]} id]
  (when id
    (locking lock
      (let [members (get @rooms id)]
        (swap! rooms dissoc id)
        (doseq [socket (keys members)]
          (send! socket {:type "revoked"})
          (ws/close socket))))))

(defn- remove! [{:keys [lock rooms]} id socket]
  (locking lock
    (when (contains? (get @rooms id) socket)
      (let [members (dissoc (get @rooms id) socket)]
        (if (seq members)
          (do (swap! rooms assoc id members)
              (presence! members (count members)))
          (swap! rooms dissoc id))))))

(defn- subscription [message]
  (try
    (when (string? message)
      (muuntaja/decode muuntaja/instance "application/json" message))
    (catch Exception _ nil)))

(defn listener [live db id]
  (let [{:keys [lock rooms ^ScheduledExecutorService scheduler]} live
        state (atom :pending)]
    {:on-open (fn [socket]
                (.schedule scheduler
                           ^Runnable (fn []
                                       (locking lock
                                         (when (= :pending @state)
                                           (reset! state :closed)
                                           (ws/close socket))))
                           5 TimeUnit/SECONDS))
     :on-message (fn [socket message]
                   (locking lock
                     (when (= :pending @state)
                       (let [{:keys [type key]} (subscription message)
                             article (when (= "subscribe" type)
                                       (try
                                         (shares/read-article db id key)
                                         (catch clojure.lang.ExceptionInfo e
                                           (when-not (= 404 (:status (ex-data e)))
                                             (throw e))
                                           nil)))]
                         (cond
                           (nil? article)
                           (do (reset! state :closed)
                               (send! socket {:type "invalid_link"})
                               (ws/close socket))

                           (>= (count (get @rooms id)) 100)
                           (do (reset! state :closed)
                               (send! socket {:type "room_full" :limit 100})
                               (ws/close socket))

                           :else
                           (let [members (assoc (get @rooms id {}) socket (:revision article))]
                             (swap! rooms assoc id members)
                             (reset! state :admitted)
                             (send! socket {:type "ready" :article article :presence (count members)})
                             (presence! (dissoc members socket) (count members))))))))
     :on-close (fn [socket _ _]
                 (reset! state :closed)
                 (remove! live id socket))
     :on-error (fn [socket _]
                 (ws/close socket))}))
