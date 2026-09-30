(ns conduit.articles
  (:require [clojure.string :as str]
            [conduit.db :as db]
            [conduit.rules :as rules]
            [next.jdbc :as jdbc])
  (:import [java.time Instant OffsetDateTime]
           [java.sql Timestamp]
           [java.util UUID]))

(defn instant-text [value]
  (when value
    (str (cond
           (instance? Timestamp value) (.toInstant ^Timestamp value)
           (instance? OffsetDateTime value) (.toInstant ^OffsetDateTime value)
           (instance? Instant value) value
           :else value))))

(defn article-row [source id viewer-id]
  (db/one source
          (str "SELECT a.*,u.username author_username,u.bio author_bio,u.image author_image,"
               "(SELECT count(*) FROM favorites f WHERE f.article_id=a.id) favorites_count,"
               "EXISTS(SELECT 1 FROM favorites f WHERE f.article_id=a.id AND f.user_id=?) favorited,"
               "EXISTS(SELECT 1 FROM follows f WHERE f.followed_id=a.author_id AND f.follower_id=?) following "
               "FROM articles a JOIN users u ON u.id=a.author_id WHERE a.id=?")
          (or viewer-id -1) (or viewer-id -1) id))

(defn by-slug [source slug viewer-id]
  (when-let [id (:id (db/one source "SELECT id FROM articles WHERE slug=?" slug))]
    (article-row source id viewer-id)))

(defn tags-for [source ids]
  (if (empty? ids) {}
      (let [marks (str/join "," (repeat (count ids) "?"))]
        (group-by :article_id
                  (apply db/all source
                         (str "SELECT article_id,tag FROM article_tags WHERE article_id IN (" marks ") ORDER BY article_id,position") ids)))))

