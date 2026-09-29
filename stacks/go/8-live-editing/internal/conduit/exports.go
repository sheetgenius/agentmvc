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

const (
	exportPending = "pending"
	exportDone    = "done"
)

type exportArgs struct {
	ID int64 `json:"id"`
}

func (exportArgs) Kind() string { return "article_export" }

type exportWorker struct {
	river.WorkerDefaults[exportArgs]
	db *bun.DB
}

func RegisterWorkers(workers *river.Workers, db *bun.DB) {
	river.AddWorker(workers, &exportWorker{db: db})
}

func (a *App) createExport(w http.ResponseWriter, r *http.Request) error {
	export := &Export{AuthorID: viewer(r).ID, Status: exportPending, CreatedAt: time.Now().UTC()}
	err := a.db.RunInTx(r.Context(), nil, func(ctx context.Context, tx bun.Tx) error {
		if _, err := tx.NewInsert().Model(export).Exec(ctx); err != nil {
			return err
		}
		_, err := a.jobs.InsertTx(ctx, tx.Tx, exportArgs{ID: export.ID}, nil)
		return err
	})
	if err == nil {
		write(w, http.StatusAccepted, map[string]any{"export": export})
	}
	return err
}

func (a *App) getExport(w http.ResponseWriter, r *http.Request) error {
	id, err := strconv.ParseInt(chi.URLParam(r, "id"), 10, 64)
	if err != nil {
		return missing("export")
	}
	export := new(Export)
	err = a.db.NewSelect().Model(export).Where("id = ? AND author_id = ?", id, viewer(r).ID).Scan(r.Context())
	if errors.Is(err, sql.ErrNoRows) {
		return missing("export")
	}
	if err == nil {
		write(w, http.StatusOK, map[string]any{"export": export})
	}
	return err
}

func (w *exportWorker) Work(ctx context.Context, job *river.Job[exportArgs]) error {
	return w.db.RunInTx(ctx, &sql.TxOptions{Isolation: sql.LevelRepeatableRead}, func(ctx context.Context, tx bun.Tx) error {
		export := new(Export)
		err := tx.NewSelect().Model(export).Where("id = ? AND status = ?", job.Args.ID, exportPending).Scan(ctx)
		if errors.Is(err, sql.ErrNoRows) {
			return nil
		}
		if err != nil {
			return err
		}
		articles, err := exportArticles(ctx, tx, export.AuthorID)
		if err != nil {
			return err
		}
		payload, err := json.Marshal(articles)
		if err != nil {
			return err
		}
		_, err = tx.NewUpdate().Model(export).Set("status = ?", exportDone).Set("completed_at = ?", time.Now().UTC()).Set("articles = ?", string(payload)).WherePK().Where("status = ?", exportPending).Exec(ctx)
		return err
	})
}

func exportArticles(ctx context.Context, tx bun.Tx, authorID int64) ([]ExportArticle, error) {
	articles := make([]Article, 0)
	if err := tx.NewSelect().Model(&articles).Where("author_id = ?", authorID).OrderExpr("created_at, id").Scan(ctx); err != nil {
		return nil, err
	}
	result := make([]ExportArticle, len(articles))
	if len(articles) == 0 {
		return result, nil
	}
	ids := make([]int64, len(articles))
	positions := make(map[int64]int, len(articles))
	for i, article := range articles {
		ids[i] = article.ID
		positions[article.ID] = i
		result[i] = ExportArticle{Slug: article.Slug, Title: article.Title, Description: article.Description, Body: article.Body, Status: article.Status, TagList: []string{}}
	}
	var tags []ArticleTag
	if err := tx.NewSelect().Model(&tags).Where("article_id IN (?)", bun.In(ids)).OrderExpr("article_id, position").Scan(ctx); err != nil {
		return nil, err
	}
	for _, tag := range tags {
		i := positions[tag.ArticleID]
		result[i].TagList = append(result[i].TagList, tag.Tag)
	}
	var counts []struct {
		ArticleID int64
		Count     int
	}
	if err := tx.NewSelect().Table("comments").Column("article_id").ColumnExpr("count(*) AS count").Where("article_id IN (?)", bun.In(ids)).Group("article_id").Scan(ctx, &counts); err != nil {
		return nil, err
	}
	for _, count := range counts {
		result[positions[count.ArticleID]].CommentsCount = count.Count
	}
	return result, nil
}
