package conduit

import (
	"context"
	"crypto/rand"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/http"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/uptrace/bun"
)

var nonSlug = regexp.MustCompile(`[^a-z0-9]+`)

const (
	statusDraft     = "draft"
	statusPublished = "published"
)

func slug(title string) (string, error) {
	var random [8]byte
	if _, err := rand.Read(random[:]); err != nil {
		return "", err
	}
	base := strings.Trim(nonSlug.ReplaceAllString(strings.ToLower(title), "-"), "-")
	if base == "" {
		base = "article"
	}
	return fmt.Sprintf("%s-%x", base, random), nil
}

func tagField(fields map[string]json.RawMessage) ([]string, bool, error) {
	raw, ok := fields["tagList"]
	if !ok {
		return nil, false, nil
	}
	var tags []string
	if json.Unmarshal(raw, &tags) != nil || tags == nil {
		return nil, true, invalid("tagList")
	}
	seen := make(map[string]bool)
	unique := make([]string, 0, len(tags))
	for _, tag := range tags {
		if strings.TrimSpace(tag) == "" {
			return nil, true, invalid("tagList")
		}
		if !seen[tag] {
			unique = append(unique, tag)
			seen[tag] = true
		}
	}
	return unique, true, nil
}

func addTags(ctx context.Context, db bun.IDB, articleID int64, tags []string) error {
	for position, tag := range tags {
		if _, err := db.NewInsert().Model(&ArticleTag{ArticleID: articleID, Tag: tag, Position: position}).Exec(ctx); err != nil {
			return err
		}
	}
	return nil
}

func replaceTags(ctx context.Context, db bun.IDB, articleID int64, tags []string) error {
	if _, err := db.NewDelete().Table("article_tags").Where("article_id = ?", articleID).Exec(ctx); err != nil {
		return err
	}
	return addTags(ctx, db, articleID, tags)
}

func (a *App) sendArticle(w http.ResponseWriter, r *http.Request, status int, article *Article) error {
	v, err := a.articleView(r.Context(), article, viewer(r), true)
	if err == nil {
		write(w, status, map[string]any{"article": v})
	}
	return err
}

func (a *App) createArticle(w http.ResponseWriter, r *http.Request) error {
	fields, err := decodeObject(r, "article")
	if err != nil {
		return err
	}
	status := statusPublished
	if raw, ok := fields["status"]; ok {
		var requested string
		if json.Unmarshal(raw, &requested) != nil || requested != statusDraft && requested != statusPublished {
			return apiError{status: http.StatusUnprocessableEntity, field: "status", text: "is invalid"}
		}
		status = requested
	}
	title, err := requiredString(fields, "title")
	if err != nil {
		return err
	}
	description, err := requiredString(fields, "description")
	if err != nil {
		return err
	}
	body, err := requiredString(fields, "body")
	if err != nil {
		return err
	}
	tags, _, err := tagField(fields)
	if err != nil {
		return err
	}
	articleSlug, err := slug(title)
	if err != nil {
		return err
	}
	now := time.Now().UTC().Truncate(time.Microsecond)
	article := &Article{AuthorID: viewer(r).ID, Slug: articleSlug, Title: title, Description: description, Body: body, Status: status, Revision: 1, CreatedAt: now, UpdatedAt: now}
	if status == statusPublished {
		article.PublishedAt = &now
	}
	if err := a.db.RunInTx(r.Context(), nil, func(ctx context.Context, tx bun.Tx) error {
		if _, err := tx.NewInsert().Model(article).Exec(ctx); err != nil {
			return err
		}
		return addTags(ctx, tx, article.ID, tags)
	}); err != nil {
		return err
	}
	view := articleFields(article, true)
	if tags != nil {
		view.TagList = tags
	}
	view.Author, err = a.profile(r.Context(), viewer(r), viewer(r))
	if err == nil {
		write(w, http.StatusCreated, map[string]any{"article": view})
	}
	return err
}

func (a *App) getArticle(w http.ResponseWriter, r *http.Request) error {
	article, err := a.visibleArticle(r)
	if err != nil {
		return err
	}
	return a.sendArticle(w, r, http.StatusOK, article)
}

