ALTER TABLE articles
  ADD COLUMN status TEXT NOT NULL DEFAULT 'published' CHECK (status IN ('draft', 'published')),
  ADD COLUMN published_at TIMESTAMPTZ,
  ADD COLUMN revision BIGINT NOT NULL DEFAULT 1;
--;;
UPDATE articles SET published_at = created_at;