(defn attach-tags [source rows]
  (let [tags (tags-for source (mapv :id rows))]
    (mapv #(assoc % :tag_list (mapv :tag (get tags (:id %)))) rows)))

(defn projection [row include-body?]
  (cond-> {:slug (:slug row) :title (:title row) :description (:description row)
           :tagList (or (:tag_list row) []) :createdAt (instant-text (:created_at row))
           :updatedAt (instant-text (:updated_at row))
           :favorited (boolean (:favorited row)) :favoritesCount (:favorites_count row)
           :author {:username (:author_username row) :bio (:author_bio row)
                    :image (:author_image row) :following (boolean (:following row))}
           :status (:status row) :publishedAt (instant-text (:published_at row))
           :revision (:revision row)}
    include-body? (assoc :body (:body row))))

(defn full [source id viewer-id]
  (some->> (article-row source id viewer-id) vector (attach-tags source) first (#(projection % true))))

(defn shared [row]
  (select-keys row [:slug :title :body :revision]))

(defn validation! [input fields]
  (doseq [field fields :when (contains? input field)]
    (rules/nonblank! field (get input field)))
  (when (contains? input :tagList)
    (when-not (and (vector? (:tagList input))
                   (every? #(and (string? %) (not (str/blank? %))) (:tagList input)))
      (rules/fail 422 :tagList "is invalid")))
  input)

(defn replace-tags! [tx article-id tags]
  (db/run tx "DELETE FROM article_tags WHERE article_id=?" article-id)
  (doseq [[position tag] (map-indexed vector (distinct tags))]
    (db/run tx "INSERT INTO article_tags(article_id,tag,position) VALUES (?,?,?)"
            article-id tag position)))

(defn create! [source author-id input]
  (doseq [field [:title :description :body]]
    (rules/nonblank! field (get input field)))
  (validation! input [:title :description :body])
  (let [status (get input :status "published")]
    (when-not (contains? #{"draft" "published"} status)
      (rules/fail 422 :status "is invalid"))
    (jdbc/with-transaction [tx source]
      (let [article (db/one tx
                            "INSERT INTO articles(author_id,slug,title,description,body,status,published_at) VALUES (?,?,?,?,?,?,CASE WHEN ?='published' THEN now() ELSE NULL END) RETURNING id"
                            author-id (str (UUID/randomUUID)) (:title input) (:description input)
                            (:body input) status status)
            id (:id article)
            slug (str (rules/slug-base (:title input)) "-" id)]
        (db/run tx "UPDATE articles SET slug=? WHERE id=?" slug id)
        (replace-tags! tx id (or (:tagList input) []))
        (full tx id author-id)))))

(defn visible! [source slug viewer-id]
  (rules/visible-article! (by-slug source slug viewer-id) viewer-id))

(defn authored! [source slug viewer-id]
  (rules/author! (visible! source slug viewer-id) viewer-id))

(defn edit-locked! [tx locked viewer-id input required-revision?]
  (let [article-id (:id locked)
        current (full tx article-id viewer-id)]
    (when (and (contains? input :revision) (nil? (:revision input)))
      (rules/fail 422 :revision "is invalid"))
    (when (and required-revision? (not (contains? input :revision)))
      (rules/fail 422 :revision "is invalid"))
    (rules/revision! (:revision input) (:revision locked) current)
    (validation! input [:title :description :body])
    (let [title (get input :title (:title locked))
          slug (if (not= title (:title locked))
                 (str (rules/slug-base title) "-" article-id)
                 (:slug locked))]
      (db/run tx "UPDATE articles SET title=?,slug=?,description=?,body=?,revision=revision+1,updated_at=GREATEST(clock_timestamp(),updated_at + interval '1 microsecond') WHERE id=?"
              title slug (get input :description (:description locked))
              (get input :body (:body locked)) article-id)
      (when (contains? input :tagList) (replace-tags! tx article-id (:tagList input)))
      (full tx article-id viewer-id))))

(defn edit! [source article-id viewer-id input required-revision?]
  (jdbc/with-transaction [tx source]
    (let [locked (db/one tx "SELECT * FROM articles WHERE id=? FOR UPDATE" article-id)]
      (when-not locked (rules/fail 404 :article "not found"))
      (edit-locked! tx locked viewer-id input required-revision?))))

(defn publish! [source id viewer-id]
  (jdbc/with-transaction [tx source]
    (let [row (db/one tx "SELECT * FROM articles WHERE id=? FOR UPDATE" id)]
      (when (= "draft" (:status row))
        (db/run tx "UPDATE articles SET status='published',published_at=clock_timestamp(),revision=revision+1,updated_at=clock_timestamp() WHERE id=?" id))
      (full tx id viewer-id))))

(defn delete! [source id]
  (db/run source "DELETE FROM articles WHERE id=?" id))

(defn page-params [params]
  (let [parse (fn [k default]
                (if-let [raw (get params k)]
                  (try (Long/parseLong raw) (catch Exception _ (rules/fail 422 k "is invalid")))
                  default))
        limit (parse :limit 20) offset (parse :offset 0)]
    (when (or (neg? limit) (neg? offset) (> limit 100) (> offset 100000000))
      (rules/fail 422 :pagination "is invalid"))
    [limit offset]))

(defn list! [source viewer-id params mode]
  (let [[limit offset] (page-params params)
        clauses (cond-> [(if (= mode :drafts) "a.status='draft'" "a.status='published'")]
                  (= mode :drafts) (conj "a.author_id=?")
                  (= mode :feed) (conj "EXISTS(SELECT 1 FROM follows f WHERE f.followed_id=a.author_id AND f.follower_id=?)")
                  (:tag params) (conj "EXISTS(SELECT 1 FROM article_tags t WHERE t.article_id=a.id AND t.tag=?)")
                  (:author params) (conj "u.username=?")
                  (:favorited params) (conj "EXISTS(SELECT 1 FROM favorites fv JOIN users fu ON fu.id=fv.user_id WHERE fv.article_id=a.id AND fu.username=?)"))
        values (cond-> []
                 (= mode :drafts) (conj viewer-id)
                 (= mode :feed) (conj viewer-id)
                 (:tag params) (conj (:tag params))
                 (:author params) (conj (:author params))
                 (:favorited params) (conj (:favorited params)))
        from (str " FROM articles a JOIN users u ON u.id=a.author_id WHERE " (str/join " AND " clauses))
        total (:count (first (apply db/all source (str "SELECT count(*) count" from) values)))
        rows (apply db/all source
                    (str "SELECT a.*,u.username author_username,u.bio author_bio,u.image author_image,"
                         "(SELECT count(*) FROM favorites f WHERE f.article_id=a.id) favorites_count,"
                         "EXISTS(SELECT 1 FROM favorites f WHERE f.article_id=a.id AND f.user_id=?) favorited,"
                         "EXISTS(SELECT 1 FROM follows f WHERE f.followed_id=a.author_id AND f.follower_id=?) following"
                         from " ORDER BY a.created_at DESC,a.id DESC LIMIT ? OFFSET ?")
                    (concat [(or viewer-id -1) (or viewer-id -1)] values [limit offset]))]
    {:articles (mapv #(projection % false) (attach-tags source rows)) :articlesCount total}))

(defn tags [source]
  (mapv :tag (db/all source "SELECT DISTINCT t.tag FROM article_tags t JOIN articles a ON a.id=t.article_id WHERE a.status='published' ORDER BY t.tag")))

(defn favorite! [source article-id viewer-id favorite?]
  (if favorite?
    (db/run source "INSERT INTO favorites(user_id,article_id) VALUES (?,?) ON CONFLICT DO NOTHING" viewer-id article-id)
    (db/run source "DELETE FROM favorites WHERE user_id=? AND article_id=?" viewer-id article-id))
  (full source article-id viewer-id))

(defn comment-row [source id viewer-id]
  (db/one source
          (str "SELECT c.*,u.username author_username,u.bio author_bio,u.image author_image,"
               "EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=? AND f.followed_id=c.author_id) following "
               "FROM comments c JOIN users u ON u.id=c.author_id WHERE c.id=?")
          (or viewer-id -1) id))

(defn comment-projection [row]
  {:id (:id row) :body (:body row) :createdAt (instant-text (:created_at row))
   :updatedAt (instant-text (:updated_at row))
   :author {:username (:author_username row) :bio (:author_bio row)
            :image (:author_image row) :following (boolean (:following row))}})

(defn comments [source article-id viewer-id]
  (mapv comment-projection
        (db/all source
                (str "SELECT c.*,u.username author_username,u.bio author_bio,u.image author_image,"
                     "EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=? AND f.followed_id=c.author_id) following "
                     "FROM comments c JOIN users u ON u.id=c.author_id WHERE c.article_id=? ORDER BY c.created_at,c.id")
                (or viewer-id -1) article-id)))

(defn add-comment! [source article-id author-id body]
  (rules/nonblank! :body body)
  (let [id (:id (db/one source "INSERT INTO comments(article_id,author_id,body) VALUES (?,?,?) RETURNING id"
                        article-id author-id body))]
    (comment-projection (comment-row source id author-id))))

(defn delete-comment! [source article-id comment-id viewer-id]
  (let [row (try (db/one source "SELECT * FROM comments WHERE id=? AND article_id=?"
                         (Long/parseLong comment-id) article-id)
                 (catch NumberFormatException _ nil))]
    (when-not row (rules/fail 404 :comment "not found"))
    (when (not= viewer-id (:author_id row)) (rules/fail 403 :comment "forbidden"))
    (db/run source "DELETE FROM comments WHERE id=?" (:id row))))
