-- +goose Up
ALTER TABLE articles
    ADD COLUMN status text NOT NULL DEFAULT 'published',
    ADD COLUMN published_at timestamptz,
    ADD COLUMN revision integer NOT NULL DEFAULT 1;

UPDATE articles SET published_at = created_at;

-- +goose Down
ALTER TABLE articles
    DROP COLUMN revision,
    DROP COLUMN published_at,
    DROP COLUMN status;
