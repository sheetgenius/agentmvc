(ns conduit.rules-test
  (:require [clojure.test :refer [deftest is testing]]
            [conduit.rules :as rules]))

(defn failure [f]
  (try (f) nil (catch clojure.lang.ExceptionInfo e (ex-data e))))

(deftest draft-visibility-and-ownership
  (let [draft {:status "draft" :author_id 7}
        published {:status "published" :author_id 7}]
    (testing "a draft looks absent to everyone except its author"
      (is (= 404 (:status (failure #(rules/visible-article! draft nil)))))
      (is (= 404 (:status (failure #(rules/visible-article! draft 8)))))
      (is (= draft (rules/visible-article! draft 7))))
    (testing "a published article is visible but mutation still needs ownership"
      (is (= published (rules/visible-article! published 8)))
      (is (= 403 (:status (failure #(rules/author! published 8))))))
    (testing "drafts reject interactions"
      (is (= 422 (:status (failure #(rules/published! draft))))))))

(deftest revision-conflict
  (let [current {:revision 4 :title "Current"}
        stale (failure #(rules/revision! 3 4 current))]
    (is (= 409 (:status stale)))
    (is (= current (:article stale)))
    (is (= 422 (:status (failure #(rules/revision! "4" 4 current)))))
    (is (nil? (rules/revision! 4 4 current)))))
