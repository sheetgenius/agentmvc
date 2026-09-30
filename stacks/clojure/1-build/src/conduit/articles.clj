(ns conduit.articles
  (:require [clojure.string :as str]
            [clojure.walk :as walk]
            [conduit.domain :as domain]
            [conduit.store :as store]
            [conduit.users :as users]
            [honey.sql :as sql]
            [next.jdbc :as jdbc])
  (:import [java.time Instant OffsetDateTime]
           [java.util UUID]))

(defn- iso [value]
  (str (cond
         (instance? OffsetDateTime value) (.toInstant ^OffsetDateTime value)
         (instance? java.sql.Timestamp value) (.toInstant ^java.sql.Timestamp value)
         (instance? Instant value) value
         :else value)))

(defn- slug [title]
  (str (str/replace (str/lower-case title) #"[^a-z0-9]+" "-")
       "-" (subs (str (UUID/randomUUID)) 0 8)))

(defn find-article [db slug]
  (domain/found (store/one db "SELECT * FROM articles WHERE slug = ?" slug) :article))

(defn- tags [db id]
  (mapv :tag (store/all db "SELECT tag FROM article_tags WHERE article_id = ? ORDER BY position" id)))

(defn- author [db viewer user-id]
  (users/profile db viewer (users/user-by-id db user-id)))

(defn present [db viewer article include-body?]
  (cond-> {:slug (:slug article) :title (:title article)
           :description (:description article) :tagList (tags db (:id article))
           :createdAt (iso (:created_at article)) :updatedAt (iso (:updated_at article))
           :favorited (boolean (and viewer
                                    (store/one db "SELECT 1 FROM favorites WHERE user_id = ? AND article_id = ?"
                                               (:id viewer) (:id article))))
           :favoritesCount (:count (store/one db "SELECT count(*) AS count FROM favorites WHERE article_id = ?"
                                              (:id article)))
           :author (author db viewer (:author_id article))}
    include-body? (assoc :body (:body article))))

(defn- replace-tags! [db article-id tag-list]
  (store/execute! db "DELETE FROM article_tags WHERE article_id = ?" article-id)
  (doseq [[position tag] (map-indexed vector (distinct tag-list))]
    (store/execute! db "INSERT INTO article_tags (article_id, tag, position) VALUES (?, ?, ?)"
                    article-id tag position)))

(defn- valid-tags [tag-list]
  (when-not (and (sequential? tag-list) (every? string? tag-list))
    (domain/fail 422 :tagList "is invalid"))
  tag-list)

(defn create! [db viewer input]
  (domain/required input [:title :description :body])
  (let [tag-list (valid-tags (get input :tagList []))]
    (jdbc/with-transaction [tx db]
      (let [article (store/one tx "INSERT INTO articles (slug, title, description, body, author_id) VALUES (?, ?, ?, ?, ?) RETURNING *"
                               (slug (:title input)) (:title input) (:description input) (:body input) (:id viewer))]
        (replace-tags! tx (:id article) tag-list)
        (present tx viewer article true)))))

(defn update! [db viewer old-slug input]
  (jdbc/with-transaction [tx db]
    (let [article (find-article tx old-slug)]
      (domain/owned (:author_id article) (:id viewer) :article)
      (when (contains? input :tagList)
        (valid-tags (:tagList input)))
      (doseq [field [:title :description :body]]
        (when (contains? input field) (domain/required input [field])))
      (let [changes (cond-> (select-keys input [:title :description :body])
                      (contains? input :title) (assoc :slug (slug (:title input))))
            updated (if (or (seq changes) (contains? input :tagList))
                      (store/statement-one tx (sql/format {:update :articles
                                                           :set (assoc changes :updated_at (OffsetDateTime/now))
                                                           :where [:= :id (:id article)]
                                                           :returning :*}))
                      article)]
        (when (contains? input :tagList)
          (replace-tags! tx (:id article) (:tagList input)))
        (present tx viewer updated true)))))

(defn delete! [db viewer slug]
  (let [article (find-article db slug)]
    (domain/owned (:author_id article) (:id viewer) :article)
    (store/execute! db "DELETE FROM articles WHERE id = ?" (:id article))))

(defn favorite! [db viewer slug favorite?]
  (let [article (find-article db slug)]
    (if favorite?
      (store/execute! db "INSERT INTO favorites (user_id, article_id) VALUES (?, ?) ON CONFLICT DO NOTHING"
                      (:id viewer) (:id article))
      (store/execute! db "DELETE FROM favorites WHERE user_id = ? AND article_id = ?"
                      (:id viewer) (:id article)))
    (present db viewer article true)))

(defn- page-size [value default]
  (try (max 0 (Integer/parseInt (or value default)))
       (catch Exception _ (Integer/parseInt default))))

(defn listing [db viewer query feed?]
  (let [query (walk/keywordize-keys query)
        filters (cond-> []
                  feed? (conj ["EXISTS (SELECT 1 FROM follows f WHERE f.followed_id = a.author_id AND f.follower_id = ?)" (:id viewer)])
                  (:author query) (conj ["EXISTS (SELECT 1 FROM users u WHERE u.id = a.author_id AND u.username = ?)" (:author query)])
                  (:tag query) (conj ["EXISTS (SELECT 1 FROM article_tags t WHERE t.article_id = a.id AND t.tag = ?)" (:tag query)])
                  (:favorited query) (conj ["EXISTS (SELECT 1 FROM favorites f JOIN users u ON u.id = f.user_id WHERE f.article_id = a.id AND u.username = ?)" (:favorited query)]))
        where (if (seq filters) (str " WHERE " (str/join " AND " (map first filters))) "")
        args (mapv second filters)
        count-row (store/statement-one db (into [(str "SELECT count(*) AS count FROM articles a" where)] args))
        rows (apply store/all db (str "SELECT a.* FROM articles a" where " ORDER BY a.created_at DESC, a.id DESC LIMIT ? OFFSET ?")
                    (concat args [(page-size (:limit query) "20") (page-size (:offset query) "0")]))]
    {:articles (mapv #(present db viewer % false) rows)
     :articlesCount (:count count-row)}))

(defn all-tags [db]
  (mapv :tag (store/all db "SELECT DISTINCT tag FROM article_tags ORDER BY tag")))

(defn- present-comment [db viewer comment]
  {:id (:id comment) :body (:body comment)
   :createdAt (iso (:created_at comment)) :updatedAt (iso (:updated_at comment))
   :author (author db viewer (:author_id comment))})

(defn comments [db viewer slug]
  (let [article (find-article db slug)]
    (mapv #(present-comment db viewer %)
          (store/all db "SELECT * FROM comments WHERE article_id = ? ORDER BY id" (:id article)))))

(defn add-comment! [db viewer slug input]
  (domain/required input [:body])
  (let [article (find-article db slug)
        comment (store/one db "INSERT INTO comments (article_id, author_id, body) VALUES (?, ?, ?) RETURNING *"
                           (:id article) (:id viewer) (:body input))]
    (present-comment db viewer comment)))

(defn delete-comment! [db viewer slug id]
  (let [article (find-article db slug)
        comment (domain/found (store/one db "SELECT * FROM comments WHERE article_id = ? AND id = ?"
                                         (:id article) (Long/parseLong id)) :comment)]
    (domain/owned (:author_id comment) (:id viewer) :comment)
    (store/execute! db "DELETE FROM comments WHERE id = ?" (:id comment))))
