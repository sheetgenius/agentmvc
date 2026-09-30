(ns conduit.shares
  (:require [clojure.data.json :as json]
            [conduit.articles :as articles]
            [conduit.db :as db]
            [conduit.rules :as rules]
            [next.jdbc :as jdbc]
            [ring.websocket :as websocket])
  (:import [java.security MessageDigest SecureRandom]
           [java.util Base64 HexFormat]
           [java.util.concurrent LinkedBlockingQueue]))

(defonce rooms (atom {}))
(def room-lock (Object.))
(def ^:private close-marker ::close)

(declare leave!)

(defn disconnect! [member]
  (let [^LinkedBlockingQueue queue (:queue member)
        [before _] (swap-vals! (:state member) assoc :closed? true)]
    (when-not (:closed? before)
      (.start (Thread/ofVirtual)
              ^Runnable
              (fn []
                (leave! member)
                (locking queue
                  (.clear queue)
                  (.offer queue close-marker))
                (when-let [^Thread sender @(:sender member)] (.interrupt sender))
                (try (websocket/close (:socket member)) (catch Exception _ nil)))))))

(defn random-key [size]
  (let [bytes (byte-array size)]
    (.nextBytes (SecureRandom.) bytes)
    (.encodeToString (.withoutPadding (Base64/getUrlEncoder)) bytes)))

(defn key-hash [key]
  (.formatHex (HexFormat/of) (.digest (MessageDigest/getInstance "SHA-256") (.getBytes key "UTF-8"))))

(defn active [source id key]
  (when (string? key)
    (when-let [row (db/one source "SELECT * FROM shares WHERE id=?" id)]
      (when (MessageDigest/isEqual (.parseHex (HexFormat/of) (:key_hash row))
                                   (.parseHex (HexFormat/of) (key-hash key)))
        row))))

(defn authorized! [source id key]
  (or (active source id key) (rules/fail 404 :share "not found")))

(defn read-article [source share]
  (some-> (articles/article-row source (:article_id share) nil) articles/shared))

(defn enqueue! [member message]
  (let [^LinkedBlockingQueue queue (:queue member)
        accepted (locking queue
                   (when-not (:closed? @(:state member))
                     (.offer queue message)))]
    (when (false? accepted) (disconnect! member))
    accepted))

(defn close-member! [member]
  (swap! (:state member) assoc :closing? true)
  (enqueue! member close-marker))

(defn sender! [member]
  (let [thread (.unstarted (Thread/ofVirtual)
                           ^Runnable
                           (fn []
                             (try
                               (loop []
                                 (let [message (.take ^LinkedBlockingQueue (:queue member))]
                                   (when-not (= close-marker message)
                                     (websocket/send (:socket member) (json/write-str message))
                                     (recur))))
                               (catch Exception _ nil)
                               (finally (disconnect! member)))))]
    (reset! (:sender member) thread)
    (.start thread)
    thread))

