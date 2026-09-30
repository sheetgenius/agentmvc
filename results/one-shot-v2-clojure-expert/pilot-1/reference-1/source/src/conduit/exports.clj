(ns conduit.exports
  (:require [clojure.data.json :as json]
            [conduit.articles :as articles]
            [conduit.db :as db]
            [conduit.rules :as rules]
            [next.jdbc :as jdbc]
            [proletarian.job :as job])
  (:import [java.util UUID]))

(defn public [row]
  {:id (str (:id row)) :status (:status row)
   :createdAt (articles/instant-text (:created_at row))
   :completedAt (articles/instant-text (:completed_at row))
   :articles (when-let [value (:articles row)]
               (json/read-str (.getValue value)))})

(defn request! [source user-id]
  (jdbc/with-transaction [tx source]
    (let [id (UUID/randomUUID)
          row (db/one tx "INSERT INTO exports(id,user_id) VALUES (?,?) RETURNING *" id user-id)]
      (job/enqueue! tx :conduit/export {:id (str id) :user-id user-id})
      (public row))))

(defn find! [source user-id id]
  (let [uuid (try (UUID/fromString id) (catch Exception _ nil))
        row (when uuid (db/one source "SELECT * FROM exports WHERE id=? AND user_id=?" uuid user-id))]
    (when-not row (rules/fail 404 :export "not found"))
    (public row)))

(defn snapshot! [source {:keys [id user-id]}]
  (jdbc/with-transaction [tx source {:isolation :repeatable-read}]
    (when-let [pending (db/one tx "SELECT id FROM exports WHERE id=? AND status='pending' FOR UPDATE" (UUID/fromString id))]
      (let [rows (db/all tx
                         (str "SELECT a.id,a.slug,a.title,a.description,a.body,a.status,"
                              "(SELECT count(*) FROM comments c WHERE c.article_id=a.id) comments_count "
                              "FROM articles a WHERE a.author_id=? ORDER BY a.created_at,a.id")
                         user-id)
            tags (articles/tags-for tx (mapv :id rows))
            items (mapv (fn [row]
                          {:slug (:slug row) :title (:title row) :description (:description row)
                           :body (:body row) :status (:status row) :commentsCount (:comments_count row)
                           :tagList (mapv :tag (get tags (:id row)))}) rows)]
        (db/run tx "UPDATE exports SET status='done',completed_at=clock_timestamp(),articles=?::jsonb WHERE id=?"
                (json/write-str items) (:id pending))))))
