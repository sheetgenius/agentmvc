package conduit

import (
	"context"
	"database/sql"
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/riverqueue/river"
	"github.com/uptrace/bun"
)

type ExportArgs struct {
	ID int64 `json:"id"`
}

func (ExportArgs) Kind() string { return "article_export" }

type ExportWorker struct {
	river.WorkerDefaults[ExportArgs]
	DB *bun.DB
}
type exportArticle struct {
	Slug          string   `json:"slug"`
	Title         string   `json:"title"`
	Description   string   `json:"description"`
	Body          string   `json:"body"`
	TagList       []string `json:"tagList"`
	Status        string   `json:"status"`
	CommentsCount int      `json:"commentsCount"`
}

func (w *ExportWorker) Work(ctx context.Context, job *river.Job[ExportArgs]) error {
	var userID int64
	var status string
	err := w.DB.DB.QueryRowContext(ctx, "SELECT user_id,status FROM exports WHERE id=$1", job.Args.ID).Scan(&userID, &status)
	if errors.Is(err, sql.ErrNoRows) || status == "done" {
		return nil
	}
	if err != nil {
		return err
	}
	rows, err := w.DB.DB.QueryContext(ctx, `SELECT a.slug,a.title,a.description,a.body,a.status,
 COALESCE((SELECT json_agg(t.tag ORDER BY t.tag) FROM article_tags t WHERE t.article_id=a.id),'[]'::json)::text,
 (SELECT count(*) FROM comments c WHERE c.article_id=a.id)
 FROM articles a WHERE a.author_id=$1 ORDER BY a.created_at,a.id`, userID)
	if err != nil {
		return err
	}
	defer rows.Close()
	out := []exportArticle{}
	for rows.Next() {
		var x exportArticle
		var tags string
		if err = rows.Scan(&x.Slug, &x.Title, &x.Description, &x.Body, &x.Status, &tags, &x.CommentsCount); err != nil {
			return err
		}
		if err = json.Unmarshal([]byte(tags), &x.TagList); err != nil {
			return err
		}
		out = append(out, x)
	}
	if err = rows.Err(); err != nil {
		return err
	}
	data, err := json.Marshal(out)
	if err != nil {
		return err
	}
	_, err = w.DB.DB.ExecContext(ctx, "UPDATE exports SET status='done',completed_at=now(),articles=$2 WHERE id=$1 AND status='pending'", job.Args.ID, string(data))
	return err
}

type exportView struct {
	ID          int64      `json:"id"`
	Status      string     `json:"status"`
	CreatedAt   time.Time  `json:"createdAt"`
	CompletedAt *time.Time `json:"completedAt"`
	Articles    any        `json:"articles"`
}

func (a *App) exportByID(ctx context.Context, id, user int64) (exportView, error) {
	var e exportView
	var completed sql.NullTime
	var data []byte
	err := a.DB.DB.QueryRowContext(ctx, "SELECT id,status,created_at,completed_at,articles FROM exports WHERE id=$1 AND user_id=$2", id, user).Scan(&e.ID, &e.Status, &e.CreatedAt, &completed, &data)
	if errors.Is(err, sql.ErrNoRows) {
		return e, fail(404, "export", "not found")
	}
	if err != nil {
		return e, err
	}
	if completed.Valid {
		e.CompletedAt = &completed.Time
	}
	if data != nil {
		var articles []exportArticle
		if err = json.Unmarshal(data, &articles); err != nil {
			return e, err
		}
		e.Articles = articles
	}
	return e, nil
}
func (a *App) createExport(w http.ResponseWriter, r *http.Request) error {
	user, err := a.caller(r, true)
	if err != nil {
		return err
	}
	tx, err := a.DB.BeginTx(r.Context(), nil)
	if err != nil {
		return err
	}
	defer tx.Rollback()
	var id int64
	err = tx.Tx.QueryRowContext(r.Context(), "INSERT INTO exports(user_id) VALUES($1) RETURNING id", user).Scan(&id)
	if err != nil {
		return err
	}
	if _, err = a.Jobs.InsertTx(r.Context(), tx.Tx, ExportArgs{ID: id}, nil); err != nil {
		return err
	}
	if err = tx.Commit(); err != nil {
		return err
	}
	e, err := a.exportByID(r.Context(), id, user)
	if err != nil {
		return err
	}
	e.Status = "pending"
	e.CompletedAt = nil
	e.Articles = nil
	send(w, 202, map[string]any{"export": e})
	return nil
}
func (a *App) getExport(w http.ResponseWriter, r *http.Request) error {
	user, err := a.caller(r, true)
	if err != nil {
		return err
	}
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		return fail(404, "export", "not found")
	}
	e, err := a.exportByID(r.Context(), id, user)
	if err != nil {
		return err
	}
	send(w, 200, map[string]any{"export": e})
	return nil
}
