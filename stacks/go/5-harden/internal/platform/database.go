package platform

import (
	"context"
	"database/sql"
	"fmt"

	_ "github.com/jackc/pgx/v5/stdlib"
	"github.com/uptrace/bun"
	"github.com/uptrace/bun/dialect/pgdialect"
)

func Open(ctx context.Context, url string) (*bun.DB, error) {
	if url == "" {
		return nil, fmt.Errorf("DATABASE_URL is required")
	}
	sqlDB, err := sql.Open("pgx", url)
	if err != nil {
		return nil, err
	}
	sqlDB.SetMaxOpenConns(20)
	sqlDB.SetMaxIdleConns(10)
	if err := sqlDB.PingContext(ctx); err != nil {
		_ = sqlDB.Close()
		return nil, err
	}
	return bun.NewDB(sqlDB, pgdialect.New()), nil
}
