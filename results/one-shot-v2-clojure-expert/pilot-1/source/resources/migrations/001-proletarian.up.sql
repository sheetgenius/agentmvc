-- Proletarian 1.0.115 PostgreSQL queue schema, adapted into Migratus statements.
-- https://github.com/msolli/proletarian/blob/v1.0.115/database/postgresql/tables.sql
-- Copyright (c) 2020-2025 Martin Solli. MIT; see licenses/proletarian-MIT.txt.
CREATE SCHEMA IF NOT EXISTS proletarian;
--;;
CREATE TABLE proletarian.job (
    job_id UUID PRIMARY KEY,
    queue TEXT NOT NULL,
    job_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    enqueued_at TIMESTAMPTZ NOT NULL,
    process_at TIMESTAMPTZ NOT NULL
);
--;;
CREATE TABLE proletarian.archived_job (
    job_id UUID PRIMARY KEY,
    queue TEXT NOT NULL,
    job_type TEXT NOT NULL,
    payload TEXT NOT NULL,
    attempts INTEGER NOT NULL,
    enqueued_at TIMESTAMPTZ NOT NULL,
    process_at TIMESTAMPTZ NOT NULL,
    status TEXT NOT NULL,
    finished_at TIMESTAMPTZ NOT NULL
);
--;;
CREATE INDEX job_queue_process_at ON proletarian.job (queue, process_at);
