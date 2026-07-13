# lit_review/corpus.py
from __future__ import annotations

import os

import psycopg
from pgvector.psycopg import register_vector
from sklearn.cluster import KMeans

from .tools import embed_text

DB_URL = os.environ["DATABASE_URL"]
EMBED_DIM = 768
N_CLUSTERS = int(os.getenv("MAX_CLUSTERS", "8"))


def _conn():
    conn = psycopg.connect(DB_URL, autocommit=True)
    register_vector(conn)
    return conn


def init_db() -> None:
    """Create the pgvector-backed papers table."""
    with _conn() as conn:
        conn.execute(
            "CREATE EXTENSION IF NOT EXISTS vector")
        conn.execute(f"""
            CREATE TABLE IF NOT EXISTS papers (
              id text PRIMARY KEY,
              title text NOT NULL,
              authors text NOT NULL,
              year int NOT NULL,
              abstract text NOT NULL,
              cluster_id int,
              embedding vector({EMBED_DIM})
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS papers_embed_idx
            ON papers USING hnsw
            (embedding vector_cosine_ops)
        """)


def ingest(papers: list[dict]) -> None:
    """Embed every abstract, cluster, and upsert."""
    vectors = [embed_text(p["abstract"]) for p in papers]
    k = min(N_CLUSTERS, len(papers))
    labels = KMeans(
        n_clusters=k, n_init="auto", random_state=0,
    ).fit_predict(vectors)
    with _conn() as conn:
        for p, vec, cid in zip(papers, vectors, labels):
            conn.execute(
                """INSERT INTO papers (id, title,
                     authors, year, abstract,
                     cluster_id, embedding)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)
                   ON CONFLICT (id) DO UPDATE SET
                     cluster_id = EXCLUDED.cluster_id,
                     embedding = EXCLUDED.embedding""",
                (p["id"], p["title"],
                 ", ".join(p["authors"]), p["year"],
                 p["abstract"], int(cid), vec),
            )


def get_known_ids() -> set[str]:
    """Every paper ID in the corpus — the citation allow-list."""
    with _conn() as conn:
        rows = conn.execute("SELECT id FROM papers").fetchall()
    return {r[0] for r in rows}
