(ns conduit.reference-integration-test
  (:require [clojure.test :refer [deftest is use-fixtures]]
            [conduit.articles :as articles]
            [conduit.database :as database]
            [conduit.db :as db]
            [conduit.exports :as exports]
            [conduit.http :as http]
            [conduit.migrations :as migrations]
            [conduit.queue :as queue]
            [conduit.shares :as shares]
            [conduit.users :as users])
  (:import [java.util UUID]
           [java.util.concurrent LinkedBlockingQueue TimeUnit]))

(def ^:dynamic *source* nil)

(use-fixtures :once
  (fn [f]
    (let [url (or (System/getenv "DATABASE_URL")
                  (throw (ex-info "Reference integration tests require DATABASE_URL" {})))]
      (with-open [source (database/open-pool url)]
        (migrations/migrate! source)
        (binding [*source* source] (f))))))

(defn await! [pred]
  (let [deadline (+ (System/nanoTime) (* 1000000000 10))]
    (loop []
      (cond
        (pred) true
        (> (System/nanoTime) deadline) (throw (ex-info "Timed out waiting for regression boundary" {}))
        :else (do (Thread/sleep 10) (recur))))))

(defn article! [status]
  (let [name (str "reference-" (UUID/randomUUID))
        user (db/one *source* "INSERT INTO users(username,email,password_hash) VALUES (?,?,?) RETURNING *"
                     name (str name "@test.invalid") "unused")
        article (articles/create! *source* (:id user)
                                  {:title "Before" :description "Regression" :body "Before"
                                   :tagList ["before"] :status status})]
    {:user user :article (articles/by-slug *source* (:slug article) (:id user))}))

(deftest revoked-capability-cannot-save-after-waiting-for-article-lock
  (let [{:keys [article]} (article! "published")
        link (shares/rotate! *source* (:id article))
        capability (shares/authorized! *source* (:id link) (:key link))
        original-one db/one
        locked (promise)
        release (promise)
        waiting-pid (promise)]
    (with-redefs [db/one (fn [source sql & args]
                           (when (= sql "SELECT * FROM articles WHERE id=? FOR UPDATE")
                             (deliver waiting-pid (:pid (original-one source "SELECT pg_backend_pid() AS pid"))))
                           (let [row (apply original-one source sql args)]
                             (when (= sql "SELECT id FROM articles WHERE id=? FOR UPDATE")
                               (deliver locked true)
                               @release)
                             row))]
      (let [revoker (future (shares/revoke! *source* (:id article)))]
        (try
          (is (= true (deref locked 3000 :timeout)))
          (let [save (future
                       (try
                         (shares/edit! *source* capability {:title "After" :body "After" :revision 1})
                         200
                         (catch clojure.lang.ExceptionInfo e (:status (ex-data e)))))
                pid (deref waiting-pid 3000 :timeout)]
            (is (integer? pid))
            (await! #(= "Lock" (:wait_event_type
                                (original-one *source* "SELECT wait_event_type FROM pg_stat_activity WHERE pid=?" pid))))
            (deliver release true)
            (is (not= :timeout (deref revoker 3000 :timeout)))
            (is (= 404 (deref save 3000 :timeout)))
            (is (= "Before" (:body (articles/article-row *source* (:id article) nil)))))
          (finally (deliver release true)))))))

(deftest export-keeps-fields-and-tags-from-one-snapshot
  (let [{:keys [user article]} (article! "draft")
        export (exports/request! *source* (:id user))
        original-all db/all
        read-fields (promise)
        release (promise)]
    (with-redefs [db/all (fn [source sql & args]
                           (let [rows (apply original-all source sql args)]
                             (when (.startsWith ^String sql "SELECT a.id,a.slug,a.title,a.description,a.body,a.status,")
                               (deliver read-fields true)
                               @release)
                             rows))]
      (let [job (future (exports/snapshot! *source* {:id (:id export) :user-id (:id user)}))]
        (try
          (is (= true (deref read-fields 3000 :timeout)))
          (articles/edit! *source* (:id article) (:id user) {:title "After" :tagList ["after"]} false)
          (deliver release true)
          (is (not= :timeout (deref job 3000 :timeout)))
          (let [done (exports/find! *source* (:id user) (:id export))
                snapshot (first (:articles done))]
            (is (= "done" (:status done)))
            (is (= "Before" (get snapshot "title")))
            (is (= ["before"] (get snapshot "tagList"))))
          (finally (deliver release true)))))))

(deftest export-worker-recovers-from-a-transient-handler-failure
  (let [{:keys [user]} (article! "published")
        export (exports/request! *source* (:id user))
        attempts (atom 0)
        original-snapshot exports/snapshot!]
    (with-redefs [exports/snapshot! (fn [source payload]
                                      (when (and (= (:id export) (:id payload)) (= 1 (swap! attempts inc)))
                                        (throw (ex-info "Injected transient failure" {})))
                                      (original-snapshot source payload))]
      (let [worker (queue/start! (queue/create-worker *source* (partial queue/handle *source*)))]
        (try
          (await! #(= "done" (:status (exports/find! *source* (:id user) (:id export)))))
          (is (= 2 @attempts))
          (finally (queue/stop! worker)))))))

(deftest owner-publish-notifies-and-delete-releases-room
  (let [{:keys [user article]} (article! "draft")
        link (shares/rotate! *source* (:id article))
        client {:socket (Object.) :queue (LinkedBlockingQueue. 8) :sender (atom nil)
                :state (atom {:share-id (:id link) :last-revision 1})}
        handler (http/handler *source* "reference-test-secret")
        request {:headers {"authorization" (str "Token " (users/token "reference-test-secret" user))
                           "accept" "application/json"}}
        path (str "/api/articles/" (:slug article))]
    (swap! shares/rooms assoc (:id link) #{client})
    (try
      (is (= 200 (:status (handler (assoc request :request-method :post :uri (str path "/publish"))))))
      (let [event (.poll ^LinkedBlockingQueue (:queue client) 2 TimeUnit/SECONDS)]
        (is (= "updated" (:type event)))
        (is (= 2 (get-in event [:article :revision]))))
      (is (= 204 (:status (handler (assoc request :request-method :delete :uri path)))))
      (is (= "revoked" (:type (.poll ^LinkedBlockingQueue (:queue client) 2 TimeUnit/SECONDS))))
      (is (not (contains? @shares/rooms (:id link))))
      (finally (swap! shares/rooms dissoc (:id link))))))
