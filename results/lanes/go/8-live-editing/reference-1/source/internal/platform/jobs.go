package platform

import (
	"context"
	"database/sql"

	"github.com/riverqueue/river"
	"github.com/riverqueue/river/riverdriver/riverdatabasesql"
	"github.com/riverqueue/river/rivermigrate"
)

func StartJobs(ctx context.Context, db *sql.DB, workers *river.Workers) (*river.Client[*sql.Tx], error) {
	driver := riverdatabasesql.New(db)
	migrator, err := rivermigrate.New(driver, nil)
	if err != nil {
		return nil, err
	}
	if _, err := migrator.Migrate(ctx, rivermigrate.DirectionUp, nil); err != nil {
		return nil, err
	}
	client, err := river.NewClient(driver, &river.Config{
		Workers:  workers,
		Queues:   map[string]river.QueueConfig{river.QueueDefault: {MaxWorkers: 4}},
		PollOnly: true,
	})
	if err != nil {
		return nil, err
	}
	if err := client.Start(context.Background()); err != nil {
		return nil, err
	}
	return client, nil
}
