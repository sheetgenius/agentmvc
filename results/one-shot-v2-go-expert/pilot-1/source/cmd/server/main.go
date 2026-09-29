package main

import (
	"context"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"conduit/internal/conduit"
	"conduit/internal/platform"
	"github.com/danielgtaylor/huma/v2"
	"github.com/danielgtaylor/huma/v2/adapters/humachi"
	"github.com/go-chi/chi/v5"
	"github.com/riverqueue/river"
)

type healthResponse struct {
	Body struct {
		Status string `json:"status"`
	}
}
type tagsResponse struct {
	Body struct {
		Tags []string `json:"tags"`
	}
}

func main() {
	if err := run(); err != nil {
		slog.Error("server stopped", "error", err)
		os.Exit(1)
	}
}

func run() error {
	ctx, cancel := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer cancel()
	db, err := platform.Open(ctx, os.Getenv("DATABASE_URL"))
	if err != nil {
		return err
	}
	defer db.Close()
	if err := platform.Migrate(ctx, db.DB); err != nil {
		return err
	}
	app := conduit.New(db, os.Getenv("SECRET_KEY_BASE"))
	workers := river.NewWorkers()
	river.AddWorker(workers, &conduit.ExportWorker{DB: db})
	jobs, closeListener, err := platform.Queue(ctx, db.DB, os.Getenv("DATABASE_URL"), workers)
	if err != nil {
		return err
	}
	defer closeListener()
	app.Jobs = jobs
	if err := jobs.Start(ctx); err != nil {
		return err
	}
	defer func() {
		stopCtx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		_ = jobs.Stop(stopCtx)
	}()
	router := chi.NewRouter()
	router.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("X-Content-Type-Options", "nosniff")
			next.ServeHTTP(w, r)
		})
	})
	app.Routes(router)
	api := humachi.New(router, huma.DefaultConfig("Conduit", "0.0.0"))
	huma.Get(api, "/api/tags", func(ctx context.Context, _ *struct{}) (*tagsResponse, error) {
		tags, err := app.Tags(ctx)
		if err != nil {
			return nil, err
		}
		out := &tagsResponse{}
		out.Body.Tags = tags
		return out, nil
	})
	huma.Get(api, "/health", func(ctx context.Context, _ *struct{}) (*healthResponse, error) {
		out := &healthResponse{}
		out.Body.Status = "ok"
		return out, db.PingContext(ctx)
	})
	port := os.Getenv("PORT")
	if port == "" {
		port = "4110"
	}
	server := &http.Server{Addr: ":" + port, Handler: router, ReadHeaderTimeout: 5 * time.Second}
	shutdownDone := make(chan error, 1)
	go func() {
		<-ctx.Done()
		shutdown, done := context.WithTimeout(context.Background(), 10*time.Second)
		defer done()
		shutdownDone <- server.Shutdown(shutdown)
	}()
	slog.Info("listening", "address", server.Addr)
	if err := server.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	return <-shutdownDone
}
