package conduit

import (
	"context"
	"database/sql"
	"errors"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
)

func (a *App) favorite(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	if err = published(x); err != nil {
		return err
	}
	if r.Method == "POST" {
		_, err = a.DB.DB.ExecContext(r.Context(), "INSERT INTO favorites(user_id,article_id) VALUES($1,$2) ON CONFLICT DO NOTHING", viewer, x.ID)
	} else {
		_, err = a.DB.DB.ExecContext(r.Context(), "DELETE FROM favorites WHERE user_id=$1 AND article_id=$2", viewer, x.ID)
	}
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

type commentView struct {
	ID        int64       `json:"id"`
	Body      string      `json:"body"`
	CreatedAt time.Time   `json:"createdAt"`
	UpdatedAt time.Time   `json:"updatedAt"`
	Author    profileView `json:"author"`
}

func scanComment(row rowScanner) (commentView, error) {
	var c commentView
	var bio, image sql.NullString
	err := row.Scan(&c.ID, &c.Body, &c.CreatedAt, &c.UpdatedAt, &c.Author.Username, &bio, &image, &c.Author.Following)
	if err != nil {
		return c, err
	}
	c.Author.Bio = nullable(bio)
	c.Author.Image = nullable(image)
	return c, nil
}

const commentSelect = `SELECT c.id,c.body,c.created_at,c.updated_at,u.username,u.bio,u.image,
 EXISTS(SELECT 1 FROM follows f WHERE f.follower_id=$1 AND f.followed_id=c.author_id)
 FROM comments c JOIN users u ON u.id=c.author_id`

func (a *App) comments(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, r.Method == "POST")
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	if r.Method == "GET" {
		rows, e := a.DB.DB.QueryContext(r.Context(), commentSelect+" WHERE c.article_id=$2 ORDER BY c.id", viewer, x.ID)
		if e != nil {
			return e
		}
		defer rows.Close()
		out := []commentView{}
		for rows.Next() {
			c, e := scanComment(rows)
			if e != nil {
				return e
			}
			out = append(out, c)
		}
		if e = rows.Err(); e != nil {
			return e
		}
		send(w, 200, map[string]any{"comments": out})
		return nil
	}
	if err = published(x); err != nil {
		return err
	}
	obj, err := decode(r, "comment")
	if err != nil {
		return err
	}
	body, err := required(obj, "body")
	if err != nil {
		return err
	}
	var id int64
	err = a.DB.DB.QueryRowContext(r.Context(), "INSERT INTO comments(article_id,author_id,body) VALUES($1,$2,$3) RETURNING id", x.ID, viewer, body).Scan(&id)
	if err != nil {
		return err
	}
	c, err := scanComment(a.DB.DB.QueryRowContext(r.Context(), commentSelect+" WHERE c.id=$2", viewer, id))
	if err != nil {
		return err
	}
	send(w, 201, map[string]any{"comment": c})
	return nil
}
func (a *App) deleteComment(w http.ResponseWriter, r *http.Request) error {
	viewer, err := a.caller(r, true)
	if err != nil {
		return err
	}
	x, err := a.recordBySlug(r.Context(), chi.URLParam(r, "slug"), viewer)
	if err != nil {
		return err
	}
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		return fail(404, "comment", "not found")
	}
	var author int64
	err = a.DB.DB.QueryRowContext(r.Context(), "SELECT author_id FROM comments WHERE id=$1 AND article_id=$2", id, x.ID).Scan(&author)
	if errors.Is(err, sql.ErrNoRows) {
		return fail(404, "comment", "not found")
	}
	if err != nil {
		return err
	}
	if author != viewer {
		return fail(403, "comment", "forbidden")
	}
	_, err = a.DB.DB.ExecContext(r.Context(), "DELETE FROM comments WHERE id=$1", id)
	if err != nil {
		return err
	}
	send(w, 204, nil)
	return nil
}
func (a *App) Tags(ctx context.Context) ([]string, error) {
	tags := []string{}
	err := a.DB.NewSelect().TableExpr("article_tags AS t").ColumnExpr("DISTINCT t.tag").
		Join("JOIN articles AS a ON a.id=t.article_id").Where("a.status = ?", "published").
		OrderExpr("t.tag").Scan(ctx, &tags)
	return tags, err
}
