(ns conduit.http
  (:require [clojure.data.json :as json]
            [clojure.string :as str]
            [conduit.articles :as articles]
            [conduit.db :as db]
            [conduit.exports :as exports]
            [conduit.rules :as rules]
            [conduit.shares :as shares]
            [conduit.users :as users]
            [muuntaja.core :as muuntaja]
            [reitit.coercion.malli :as malli]
            [reitit.ring :as ring]
            [reitit.ring.coercion :as coercion]
            [reitit.ring.middleware.muuntaja :as format]
            [reitit.ring.middleware.parameters :as parameters]))

(defn reply ([status body] {:status status :body body})
  ([body] (reply 200 body)))
(def no-content {:status 204 :body ""})

(defn item [request root fields]
  (let [body (:body-params request)
        nested (or (get body root) (get body (name root)))]
    (when-not (map? nested) (rules/fail 422 root "is invalid"))
    (reduce (fn [acc field]
              (cond
                (contains? nested field) (assoc acc field (get nested field))
                (contains? nested (name field)) (assoc acc field (get nested (name field)))
                :else acc)) {} fields)))

(defn share-item [request]
  (let [body (:body-params request)
        nested (or (get body :article) (get body "article"))]
    (when-not (and (map? body) (= 1 (count body)) (map? nested)
                   (= #{"title" "body" "revision"} (set (map name (keys nested)))))
      (rules/fail 422 :article "is invalid"))
    (item request :article [:title :body :revision])))

(defn path [request key] (get-in request [:path-params key]))
(defn viewer-id [request] (get-in request [:viewer :id]))
(defn required-id [request] (:id (users/required! request)))

(defn query [request]
  (reduce (fn [acc key]
            (if-let [value (get-in request [:query-params (name key)])]
              (assoc acc key value) acc))
          {} [:limit :offset :tag :author :favorited]))

(defn routes [source secret]
  [["/health" {:get (fn [_] (reply {:status "ok"}))}]
   ["/api/users" {:post (fn [request]
                          (reply 201 {:user (users/public secret
                                                          (users/register! source (item request :user [:username :email :password])))}))
                  :parameters {:body [:map [:user map?]]}}]
   ["/api/users/login" {:post (fn [request]
                                (reply {:user (users/public secret
                                                            (users/login! source (item request :user [:email :password])))}))}]
   ["/api/user" {:get (fn [request]
                        (reply {:user (users/public secret (users/required! request))}))
                 :put (fn [request]
                        (reply {:user (users/public secret
                                                    (users/update! source (required-id request)
                                                                   (item request :user [:username :email :password :bio :image])))}))}]
   ["/api/user/drafts" {:get (fn [request]
                               (reply (articles/list! source (required-id request) (query request) :drafts)))}]
   ["/api/user/exports" {:post (fn [request]
                                 (reply 202 {:export (exports/request! source (required-id request))}))}]
   ["/api/user/exports/:id" {:get (fn [request]
                                    (reply {:export (exports/find! source (required-id request) (path request :id))}))}]
   ["/api/profiles/:username" {:get (fn [request]
                                      (reply {:profile (users/profile! source (path request :username)
                                                                       (viewer-id request))}))}]
   ["/api/profiles/:username/follow"
    {:post (fn [request]
             (reply {:profile (users/follow! source (required-id request) (path request :username) true)}))
     :delete (fn [request]
               (reply {:profile (users/follow! source (required-id request) (path request :username) false)}))}]
   ["/api/tags" {:get (fn [_] (reply {:tags (articles/tags source)}))}]
   ["/api/articles" {:get (fn [request]
                            (reply (articles/list! source (viewer-id request) (query request) :public)))
                     :post (fn [request]
                             (reply 201 {:article (articles/create! source (required-id request)
                                                                    (item request :article [:title :description :body :tagList :status]))}))}]
   ["/api/articles/feed" {:get (fn [request]
                                 (reply (articles/list! source (required-id request) (query request) :feed)))}]
   ["/api/articles/:slug"
    {:get (fn [request]
            (let [row (articles/visible! source (path request :slug) (viewer-id request))]
              (reply {:article (articles/full source (:id row) (viewer-id request))})))
     :put (fn [request]
            (let [id (required-id request)
                  row (articles/authored! source (path request :slug) id)
                  article (articles/edit! source (:id row) id
                                          (item request :article [:title :description :body :tagList :revision]) false)]
              (when-let [share (:id (db/one source "SELECT id FROM shares WHERE article_id=?" (:id row)))]
                (shares/broadcast! share (shares/read-article source {:article_id (:id row)})))
              (reply {:article article})))
     :delete (fn [request]
               (let [id (required-id request)
                     row (articles/authored! source (path request :slug) id)]
                 (articles/delete! source (:id row)) no-content))}]
   ["/api/articles/:slug/publish" {:post (fn [request]
                                           (let [id (required-id request)
                                                 row (articles/authored! source (path request :slug) id)]
                                             (reply {:article (articles/publish! source (:id row) id)})))}]
   ["/api/articles/:slug/favorite"
    {:post (fn [request]
             (let [id (required-id request)
                   row (articles/visible! source (path request :slug) id)]
               (rules/published! row)
               (reply {:article (articles/favorite! source (:id row) id true)})))
     :delete (fn [request]
               (let [id (required-id request)
                     row (articles/visible! source (path request :slug) id)]
                 (rules/published! row)
                 (reply {:article (articles/favorite! source (:id row) id false)})))}]
   ["/api/articles/:slug/comments"
    {:get (fn [request]
            (let [row (articles/visible! source (path request :slug) (viewer-id request))]
              (reply {:comments (articles/comments source (:id row) (viewer-id request))})))
     :post (fn [request]
             (let [id (required-id request)
                   row (articles/visible! source (path request :slug) id)]
               (rules/published! row)
               (reply 201 {:comment (articles/add-comment! source (:id row) id
                                                           (:body (item request :comment [:body])))})))}]
   ["/api/articles/:slug/comments/:id"
    {:delete (fn [request]
               (let [id (required-id request)
                     row (articles/visible! source (path request :slug) id)]
                 (articles/delete-comment! source (:id row) (path request :id) id)
                 no-content))}]
   ["/api/articles/:slug/share"
    {:post (fn [request]
             (let [id (required-id request)
                   row (articles/authored! source (path request :slug) id)]
               (reply 201 {:share (shares/rotate! source (:id row))})))
     :delete (fn [request]
               (let [id (required-id request)
                     row (articles/authored! source (path request :slug) id)]
                 (shares/revoke! source (:id row)) no-content))}]
   ["/api/shares/:id/article"
    {:get (fn [request]
            (let [share (:share request)]
              (reply {:article (shares/read-article source share)})))
     :put (fn [request]
            (let [share (:share request)]
              (reply {:article (shares/edit! source share (share-item request))})))}]
   ["/api/shares/:id/live"
    {:get (fn [request]
            {:status 101 :ring.websocket/listener (shares/listener source (path request :id))})}]])

(defn auth-required? [request]
  (let [uri (:uri request) method (:request-method request)]
    (or (= uri "/api/user")
        (str/starts-with? uri "/api/user/")
        (and (re-matches #"/api/profiles/[^/]+/follow" uri) (#{:post :delete} method))
        (and (= uri "/api/articles") (= method :post))
        (= uri "/api/articles/feed")
        (and (str/starts-with? uri "/api/articles/") (not= method :get)))))

(defn wrap-auth [handler source secret]
  (fn [request]
    (let [viewer (users/authenticate source secret request)
          _ (when (and (auth-required? request) (nil? viewer))
              (rules/fail 401 :token "is missing"))
          share-id (second (re-matches #"/api/shares/([^/]+)/article" (:uri request)))
          share (when share-id
                  (shares/authorized! source share-id (get-in request [:headers "x-share-key"])))
          length (try (Long/parseLong (get-in request [:headers "content-length"] "0"))
                      (catch Exception _ 0))]
      (when (> length 1048576) (rules/fail 413 :body "is too large"))
      (handler (cond-> (assoc request :viewer viewer) share (assoc :share share))))))

(defn wrap-boundary [handler]
  (fn [request]
    (let [cors {"Access-Control-Allow-Origin" "*"
                "Access-Control-Allow-Headers" "Authorization, Content-Type, X-Share-Key"
                "Access-Control-Allow-Methods" "GET, POST, PUT, DELETE, OPTIONS"
                "X-Content-Type-Options" "nosniff"}]
      (if (= :options (:request-method request))
        {:status 204 :headers cors :body ""}
        (let [response (try
                         (handler request)
                         (catch clojure.lang.ExceptionInfo e
                           (let [{:keys [status errors article]} (ex-data e)]
                             {:status (or status 400)
                              :headers {"Content-Type" "application/json; charset=utf-8"}
                              :body (json/write-str (cond-> {:errors (or errors {"body" ["is invalid"]})}
                                                      article (assoc :article article)))}))
                         (catch Exception e
                           (println "Request failed:" (.getMessage e))
                           {:status 500 :headers {"Content-Type" "application/json; charset=utf-8"}
                            :body (json/write-str {:errors {:body ["internal error"]}})}))]
          (update response :headers merge cors))))))

(defn handler
  ([source] (handler source "test-secret"))
  ([source secret]
   (wrap-boundary
    (wrap-auth
     (ring/ring-handler
      (ring/router
       (routes source secret)
       {:conflicts nil :data {:muuntaja muuntaja/instance
                              :coercion malli/coercion
                              :middleware [parameters/parameters-middleware
                                           format/format-negotiate-middleware
                                           format/format-response-middleware
                                           format/format-request-middleware
                                           coercion/coerce-request-middleware
                                           coercion/coerce-response-middleware]}})
      (ring/create-default-handler)) source secret))))
