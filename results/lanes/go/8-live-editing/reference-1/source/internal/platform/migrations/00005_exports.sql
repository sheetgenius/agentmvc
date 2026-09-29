-- +goose Up
CREATE TABLE exports (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    author_id bigint NOT NULL REFERENCES users(id),
    status text NOT NULL,
    created_at timestamptz NOT NULL,
    completed_at timestamptz,
    articles jsonb
);

-- +goose Down
DROP TABLE exports;