func (a *App) visibleArticle(r *http.Request) (*Article, error) {
	article := new(Article)
	query := a.db.NewSelect().Model(article).Where("slug = ?", chi.URLParam(r, "slug"))
	if user := viewer(r); user != nil {
		query.Where("(status = ? OR author_id = ?)", statusPublished, user.ID)
	} else {
		query.Where("status = ?", statusPublished)
	}
	err := query.Scan(r.Context())
	if errors.Is(err, sql.ErrNoRows) {
		return nil, missing("article")
	}
	return article, err
}

func (a *App) ownedArticle(r *http.Request) (*Article, error) {
	article, err := a.visibleArticle(r)
	if err != nil {
		return nil, err
	}
	if article.AuthorID != viewer(r).ID {
		return nil, forbidden("article")
	}
	return article, nil
}

func (a *App) updateArticle(w http.ResponseWriter, r *http.Request) error {
	article, err := a.ownedArticle(r)
	if err != nil {
		return err
	}
	fields, err := decodeObject(r, "article")
	if err != nil {
		return err
	}
	raw, checkRevision := fields["revision"]
	if checkRevision {
		var revision *int
		if json.Unmarshal(raw, &revision) != nil || revision == nil {
			return apiError{status: http.StatusUnprocessableEntity, field: "revision", text: "is invalid"}
		}
		if *revision != article.Revision {
			return a.staleRevision(r, article)
		}
	}
	if title, ok, err := stringField(fields, "title"); err != nil {
		return err
	} else if ok && title != article.Title {
		article.Title = title
		article.Slug, err = slug(title)
		if err != nil {
			return err
		}
	}
	if description, ok, err := stringField(fields, "description"); err != nil {
		return err
	} else if ok {
		article.Description = description
	}
	if body, ok, err := stringField(fields, "body"); err != nil {
		return err
	} else if ok {
		article.Body = body
	}
	tags, present, err := tagField(fields)
	if err != nil {
		return err
	}
	article.UpdatedAt = time.Now().UTC().Truncate(time.Microsecond)
	previousRevision := article.Revision
	var changed int64
	if err := a.db.RunInTx(r.Context(), nil, func(ctx context.Context, tx bun.Tx) error {
		query := tx.NewUpdate().Model(article).Column("slug", "title", "description", "body", "updated_at").Set("revision = revision + 1").WherePK()
		if checkRevision {
			query.Where("revision = ?", previousRevision)
		}
		result, err := query.Exec(ctx)
		if err != nil {
			return err
		}
		changed, err = result.RowsAffected()
		if err != nil || changed == 0 || !present {
			return err
		}
		return replaceTags(ctx, tx, article.ID, tags)
	}); err != nil {
		return err
	}
	if changed == 0 {
		if !checkRevision {
			return missing("article")
		}
		current := new(Article)
		if err := a.db.NewSelect().Model(current).Where("id = ?", article.ID).Scan(r.Context()); err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return missing("article")
			}
			return err
		}
		return a.staleRevision(r, current)
	}
	if err := a.db.NewSelect().Model(article).WherePK().Scan(r.Context()); err != nil {
		return err
	}
	return a.sendArticle(w, r, http.StatusOK, article)
}

func (a *App) staleRevision(r *http.Request, article *Article) error {
	current, err := a.articleView(r.Context(), article, viewer(r), true)
	if err != nil {
		return err
	}
	return apiError{status: http.StatusConflict, field: "revision", text: "is stale", article: &current}
}

func (a *App) publishArticle(w http.ResponseWriter, r *http.Request) error {
	article, err := a.ownedArticle(r)
	if err != nil {
		return err
	}
	if article.Status == statusDraft {
		now := time.Now().UTC().Truncate(time.Microsecond)
		_, err = a.db.NewUpdate().Model(article).
			Set("status = ?", statusPublished).
			Set("published_at = ?", now).
			Set("revision = revision + 1").
			Set("updated_at = ?", now).
			WherePK().Where("status = ?", statusDraft).Exec(r.Context())
		if err != nil {
			return err
		}
		if err := a.db.NewSelect().Model(article).WherePK().Scan(r.Context()); err != nil {
			return err
		}
	}
	return a.sendArticle(w, r, http.StatusOK, article)
}

