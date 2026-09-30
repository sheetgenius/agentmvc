(ns conduit.http
  (:require [conduit.articles :as articles]
            [conduit.users :as users]
            [muuntaja.core :as muuntaja]
            [reitit.ring :as ring]
            [reitit.ring.middleware.muuntaja :as format]
            [reitit.ring.middleware.parameters :as parameters]))

(defn- response
  ([body] (response 200 body))
  ([status body] {:status status :body body}))

(defn- no-content [_]
  {:status 204})

(defn- request-body [request key]
  (get-in request [:body-params key]))

(defn- param [request key]
  (get-in request [:path-params key]))

(defn- authorized [f]
  (fn [request]
    (users/require-user request)
    (f request)))

(defn- wrap-api [handler db secret]
  (fn [request]
    (if (= :options (:request-method request))
      {:status 204 :headers {"Access-Control-Allow-Origin" "*"
                             "Access-Control-Allow-Headers" "Content-Type, Authorization"
                             "Access-Control-Allow-Methods" "GET, POST, PUT, DELETE, OPTIONS"}}
      (try
        (let [result (handler (assoc request :current-user
                                     (users/current db secret (get-in request [:headers "authorization"]))))]
          (update result :headers merge {"Access-Control-Allow-Origin" "*"}))
        (catch clojure.lang.ExceptionInfo e
          (let [{:keys [status errors]} (ex-data e)]
            {:status status :headers {"Content-Type" "application/json; charset=utf-8"
                                      "Access-Control-Allow-Origin" "*"}
             :body (muuntaja/encode muuntaja/instance "application/json" {:errors errors})}))))))

(defn handler [db secret]
  (wrap-api
   (ring/ring-handler
    (ring/router
     [["/health" {:get (fn [_] (response {:status "ok"}))}]
      ["/api"
       ["/users" {:post (fn [r] (response 201 {:user (users/public secret (users/register! db (request-body r :user)))}))}]
       ["/users/login" {:post (fn [r] (response {:user (users/public secret (users/login! db (request-body r :user)))}))}]
       ["/user" {:get (authorized (fn [r] (response {:user (users/public secret (:current-user r))})))
                 :put (authorized (fn [r] (response {:user (users/public secret (users/update! db (:current-user r) (request-body r :user)))})))}]
       ["/profiles/:username"
        {:get (fn [r] (response {:profile (users/get-profile db (:current-user r) (param r :username))}))}]
       ["/profiles/:username/follow"
        {:post (authorized (fn [r] (response {:profile (users/follow! db (:current-user r) (param r :username) true)})))
         :delete (authorized (fn [r] (response {:profile (users/follow! db (:current-user r) (param r :username) false)})))}]
       ["/articles" {:get (fn [r] (response (articles/listing db (:current-user r) (:query-params r) false)))
                     :post (authorized (fn [r] (response 201 {:article (articles/create! db (:current-user r) (request-body r :article))})))}]
       ["/articles/feed" {:get (authorized (fn [r] (response (articles/listing db (:current-user r) (:query-params r) true))))}]
       ["/articles/:slug"
        {:get (fn [r] (response {:article (articles/present db (:current-user r) (articles/find-article db (param r :slug)) true)}))
         :put (authorized (fn [r] (response {:article (articles/update! db (:current-user r) (param r :slug) (request-body r :article))})))
         :delete (authorized (fn [r] (no-content (articles/delete! db (:current-user r) (param r :slug)))))}]
       ["/articles/:slug/favorite"
        {:post (authorized (fn [r] (response {:article (articles/favorite! db (:current-user r) (param r :slug) true)})))
         :delete (authorized (fn [r] (response {:article (articles/favorite! db (:current-user r) (param r :slug) false)})))}]
       ["/articles/:slug/comments"
        {:get (fn [r] (response {:comments (articles/comments db (:current-user r) (param r :slug))}))
         :post (authorized (fn [r] (response 201 {:comment (articles/add-comment! db (:current-user r) (param r :slug) (request-body r :comment))})))}]
       ["/articles/:slug/comments/:id"
        {:delete (authorized (fn [r] (no-content (articles/delete-comment! db (:current-user r) (param r :slug) (param r :id)))))}]
       ["/tags" {:get (fn [_] (response {:tags (articles/all-tags db)}))}]]]
     {:conflicts nil
      :data {:muuntaja muuntaja/instance
             :middleware [parameters/parameters-middleware
                          format/format-negotiate-middleware
                          format/format-response-middleware
                          format/format-request-middleware]}})
    (ring/create-default-handler))
   db secret))
