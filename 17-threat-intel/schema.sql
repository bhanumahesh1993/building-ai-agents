-- schema.sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS advisories (
    cve_id TEXT PRIMARY KEY,
    summary TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL
);

CREATE INDEX IF NOT EXISTS advisories_embedding_idx
    ON advisories USING hnsw (embedding vector_cosine_ops);
