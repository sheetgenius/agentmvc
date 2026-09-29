package conduit

import (
	"database/sql"
	"errors"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
)

func (a *App) createComment(w http.ResponseWriter, r *http.Request) error {
	article, err := a.visibleArticle(r)
	if err != nil {
		return err
	}
	if article.Status == statusDraft {
		return apiError{status: http.StatusUnprocessableEntity, field: "article", text: "is a draft"}
	}
	fields, err := decodeObject(r, "comment")
	if err != nil {
		return err
	}
	body, err := requiredString(fields, "body")
	if err != nil {
		return err
	}
	now := time.Now().UTC().Truncate(time.Microsecond)
	comment := &Comment{ArticleID: article.ID, AuthorID: viewer(r).ID, Body: body, CreatedAt: now, UpdatedAt: now}
	if _, err := a.db.NewInsert().Model(comment).Exec(r.Context()); err != nil {
		return err
	}
	view, err := a.commentView(r.Context(), comment, viewer(r))
	if err == nil {
		write(w, http.StatusCreated, map[string]any{"comment": view})
	}
	return err
}

func (a *App) listComments(w http.ResponseWriter, r *http.Request) error {
	article, err := a.visibleArticle(r)
	if err != nil {
		return err
	}
	comments := make([]Comment, 0)
	if err := a.db.NewSelect().Model(&comments).Where("article_id = ?", article.ID).Order("id").Scan(r.Context()); err != nil {
		return err
	}
	views := make([]CommentView, 0, len(comments))
	for i := range comments {
		view, err := a.commentView(r.Context(), &comments[i], viewer(r))
		if err != nil {
			return err
		}
		views = append(views, view)
	}
	write(w, http.StatusOK, map[string]any{"comments": views})
	return nil
}

func (a *App) deleteComment(w http.ResponseWriter, r *http.Request) error {
	article, err := a.visibleArticle(r)
	if err != nil {
		return err
	}
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		return missing("comment")
	}
	comment := new(Comment)
	err = a.db.NewSelect().Model(comment).Where("id = ? AND article_id = ?", id, article.ID).Scan(r.Context())
	if errors.Is(err, sql.ErrNoRows) {
		return missing("comment")
	}
	if err != nil {
		return err
	}
	if comment.AuthorID != viewer(r).ID {
		return forbidden("comment")
	}
	if _, err := a.db.NewDelete().Model(comment).WherePK().Exec(r.Context()); err != nil {
		return err
	}
	write(w, http.StatusNoContent, nil)
	return nil
}
