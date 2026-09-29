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
	"github.com/go-chi/chi/v5"
	"github.com/riverqueue/river"
)

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
	secret := os.Getenv("SECRET_KEY_BASE")
	if secret == "" {
		return errors.New("SECRET_KEY_BASE is required")
	}
	workers := river.NewWorkers()
	conduit.RegisterWorkers(workers, db)
	jobs, err := platform.StartJobs(ctx, db.DB, workers)
	if err != nil {
		return err
	}
	defer func() {
		shutdown, done := context.WithTimeout(context.Background(), 10*time.Second)
		defer done()
		if err := jobs.Stop(shutdown); err != nil {
			slog.Error("job shutdown failed", "error", err)
		}
	}()
	router := chi.NewRouter()
	router.Get("/health", func(w http.ResponseWriter, r *http.Request) {
		if err := db.PingContext(r.Context()); err != nil {
			http.Error(w, "database unavailable", http.StatusServiceUnavailable)
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_, _ = w.Write([]byte(`{"status":"ok"}`))
	})
	router.Mount("/", conduit.New(db, jobs, secret))
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
