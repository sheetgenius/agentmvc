package conduit

import (
	"context"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"database/sql"
	"encoding/base64"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/uptrace/bun"
)

func randomToken(size int) (string, error) {
	bytes := make([]byte, size)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return base64.RawURLEncoding.EncodeToString(bytes), nil
}

func (a *App) share(ctx context.Context, id, key string) (*ArticleShare, error) {
	share := new(ArticleShare)
	err := a.db.NewSelect().Model(share).Where("id = ?", id).Scan(ctx)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, missing("share")
	}
	if err != nil {
		return nil, err
	}
	hash := sha256.Sum256([]byte(key))
	if key == "" || subtle.ConstantTimeCompare(hash[:], share.KeyHash) != 1 {
		return nil, missing("share")
	}
	return share, nil
}

func (a *App) sharedRecord(ctx context.Context, share *ArticleShare) (*Article, error) {
	article := new(Article)
	err := a.db.NewSelect().Model(article).Where("id = ?", share.ArticleID).Scan(ctx)
	if errors.Is(err, sql.ErrNoRows) {
		return nil, missing("share")
	}
	return article, err
}

func (a *App) createShare(w http.ResponseWriter, r *http.Request) error {
	article, err := a.ownedArticle(r)
	if err != nil {
		return err
	}
	id, err := randomToken(18)
	if err != nil {
		return err
	}
	key, err := randomToken(32)
	if err != nil {
		return err
	}
	hash := sha256.Sum256([]byte(key))
	share := &ArticleShare{ID: id, ArticleID: article.ID, KeyHash: hash[:]}
	room := a.rooms.room(article.ID)
	room.mu.Lock()
	defer room.mu.Unlock()
	var oldID string
	err = a.db.RunInTx(r.Context(), nil, func(ctx context.Context, tx bun.Tx) error {
		if err := tx.NewSelect().Table("article_shares").Column("id").Where("article_id = ?", article.ID).Scan(ctx, &oldID); err != nil && !errors.Is(err, sql.ErrNoRows) {
			return err
		}
		if _, err := tx.NewDelete().Table("article_shares").Where("article_id = ?", article.ID).Exec(ctx); err != nil {
			return err
		}
		_, err := tx.NewInsert().Model(share).Exec(ctx)
		return err
	})
	if err != nil {
		return err
	}
	if oldID != "" {
		room.revoke(oldID)
	}
	write(w, http.StatusCreated, map[string]any{"share": map[string]string{"id": id, "key": key}})
	return nil
}

func (a *App) deleteShare(w http.ResponseWriter, r *http.Request) error {
	article, err := a.ownedArticle(r)
	if err != nil {
		return err
	}
	room := a.rooms.room(article.ID)
	room.mu.Lock()
	defer room.mu.Unlock()
	var oldID string
	err = a.db.NewSelect().Table("article_shares").Column("id").Where("article_id = ?", article.ID).Scan(r.Context(), &oldID)
	if err != nil && !errors.Is(err, sql.ErrNoRows) {
		return err
	}
	if _, err := a.db.NewDelete().Table("article_shares").Where("article_id = ?", article.ID).Exec(r.Context()); err != nil {
		return err
	}
	if oldID != "" {
		room.revoke(oldID)
	}
	write(w, http.StatusNoContent, nil)
	return nil
}

func (a *App) getSharedArticle(w http.ResponseWriter, r *http.Request) error {
	share, err := a.share(r.Context(), chi.URLParam(r, "id"), r.Header.Get("X-Share-Key"))
	if err != nil {
		return err
	}
	article, err := a.sharedRecord(r.Context(), share)
	if err == nil {
		write(w, http.StatusOK, map[string]any{"article": sharedArticle(article)})
	}
	return err
}

func (a *App) updateSharedArticle(w http.ResponseWriter, r *http.Request) error {
	id, key := chi.URLParam(r, "id"), r.Header.Get("X-Share-Key")
	share, err := a.share(r.Context(), id, key)
	if err != nil {
		return err
	}
	room := a.rooms.room(share.ArticleID)
	room.mu.Lock()
	defer room.mu.Unlock()
	share, err = a.share(r.Context(), id, key)
	if err != nil {
		return err
	}
	article, err := a.sharedRecord(r.Context(), share)
	if err != nil {
		return err
	}
	var input struct {
		Article map[string]json.RawMessage `json:"article"`
	}
	decoder := json.NewDecoder(io.LimitReader(r.Body, 1<<20))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&input); err != nil || len(input.Article) != 3 {
		return apiError{status: http.StatusUnprocessableEntity, field: "article", text: "is invalid"}
	}
	fields := input.Article
	var revision *int
	if raw, ok := fields["revision"]; !ok || json.Unmarshal(raw, &revision) != nil || revision == nil {
		return apiError{status: http.StatusUnprocessableEntity, field: "revision", text: "is invalid"}
	}
	if *revision != article.Revision {
		return apiError{status: http.StatusConflict, field: "revision", text: "is stale", article: sharedArticle(article)}
	}
	title, err := requiredString(fields, "title")
	if err != nil {
		return err
	}
	body, err := requiredString(fields, "body")
	if err != nil {
		return err
	}
	if title != article.Title {
		article.Slug, err = slug(title)
		if err != nil {
			return err
		}
	}
	article.Title, article.Body = title, body
	article.UpdatedAt = time.Now().UTC().Truncate(time.Microsecond)
	err = a.db.NewUpdate().Model(article).Column("slug", "title", "body", "updated_at").
		Set("revision = revision + 1").WherePK().Where("revision = ?", *revision).
		Returning("revision").Scan(r.Context(), &article.Revision)
	if errors.Is(err, sql.ErrNoRows) {
		current, err := a.sharedRecord(r.Context(), share)
		if err != nil {
			return err
		}
		return apiError{status: http.StatusConflict, field: "revision", text: "is stale", article: sharedArticle(current)}
	}
	if err != nil {
		return err
	}
	current := sharedArticle(article)
	room.updated(current)
	write(w, http.StatusOK, map[string]any{"article": current})
	return nil
}