(defn leave! [member]
  (locking room-lock
    (when-let [id (:share-id @(:state member))]
      (let [old (get @rooms id #{})
            remaining (disj old member)]
        (swap! (:state member) dissoc :share-id)
        (if (seq remaining) (swap! rooms assoc id remaining) (swap! rooms dissoc id))
        (doseq [peer remaining]
          (enqueue! peer {:type "presence" :count (count remaining)}))))))

(defn revoke-room! [id]
  (locking room-lock
    (let [members (get @rooms id)]
      (swap! rooms dissoc id)
      (doseq [member members]
        (swap! (:state member) dissoc :share-id)
        (enqueue! member {:type "revoked"})
        (close-member! member)))))

(defn rotate! [source article-id]
  (let [id (random-key 16) key (random-key 32)
        old (jdbc/with-transaction [tx source]
              (when-not (db/one tx "SELECT id FROM articles WHERE id=? FOR UPDATE" article-id)
                (rules/fail 404 :article "not found"))
              (let [previous (:id (db/one tx "DELETE FROM shares WHERE article_id=? RETURNING id" article-id))]
                (db/run tx "INSERT INTO shares(id,article_id,key_hash) VALUES (?,?,?)"
                        id article-id (key-hash key))
                previous))]
    (when old (revoke-room! old))
    {:id id :key key}))

(defn revoke! [source article-id]
  (let [old (jdbc/with-transaction [tx source]
              (db/one tx "SELECT id FROM articles WHERE id=? FOR UPDATE" article-id)
              (:id (db/one tx "DELETE FROM shares WHERE article_id=? RETURNING id" article-id)))]
    (when old (revoke-room! old))))

(defn delete-article! [source article-id]
  (let [old (jdbc/with-transaction [tx source]
              (db/one tx "SELECT id FROM articles WHERE id=? FOR UPDATE" article-id)
              (let [share (:id (db/one tx "SELECT id FROM shares WHERE article_id=?" article-id))]
                (articles/delete! tx article-id)
                share))]
    (when old (revoke-room! old))))

(declare broadcast!)

(defn edit! [source share input]
  (try
    (let [updated (jdbc/with-transaction [tx source]
                    (let [locked (db/one tx "SELECT * FROM articles WHERE id=? FOR UPDATE" (:article_id share))
                          current (db/one tx "SELECT * FROM shares WHERE id=? AND article_id=?"
                                          (:id share) (:article_id share))]
                      (when-not (and locked current (= (:key_hash share) (:key_hash current)))
                        (rules/fail 404 :share "not found"))
                      (when-not (and (map? input)
                                     (= (set (keys input)) #{:title :body :revision}))
                        (rules/fail 422 :article "is invalid"))
                      (articles/edit-locked! tx locked nil input true)))
          representation (select-keys updated [:slug :title :body :revision])]
      (broadcast! (:id share) representation)
      representation)
    (catch clojure.lang.ExceptionInfo e
      (if-let [article (:article (ex-data e))]
        (throw (ex-info (.getMessage e) (assoc (ex-data e) :article (select-keys article [:slug :title :body :revision]))))
        (throw e)))))

(defn broadcast! [id article]
  (locking room-lock
    (doseq [member (get @rooms id)]
      (let [last-revision (:last-revision @(:state member))]
        (when (> (:revision article) last-revision)
          (when (enqueue! member {:type "updated" :article article})
            (swap! (:state member) assoc :last-revision (:revision article))))))))

(defn notify-article! [source article-id]
  (when-let [share (db/one source "SELECT * FROM shares WHERE article_id=?" article-id)]
    (when-let [article (read-article source share)]
      (broadcast! (:id share) article))))

(defn subscribe! [source id member key]
  (locking room-lock
    (if-let [share (active source id key)]
      (let [members (get @rooms id #{})]
        (if (>= (count members) 100)
          (do (enqueue! member {:type "room_full" :limit 100}) (close-member! member))
          (let [article (read-article source share)
                joined (conj members member)
                count-now (count joined)]
            (swap! (:state member) assoc :share-id id :last-revision (:revision article))
            (swap! rooms assoc id joined)
            (enqueue! member {:type "ready" :article article :presence count-now})
            (doseq [peer members]
              (enqueue! peer {:type "presence" :count count-now})))))
      (do (enqueue! member {:type "invalid_link"}) (close-member! member)))))

(defn listener [source id]
  (let [member* (atom nil)]
    {:on-open (fn [socket]
                (let [member {:socket socket :queue (LinkedBlockingQueue. 256) :sender (atom nil)
                              :state (atom {:last-revision 0})}]
                  (reset! member* member)
                  (sender! member)
                  (.start (Thread/ofVirtual)
                          ^Runnable (fn []
                                      (Thread/sleep 5000)
                                      (when-not (:share-id @(:state member))
                                        (close-member! member))))))
     :on-message (fn [_ message]
                   (when-let [member @member*]
                     (when-not (some @(:state member) [:share-id :closing? :closed?])
                       (let [data (try (json/read-str message :key-fn keyword)
                                       (catch Exception _ nil))]
                         (subscribe! source id member (when (= "subscribe" (:type data)) (:key data)))))))
     :on-close (fn [_ _ _] (when-let [member @member*] (disconnect! member)))
     :on-error (fn [_ _] (when-let [member @member*] (disconnect! member)))}))
