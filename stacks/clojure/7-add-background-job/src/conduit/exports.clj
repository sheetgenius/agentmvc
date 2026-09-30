(ns conduit.exports
  (:require [conduit.domain :as domain]
            [conduit.store :as store]
            [muuntaja.core :as muuntaja]
            [next.jdbc :as jdbc]
            [proletarian.job :as job]))

(defn- present [export]
  {:id (:id export)
   :status (if (:completed_at export) "done" "pending")
   :createdAt (store/iso (:created_at export))
   :completedAt (some-> (:completed_at export) store/iso)
   :articles (when-let [articles (:articles export)]
               (muuntaja/decode muuntaja/instance "application/json" (str articles)))})

(defn request! [db user]
  (jdbc/with-transaction [tx db]
    (let [export (store/one tx "INSERT INTO article_exports (user_id) VALUES (?) RETURNING *" (:id user))]
      (job/enqueue! tx ::build (:id export))
      (present export))))

(defn find-export [db user id]
  (present (domain/found
            (store/one db "SELECT * FROM article_exports WHERE id = ? AND user_id = ?"
                       (parse-long id) (:id user))
            :export)))

(defn- snapshot [rows]
  (mapv (fn [group]
          (let [article (first group)]
            {:slug (:slug article)
             :title (:title article)
             :description (:description article)
             :body (:body article)
             :tagList (mapv :tag (filter :tag group))
             :status (:status article)
             :commentsCount (:comments_count article)}))
        (partition-by :id rows)))

(defn build! [db export-id]
  (when-let [export (store/one db "SELECT user_id FROM article_exports WHERE id = ? AND completed_at IS NULL" export-id)]
    (let [rows (store/all db
                          (str "SELECT a.id, a.slug, a.title, a.description, a.body, a.status, "
                               "t.tag, (SELECT count(*) FROM comments c WHERE c.article_id = a.id) AS comments_count "
                               "FROM articles a LEFT JOIN article_tags t ON t.article_id = a.id "
                               "WHERE a.author_id = ? ORDER BY a.created_at, a.id, t.position")
                          (:user_id export))
          articles (slurp (muuntaja/encode muuntaja/instance "application/json" (snapshot rows)))]
      (store/execute! db "UPDATE article_exports SET articles = ?::jsonb, completed_at = now() WHERE id = ? AND completed_at IS NULL"
                      articles export-id))))
