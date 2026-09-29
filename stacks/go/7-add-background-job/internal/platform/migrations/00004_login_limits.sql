-- +goose Up
ALTER TABLE users
    ADD COLUMN failed_login_attempts integer NOT NULL DEFAULT 0,
    ADD COLUMN last_failed_login_at timestamptz;

-- +goose Down
ALTER TABLE users
    DROP COLUMN last_failed_login_at,
    DROP COLUMN failed_login_attempts;
