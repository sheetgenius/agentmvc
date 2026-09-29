package conduit

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
	"unicode"

	"github.com/go-chi/chi/v5"
)

type articleRecord struct {
	ID, AuthorID                           int64
	Slug, Title, Description, Body, Status string
	Revision                               int
	CreatedAt, UpdatedAt                   time.Time
	PublishedAt                            sql.NullTime
}

func scanRecord(row *sql.Row) (articleRecord, error) {
	var x articleRecord
	err := row.Scan(&x.ID, &x.AuthorID, &x.Slug, &x.Title, &x.Description, &x.Body, &x.Status, &x.Revision, &x.CreatedAt, &x.UpdatedAt, &x.PublishedAt)
	return x, err
}

const recordColumns = "id,author_id,slug,title,description,body,status,revision,created_at,updated_at,published_at"

func (a *App) recordBySlug(ctx context.Context, slug string, viewer int64) (articleRecord, error) {
	x, err := scanRecord(a.DB.DB.QueryRowContext(ctx, "SELECT "+recordColumns+" FROM articles WHERE slug=$1 AND (status='published' OR author_id=$2)", slug, viewer))
	if errors.Is(err, sql.ErrNoRows) {
		return x, fail(404, "article", "not found")
	}
	return x, err
}
func (a *App) recordByID(ctx context.Context, id int64) (articleRecord, error) {
	return scanRecord(a.DB.DB.QueryRowContext(ctx, "SELECT "+recordColumns+" FROM articles WHERE id=$1", id))
}
func own(x articleRecord, viewer int64) error {
	if x.AuthorID != viewer {
		return fail(403, "article", "forbidden")
	}
	return nil
}
func published(x articleRecord) error {
	if x.Status == "draft" {
		return fail(422, "article", "is a draft")
	}
	return nil
}
func slugify(title string) string {
	var b strings.Builder
	dash := false
	for _, r := range strings.ToLower(title) {
		if unicode.IsLetter(r) || unicode.IsDigit(r) {
			if r < 128 {
				b.WriteRune(r)
				dash = false
			}
		} else if !dash && b.Len() > 0 {
			b.WriteByte('-')
			dash = true
		}
	}
	return strings.Trim(b.String(), "-") + "-" + randomURL(6)
}

type ArticleView struct {
	Slug           string      `json:"slug"`
	Title          string      `json:"title"`
	Description    string      `json:"description"`
	Body           string      `json:"body,omitempty"`
	TagList        []string    `json:"tagList"`
	CreatedAt      time.Time   `json:"createdAt"`
	UpdatedAt      time.Time   `json:"updatedAt"`
	Favorited      bool        `json:"favorited"`
	FavoritesCount int         `json:"favoritesCount"`
	Author         profileView `json:"author"`
	Status         string      `json:"status"`
	PublishedAt    *time.Time  `json:"publishedAt"`
	Revision       int         `json:"revision"`
}
type rowScanner interface{ Scan(...any) error }

const viewSelect = `SELECT a.slug,a.title,a.description,a.body,a.created_at,a.updated_at,a.status,a.published_at,a.revision,
 u.username,u.bio,u.image,
 EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=$1 AND f.followed_id=u.id),
 EXISTS(SELECT 1 FROM favorites f WHERE f.user_id=$1 AND f.article_id=a.id),
 (SELECT count(*) FROM favorites f WHERE f.article_id=a.id),
 COALESCE((SELECT json_agg(t.tag ORDER BY t.tag) FROM article_tags t WHERE t.article_id=a.id),'[]'::json)::text
 FROM articles a JOIN users u ON u.id=a.author_id`

func scanView(row rowScanner, body bool) (ArticleView, error) {
	var v ArticleView
	var bio, image sql.NullString
	var pub sql.NullTime
	var tags string
	err := row.Scan(&v.Slug, &v.Title, &v.Description, &v.Body, &v.CreatedAt, &v.UpdatedAt, &v.Status, &pub, &v.Revision, &v.Author.Username, &bio, &image, &v.Author.Following, &v.Favorited, &v.FavoritesCount, &tags)
	if err != nil {
		return v, err
	}
	v.Author.Bio = nullable(bio)
	v.Author.Image = nullable(image)
	if pub.Valid {
		v.PublishedAt = &pub.Time
	}
	_ = json.Unmarshal([]byte(tags), &v.TagList)
	if v.TagList == nil {
		v.TagList = []string{}
	}
	if !body {
		v.Body = ""
	}
	return v, nil
}
func (a *App) viewArticle(ctx context.Context, id, viewer int64, body bool) (ArticleView, error) {
	return scanView(a.DB.DB.QueryRowContext(ctx, viewSelect+" WHERE a.id=$2", viewer, id), body)
}
func tagsField(obj map[string]json.RawMessage) ([]string, bool, error) {
	raw, ok := obj["tagList"]
	if !ok {
		return nil, false, nil
	}
	if string(raw) == "null" {
		return nil, true, fail(422, "tagList", "is invalid")
	}
	var tags []string
	if err := json.Unmarshal(raw, &tags); err != nil {
		return nil, true, fail(422, "tagList", "is invalid")
	}
	return tags, true, nil
}

