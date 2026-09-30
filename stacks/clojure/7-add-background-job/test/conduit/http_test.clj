(ns conduit.http-test
  (:require [clojure.test :refer [deftest is]]
            [conduit.http :as http]))

(deftest health-route
  (let [response ((http/handler nil "test") {:request-method :get :uri "/health"
                                             :headers {"accept" "application/json"}})]
    (is (= 200 (:status response)))
    (is (= "application/json; charset=utf-8" (get-in response [:headers "Content-Type"])))))
