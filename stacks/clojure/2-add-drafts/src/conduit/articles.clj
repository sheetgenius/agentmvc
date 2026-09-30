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

(defn find-article [db viewer slug]
  (domain/found (store/one db "SELECT * FROM articles WHERE slug = ? AND (status = 'published' OR author_id = ?)"
                           slug (:id viewer)) :article))

(defn- tags [db id]
  (mapv :tag (store/all db "SELECT tag FROM article_tags WHERE article_id = ? ORDER BY position" id)))

(defn- author [db viewer user-id]
  (users/profile db viewer (users/user-by-id db user-id)))

(defn present [db viewer article include-body?]
  (cond-> {:slug (:slug article) :title (:title article)
           :description (:description article) :tagList (tags db (:id article))
           :createdAt (iso (:created_at article)) :updatedAt (iso (:updated_at article))
           :status (:status article) :publishedAt (some-> (:published_at article) iso)
           :revision (:revision article)
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
  (let [tag-list (valid-tags (get input :tagList []))
        status (get input :status "published")]
    (when-not (#{"draft" "published"} status)
      (domain/fail 422 :status "is invalid"))
    (jdbc/with-transaction [tx db]
      (let [article (store/one tx "INSERT INTO articles (slug, title, description, body, author_id, status, published_at) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *"
                               (slug (:title input)) (:title input) (:description input) (:body input)
                               (:id viewer) status (when (= status "published") (OffsetDateTime/now)))]
        (replace-tags! tx (:id article) tag-list)
        (present tx viewer article true)))))

(defn- stale! [db viewer article]
  (throw (ex-info "is stale" {:status 409 :errors {:revision ["is stale"]}
                              :article (present db viewer article true)})))

(defn update! [db viewer old-slug input]
  (jdbc/with-transaction [tx db]
    (let [article (find-article tx viewer old-slug)]
      (domain/owned (:author_id article) (:id viewer) :article)
      (when (contains? input :revision)
        (when-not (integer? (:revision input))
          (domain/fail 422 :revision "is invalid"))
        (when (not= (:revision input) (:revision article))
          (stale! tx viewer article)))
      (when (contains? input :tagList)
        (valid-tags (:tagList input)))
      (doseq [field [:title :description :body]]
        (when (contains? input field) (domain/required input [field])))
      (let [changes (cond-> (select-keys input [:title :description :body])
                      (contains? input :title) (assoc :slug (slug (:title input))))
            updated (store/statement-one tx (sql/format {:update :articles
                                                         :set (assoc changes :updated_at (OffsetDateTime/now)
                                                                     :revision (inc (:revision article)))
                                                         :where [:and [:= :id (:id article)]
                                                                 [:= :revision (:revision article)]]
                                                         :returning :*}))]
        (when-not updated
          (if-let [current (store/one tx "SELECT * FROM articles WHERE id = ?" (:id article))]
            (stale! tx viewer current)
            (domain/fail 404 :article "not found")))
        (when (contains? input :tagList)
          (replace-tags! tx (:id article) (:tagList input)))
        (present tx viewer updated true)))))

(defn publish! [db viewer slug]
  (jdbc/with-transaction [tx db]
    (let [article (find-article tx viewer slug)]
      (domain/owned (:author_id article) (:id viewer) :article)
      (present tx viewer
               (if (= "draft" (:status article))
                 (or (store/one tx "UPDATE articles SET status = 'published', published_at = now(), revision = revision + 1 WHERE id = ? AND status = 'draft' RETURNING *"
                                (:id article))
                     (domain/found (store/one tx "SELECT * FROM articles WHERE id = ?" (:id article)) :article))
                 article)
               true))))

(defn delete! [db viewer slug]
  (let [article (find-article db viewer slug)]
    (domain/owned (:author_id article) (:id viewer) :article)
    (store/execute! db "DELETE FROM articles WHERE id = ?" (:id article))))

(defn- published-article [db viewer slug]
  (let [article (find-article db viewer slug)]
    (when (= "draft" (:status article))
      (domain/fail 422 :article "is a draft"))
    article))

(defn favorite! [db viewer slug favorite?]
  (let [article (published-article db viewer slug)]
    (if favorite?
      (store/execute! db "INSERT INTO favorites (user_id, article_id) VALUES (?, ?) ON CONFLICT DO NOTHING"
                      (:id viewer) (:id article))
      (store/execute! db "DELETE FROM favorites WHERE user_id = ? AND article_id = ?"
                      (:id viewer) (:id article)))
    (present db viewer article true)))

(defn- page-size [value default]
  (try (max 0 (Integer/parseInt (or value default)))
       (catch Exception _ (Integer/parseInt default))))

(defn- article-page [db viewer query filters]
  (let [where (str " WHERE " (str/join " AND " (map first filters)))
        args (mapv second filters)
        count-row (store/statement-one db (into [(str "SELECT count(*) AS count FROM articles a" where)] args))
        rows (apply store/all db (str "SELECT a.* FROM articles a" where " ORDER BY a.created_at DESC, a.id DESC LIMIT ? OFFSET ?")
                    (concat args [(page-size (:limit query) "20") (page-size (:offset query) "0")]))]
    {:articles (mapv #(present db viewer % false) rows)
     :articlesCount (:count count-row)}))

(defn listing [db viewer query feed?]
  (let [query (walk/keywordize-keys query)
        filters (cond-> [["a.status = ?" "published"]]
                  feed? (conj ["EXISTS (SELECT 1 FROM follows f WHERE f.followed_id = a.author_id AND f.follower_id = ?)" (:id viewer)])
                  (:author query) (conj ["EXISTS (SELECT 1 FROM users u WHERE u.id = a.author_id AND u.username = ?)" (:author query)])
                  (:tag query) (conj ["EXISTS (SELECT 1 FROM article_tags t WHERE t.article_id = a.id AND t.tag = ?)" (:tag query)])
                  (:favorited query) (conj ["EXISTS (SELECT 1 FROM favorites f JOIN users u ON u.id = f.user_id WHERE f.article_id = a.id AND u.username = ?)" (:favorited query)]))]
    (article-page db viewer query filters)))

(defn drafts [db viewer query]
  (article-page db viewer (walk/keywordize-keys query)
                [["a.status = ?" "draft"] ["a.author_id = ?" (:id viewer)]]))

(defn all-tags [db]
  (mapv :tag (store/all db "SELECT DISTINCT t.tag FROM article_tags t JOIN articles a ON a.id = t.article_id WHERE a.status = 'published' ORDER BY t.tag")))

(defn- present-comment [db viewer comment]
  {:id (:id comment) :body (:body comment)
   :createdAt (iso (:created_at comment)) :updatedAt (iso (:updated_at comment))
   :author (author db viewer (:author_id comment))})

(defn comments [db viewer slug]
  (let [article (find-article db viewer slug)]
    (mapv #(present-comment db viewer %)
          (store/all db "SELECT * FROM comments WHERE article_id = ? ORDER BY id" (:id article)))))

(defn add-comment! [db viewer slug input]
  (let [article (published-article db viewer slug)]
    (domain/required input [:body])
    (present-comment db viewer
                     (store/one db "INSERT INTO comments (article_id, author_id, body) VALUES (?, ?, ?) RETURNING *"
                                (:id article) (:id viewer) (:body input)))))

(defn delete-comment! [db viewer slug id]
  (let [article (find-article db viewer slug)
        comment (domain/found (store/one db "SELECT * FROM comments WHERE article_id = ? AND id = ?"
                                         (:id article) (Long/parseLong id)) :comment)]
    (domain/owned (:author_id comment) (:id viewer) :comment)
    (store/execute! db "DELETE FROM comments WHERE id = ?" (:id comment))))
