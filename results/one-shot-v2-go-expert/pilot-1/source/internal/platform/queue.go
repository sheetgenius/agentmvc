package platform

import (
	"context"
	"database/sql"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/riverqueue/river"
	"github.com/riverqueue/river/riverdriver/riverdatabasesql"
)

// Queue shares application transactions; the second pool is only for LISTEN.
// Register workers before calling this, then start/stop the client with the server.
func Queue(ctx context.Context, db *sql.DB, url string, workers *river.Workers) (*river.Client[*sql.Tx], func(), error) {
	listener, err := pgxpool.New(ctx, url)
	if err != nil {
		return nil, nil, err
	}
	client, err := river.NewClient(riverdatabasesql.NewWithPgxListener(db, listener), &river.Config{
		Workers: workers,
		Queues:  map[string]river.QueueConfig{river.QueueDefault: {MaxWorkers: 4}},
	})
	if err != nil {
		listener.Close()
		return nil, nil, err
	}
	return client, listener.Close, nil
}