func (a *App) deleteArticle(w http.ResponseWriter, r *http.Request) error {
	article, err := a.ownedArticle(r)
	if err != nil {
		return err
	}
	_, err = a.db.NewDelete().Model(article).WherePK().Exec(r.Context())
	if err == nil {
		write(w, http.StatusNoContent, nil)
	}
	return err
}

func (a *App) setFavorite(w http.ResponseWriter, r *http.Request) error {
	article, err := a.visibleArticle(r)
	if err != nil {
		return err
	}
	if article.Status == statusDraft {
		return apiError{status: http.StatusUnprocessableEntity, field: "article", text: "is a draft"}
	}
	if r.Method == http.MethodPost {
		_, err = a.db.NewInsert().Model(&Favorite{UserID: viewer(r).ID, ArticleID: article.ID}).On("CONFLICT DO NOTHING").Exec(r.Context())
	} else {
		_, err = a.db.NewDelete().Table("favorites").Where("user_id = ? AND article_id = ?", viewer(r).ID, article.ID).Exec(r.Context())
	}
	if err != nil {
		return err
	}
	return a.sendArticle(w, r, http.StatusOK, article)
}

func pagination(r *http.Request) (int, int) {
	limit, err := strconv.Atoi(r.URL.Query().Get("limit"))
	if err != nil || limit < 0 {
		limit = 20
	}
	offset, err := strconv.Atoi(r.URL.Query().Get("offset"))
	if err != nil || offset < 0 {
		offset = 0
	}
	return limit, offset
}

func (a *App) listArticles(w http.ResponseWriter, r *http.Request) error {
	return a.articleList(w, r, "public")
}

func (a *App) feed(w http.ResponseWriter, r *http.Request) error {
	return a.articleList(w, r, "feed")
}

func (a *App) drafts(w http.ResponseWriter, r *http.Request) error {
	return a.articleList(w, r, "drafts")
}

func (a *App) articleList(w http.ResponseWriter, r *http.Request, scope string) error {
	articles := make([]Article, 0)
	query := a.db.NewSelect().Model(&articles)
	if scope == "drafts" {
		query.Where("status = ? AND author_id = ?", statusDraft, viewer(r).ID)
	} else if scope == "feed" {
		query.Where("status = ?", statusPublished)
		query.Where("author_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)", viewer(r).ID)
	} else {
		query.Where("status = ?", statusPublished)
		params := r.URL.Query()
		if author := params.Get("author"); author != "" {
			query.Where("author_id IN (SELECT id FROM users WHERE username = ?)", author)
		}
		if tag := params.Get("tag"); tag != "" {
			query.Where("id IN (SELECT article_id FROM article_tags WHERE tag = ?)", tag)
		}
		if favorite := params.Get("favorited"); favorite != "" {
			query.Where("id IN (SELECT article_id FROM favorites WHERE user_id IN (SELECT id FROM users WHERE username = ?))", favorite)
		}
	}
	count, err := query.Count(r.Context())
	if err != nil {
		return err
	}
	limit, offset := pagination(r)
	if err := query.OrderExpr("created_at DESC, id DESC").Limit(limit).Offset(offset).Scan(r.Context()); err != nil {
		return err
	}
	views, err := a.articleViews(r.Context(), articles, viewer(r), false)
	if err != nil {
		return err
	}
	write(w, http.StatusOK, map[string]any{"articles": views, "articlesCount": count})
	return nil
}

func (a *App) tags(w http.ResponseWriter, r *http.Request) error {
	tags := make([]string, 0)
	if err := a.db.NewSelect().Table("article_tags").Column("tag").Join("JOIN articles ON articles.id = article_tags.article_id").Where("articles.status = ?", statusPublished).Distinct().Order("tag").Scan(r.Context(), &tags); err != nil {
		return err
	}
	write(w, http.StatusOK, map[string]any{"tags": tags})
	return nil
}
