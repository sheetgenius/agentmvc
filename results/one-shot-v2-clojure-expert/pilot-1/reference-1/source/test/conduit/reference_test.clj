(ns conduit.reference-test
  (:require [clojure.test :refer [deftest is]]
            [conduit.shares :as shares]
            [conduit.users :as users]
            [ring.websocket :as websocket])
  (:import [java.util UUID]
           [java.util.concurrent CountDownLatch LinkedBlockingQueue TimeUnit]))

(deftest password-work-is-bounded-and-releases-after-failure
  (is (thrown? Exception (users/password-work #(throw (Exception. "failure")))))
  (let [entered (CountDownLatch. 2)
        release (promise)
        active (atom 0)
        peak (atom 0)
        work (doall (repeatedly 6 #(future
                                     (users/password-work
                                      (fn []
                                        (swap! peak max (swap! active inc))
                                        (.countDown entered)
                                        (try @release (finally (swap! active dec))))))))]
    (try
      (is (.await entered 2 TimeUnit/SECONDS))
      (is (= 2 @active))
      (finally (deliver release true)))
    (doseq [result work] (is (= true (deref result 3000 :timeout))))
    (is (= 2 @peak))
    (is (= :available (users/password-work (constantly :available))))))

(deftest concurrent-login-admission-reserves-before-work
  (let [email (str (UUID/randomUUID))
        start (promise)
        work (doall (repeatedly 25 #(future
                                      @start
                                      (try
                                        (users/reserve-login! email)
                                        :admitted
                                        (catch clojure.lang.ExceptionInfo e (:status (ex-data e)))))))]
    (deliver start true)
    (is (= {:admitted 20 429 5} (frequencies (map #(deref % 3000 :timeout) work))))
    (swap! users/login-failures dissoc email)))

(deftest token-validation-does-not-hide-database-failures
  (let [credential (users/token "reference-secret" {:id 7})]
    (with-redefs [users/user-by-id (fn [_ _] (throw (ex-info "Database unavailable" {:database true})))]
      (is (thrown-with-msg? clojure.lang.ExceptionInfo #"Database unavailable"
                            (users/from-token nil "reference-secret" credential))))))

(defn member [capacity]
  {:socket (Object.) :queue (LinkedBlockingQueue. capacity) :sender (atom nil)
   :state (atom {:share-id (str (UUID/randomUUID)) :last-revision 1})})

(deftest idle-disconnect-terminates-sender-and-releases-room
  (let [client (member 1)
        id (:share-id @(:state client))
        closed (promise)]
    (with-redefs [websocket/close (fn [_] (deliver closed true))]
      (swap! shares/rooms assoc id #{client})
      (let [^Thread sender (shares/sender! client)
            ^Thread cleanup (shares/disconnect! client)]
        (.join cleanup 2000)
        (.join sender 2000)
        (is (= true (deref closed 1000 :timeout)))
        (is (not (.isAlive sender)))
        (is (not (contains? @shares/rooms id)))))))

(deftest full-output-queue-disconnects-a-blocked-sender
  (let [client (member 1)
        id (:share-id @(:state client))
        sending (promise)
        release (promise)
        closed (promise)]
    (with-redefs [websocket/send (fn [_ _] (deliver sending true) @release)
                  websocket/close (fn [_] (deliver closed true))]
      (swap! shares/rooms assoc id #{client})
      (let [^Thread sender (shares/sender! client)]
        (try
          (is (shares/enqueue! client {:type "first"}))
          (is (= true (deref sending 2000 :timeout)))
          (is (shares/enqueue! client {:type "buffered"}))
          (is (false? (shares/enqueue! client {:type "overflow"})))
          (is (= true (deref closed 2000 :timeout)))
          (.join sender 2000)
          (is (not (.isAlive sender)))
          (is (not (contains? @shares/rooms id)))
          (finally
            (deliver release true)
            (shares/disconnect! client)))))))