type sqlExecer interface {
	ExecContext(context.Context, string, ...any) (sql.Result, error)
}

func (a *App) replaceTags(ctx context.Context, tx sqlExecer, id int64, tags []string) error {
	if _, err := tx.ExecContext(ctx, "DELETE FROM article_tags WHERE article_id=$1", id); err != nil {
		return err
	}
	for _, tag := range tags {
		if tag == "" {
			continue
		}
		if _, err := tx.ExecContext(ctx, "INSERT INTO article_tags(article_id,tag) VALUES($1,$2) ON CONFLICT DO NOTHING", id, tag); err != nil {
			return err
		}
	}
	return nil
}
func (a *App) createArticle(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	obj, err := decode(r, "article")
	if err != nil {
		return err
	}
	title, err := required(obj, "title")
	if err != nil {
		return err
	}
	description, err := required(obj, "description")
	if err != nil {
		return err
	}
	body, err := required(obj, "body")
	if err != nil {
		return err
	}
	status := "published"
	if raw, ok := obj["status"]; ok {
		if string(raw) == "null" || json.Unmarshal(raw, &status) != nil || status != "draft" && status != "published" {
			return fail(422, "status", "is invalid")
		}
	}
	tags, _, err := tagsField(obj)
	if err != nil {
		return err
	}
	var pub any
	if status == "published" {
		pub = time.Now().UTC()
	}
	tx, err := a.DB.BeginTx(r.Context(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var id int64
	err = tx.Tx.QueryRowContext(r.Context(), `INSERT INTO articles(author_id,slug,title,description,body,status,published_at) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING id`, viewer, slugify(title), title, description, body, status, pub).Scan(&id)
	if err != nil {
		return err
	}
	if err = a.replaceTags(r.Context(), tx.Tx, id, tags); err != nil {
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	v, err := a.viewArticle(r.Context(), id, viewer, true)
	if err != nil {
		return err
	}
	send(w, 201, map[string]any{"article": v})
	return nil
}
func (a *App) getArticle(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, false)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	v, err := a.viewArticle(r.Context(), x.ID, viewer, true)
	if err != nil {
		return err
	}
	send(w, 200, map[string]any{"article": v})
	return nil
}
func (a *App) listArticles(w http.ResponseWriter, r *http.Request) error {
	path := r.URL.Path
	required := path == "/api/articles/feed" || path == "/api/user/drafts"
	viewer, err := a.caller(r, required)
	if err != nil {
		return err
	}
	limit, offset := 20, 0
	if s := r.URL.Query().Get("limit"); s != "" {
		limit, err = strconv.Atoi(s)
		if err != nil || limit < 0 {
			return fail(422, "limit", "is invalid")
		}
		if limit > 100 {
			limit = 100
		}
	}
	if s := r.URL.Query().Get("offset"); s != "" {
		offset, err = strconv.Atoi(s)
		if err != nil || offset < 0 {
			return fail(422, "offset", "is invalid")
		}
	}
	where := " WHERE a.status='published' AND $1::bigint>=0"
	args := []any{viewer}
	add := func(condition string, value any) {
		args = append(args, value)
		where += fmt.Sprintf(" AND "+condition, len(args))
	}
	if path == "/api/user/drafts" {
		where = " WHERE a.status='draft' AND a.author_id=$1"
	}
	if path == "/api/articles/feed" {
		where += " AND EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=$1 AND f.followed_id=a.author_id)"
	}
	if path == "/api/articles" {
		q := r.URL.Query()
		if v := q.Get("tag"); v != "" {
			add("EXISTS(SELECT 1 FROM article_tags t WHERE t.article_id=a.id AND t.tag=$%d)", v)
		}
		if v := q.Get("author"); v != "" {
			add("u.username=$%d", v)
		}
		if v := q.Get("favorited"); v != "" {
			add("EXISTS(SELECT 1 FROM favorites f JOIN users fu ON fu.id=f.user_id WHERE f.article_id=a.id AND fu.username=$%d)", v)
		}
	}
	var count int
	err = a.DB.DB.QueryRowContext(r.Context(), "SELECT count(*) FROM articles a JOIN users u ON u.id=a.author_id"+where, args...).Scan(&count)
	if err != nil {
		return err
	}
	args = append(args, limit, offset)
	query := viewSelect + where + fmt.Sprintf(" ORDER BY a.created_at DESC,a.id DESC LIMIT $%d OFFSET $%d", len(args)-1, len(args))
	rows, err := a.DB.DB.QueryContext(r.Context(), query, args...)
	if err != nil {
		return err
	}
	defer rows.Close()
	articles := []ArticleView{}
	for rows.Next() {
		v, e := scanView(rows, false)
		if e != nil {
			return e
		}
		articles = append(articles, v)
	}
	if err = rows.Err(); err != nil {
		return err
	}
	send(w, 200, map[string]any{"articles": articles, "articlesCount": count})
	return nil
}
func (a *App) updateArticle(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	if err = own(x, viewer); err != nil {
		return err
	}
	obj, err := decode(r, "article")
	if err != nil {
		return err
	}
	revision, present, err := integer(obj, "revision")
	if err != nil {
		return err
	}
	if present && revision != x.Revision {
		v, _ := a.viewArticle(r.Context(), x.ID, viewer, true)
		return failure{409, "revision", "is stale", v}
	}
	v, err := a.saveArticle(r.Context(), x.ID, viewer, obj, present, revision, false, "", "")
	if err != nil {
		return err
	}
	send(w, 200, map[string]any{"article": v})
	return nil
}
func (a *App) saveArticle(ctx context.Context, id, viewer int64, obj map[string]json.RawMessage, check bool, revision int, shared bool, shareID, key string) (ArticleView, error) {
	a.rooms.mu.Lock()
	defer a.rooms.mu.Unlock()
	if shared {
		validID, err := a.validShare(ctx, shareID, key)
		if err != nil || validID != id {
			return ArticleView{}, fail(404, "share", "not found")
		}
	}
	tx, err := a.DB.BeginTx(ctx, nil)
	if err != nil {
		return ArticleView{}, err
	}
	defer tx.Rollback()
	var x articleRecord
	err = tx.Tx.QueryRowContext(ctx, "SELECT "+recordColumns+" FROM articles WHERE id=$1 FOR UPDATE", id).Scan(&x.ID, &x.AuthorID, &x.Slug, &x.Title, &x.Description, &x.Body, &x.Status, &x.Revision, &x.CreatedAt, &x.UpdatedAt, &x.PublishedAt)
	if err != nil {
		return ArticleView{}, err
	}
	if check && revision != x.Revision {
		v, _ := a.viewArticle(ctx, id, viewer, true)
		if shared {
			return ArticleView{}, failure{409, "revision", "is stale", sharedView(v)}
		}
		return ArticleView{}, failure{409, "revision", "is stale", v}
	}
	if shared {
		for key := range obj {
			if key != "title" && key != "body" && key != "revision" {
				return ArticleView{}, fail(422, key, "is invalid")
			}
		}
	}
	for _, key := range []string{"title", "description", "body"} {
		if shared && key == "description" {
			continue
		}
		v, ok, e := field(obj, key)
		if e != nil {
			return ArticleView{}, e
		}
		if !ok {
			if shared {
				return ArticleView{}, bad(key)
			}
			continue
		}
		if strings.TrimSpace(v) == "" {
			return ArticleView{}, bad(key)
		}
		switch key {
		case "title":
			if v != x.Title {
				x.Slug = slugify(v)
			}
			x.Title = v
		case "description":
			x.Description = v
		case "body":
			x.Body = v
		}
	}
	tags, present, e := tagsField(obj)
	if e != nil {
		return ArticleView{}, e
	}
	if shared && present {
		return ArticleView{}, fail(422, "tagList", "is invalid")
	}
	_, err = tx.Tx.ExecContext(ctx, "UPDATE articles SET slug=$1,title=$2,description=$3,body=$4,revision=revision+1,updated_at=now() WHERE id=$5", x.Slug, x.Title, x.Description, x.Body, id)
	if err != nil {
		return ArticleView{}, err
	}
	if present {
		if err = a.replaceTags(ctx, tx.Tx, id, tags); err != nil {
			return ArticleView{}, err
		}
	}
	if err = tx.Commit(); err != nil {
		return ArticleView{}, err
	}
	v, err := a.viewArticle(ctx, id, viewer, true)
	if err == nil {
		a.rooms.updatedLocked(id, sharedView(v))
	}
	return v, err
}
func (a *App) deleteArticle(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	if err = own(x, viewer); err != nil {
		return err
	}
	_, err = a.DB.DB.ExecContext(r.Context(), "DELETE FROM articles WHERE id=$1", x.ID)
	if err != nil {
		return err
	}
	a.rooms.revokeArticle(x.ID)
	send(w, 204, nil)
	return nil
}
func (a *App) publishArticle(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	if err = own(x, viewer); err != nil {
		return err
	}
	a.rooms.mu.Lock()
	defer a.rooms.mu.Unlock()
	changed := false
	if x.Status == "draft" {
		result, updateErr := a.DB.DB.ExecContext(r.Context(), "UPDATE articles SET status='published',published_at=now(),revision=revision+1,updated_at=now() WHERE id=$1 AND status='draft'", x.ID)
		err = updateErr
		if err != nil {
			return err
		}
		n, _ := result.RowsAffected()
		changed = n > 0
	}
	v, err := a.viewArticle(r.Context(), x.ID, viewer, true)
	if err != nil {
		return err
	}
	if changed {
		a.rooms.updatedLocked(x.ID, sharedView(v))
	}
	send(w, 200, map[string]any{"article": v})
	return nil
}
