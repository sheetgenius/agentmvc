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

func (a *App) replaceTags(r *http.Request, articleID int64, tags []string) error {
	return a.db.RunInTx(r.Context(), nil, func(ctx context.Context, tx bun.Tx) error {
		if _, err := tx.NewDelete().Table("article_tags").Where("article_id = ?", articleID).Exec(ctx); err != nil {
			return err
		}
		for position, tag := range tags {
			if _, err := tx.NewInsert().Model(&ArticleTag{ArticleID: articleID, Tag: tag, Position: position}).Exec(ctx); err != nil {
				return err
			}
		}
		return nil
	})
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
	article := &Article{AuthorID: viewer(r).ID, Slug: articleSlug, Title: title, Description: description, Body: body, CreatedAt: now, UpdatedAt: now}
	if _, err := a.db.NewInsert().Model(article).Exec(r.Context()); err != nil {
		return err
	}
	if err := a.replaceTags(r, article.ID, tags); err != nil {
		return err
	}
	return a.sendArticle(w, r, http.StatusCreated, article)
}

func (a *App) getArticle(w http.ResponseWriter, r *http.Request) error {
	article, err := a.articleBySlug(r.Context(), chi.URLParam(r, "slug"))
	if errors.Is(err, sql.ErrNoRows) {
		return missing("article")
	}
	if err != nil {
		return err
	}
	return a.sendArticle(w, r, http.StatusOK, article)
}

func (a *App) ownedArticle(r *http.Request) (*Article, error) {
	article, err := a.articleBySlug(r.Context(), chi.URLParam(r, "slug"))
	if errors.Is(err, sql.ErrNoRows) {
		return nil, missing("article")
	}
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
	if _, err := a.db.NewUpdate().Model(article).Column("slug", "title", "description", "body", "updated_at").WherePK().Exec(r.Context()); err != nil {
		return err
	}
	if present {
		if err := a.replaceTags(r, article.ID, tags); err != nil {
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
	article, err := a.articleBySlug(r.Context(), chi.URLParam(r, "slug"))
	if errors.Is(err, sql.ErrNoRows) {
		return missing("article")
	}
	if err != nil {
		return err
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
	return a.articleList(w, r, false)
}

func (a *App) feed(w http.ResponseWriter, r *http.Request) error {
	return a.articleList(w, r, true)
}

func (a *App) articleList(w http.ResponseWriter, r *http.Request, feed bool) error {
	articles := make([]Article, 0)
	query := a.db.NewSelect().Model(&articles)
	if feed {
		query.Where("author_id IN (SELECT followed_id FROM follows WHERE follower_id = ?)", viewer(r).ID)
	} else {
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
	views := make([]ArticleView, 0, len(articles))
	for i := range articles {
		view, err := a.articleView(r.Context(), &articles[i], viewer(r), false)
		if err != nil {
			return err
		}
		views = append(views, view)
	}
	write(w, http.StatusOK, map[string]any{"articles": views, "articlesCount": count})
	return nil
}

func (a *App) tags(w http.ResponseWriter, r *http.Request) error {
	tags := make([]string, 0)
	if err := a.db.NewSelect().Table("article_tags").Column("tag").Distinct().Order("tag").Scan(r.Context(), &tags); err != nil {
		return err
	}
	write(w, http.StatusOK, map[string]any{"tags": tags})
	return nil
}
