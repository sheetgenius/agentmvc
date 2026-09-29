package platform

import (
	"context"
	"database/sql"
	"embed"
	"io/fs"

	"github.com/pressly/goose/v3"
	"github.com/pressly/goose/v3/lock"
	"github.com/riverqueue/river/riverdriver/riverdatabasesql"
	"github.com/riverqueue/river/rivermigrate"
)

//go:embed migrations/*.sql
var migrationFiles embed.FS

func Migrate(ctx context.Context, db *sql.DB) error {
	files, err := fs.Sub(migrationFiles, "migrations")
	if err != nil {
		return err
	}
	locker, err := lock.NewPostgresSessionLocker()
	if err != nil {
		return err
	}
	queue := goose.NewGoMigration(1, &goose.GoFunc{RunDB: func(ctx context.Context, db *sql.DB) error {
		migrator, err := rivermigrate.New(riverdatabasesql.New(db), nil)
		if err != nil {
			return err
		}
		_, err = migrator.Migrate(ctx, rivermigrate.DirectionUp, &rivermigrate.MigrateOpts{TargetVersion: 7})
		return err
	}}, nil)
	provider, err := goose.NewProvider(goose.DialectPostgres, db, files,
		goose.WithSessionLocker(locker), goose.WithGoMigrations(queue))
	if err != nil {
		return err
	}
	_, err = provider.Up(ctx)
	return err
}
