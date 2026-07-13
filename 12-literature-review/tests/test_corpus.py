# tests/test_corpus.py — corpus ingest/parsing logic, DB and
# embedding calls faked out so the suite stays fully offline.
from __future__ import annotations

import lit_review.corpus as corpus


class _FakeConn:
    """Records every execute() call instead of touching a real DB."""

    def __init__(self):
        self.executed: list[tuple] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        return self

    def fetchall(self):
        return [("2501.00001",), ("2501.00002",)]


def test_ingest_embeds_clusters_and_upserts_every_paper(monkeypatch):
    fake_conn = _FakeConn()
    monkeypatch.setattr(corpus, "_conn", lambda: fake_conn)
    # Deterministic stand-in for the real embedding call: length of
    # the abstract is enough signal for KMeans to separate clusters.
    monkeypatch.setattr(
        corpus, "embed_text", lambda text: [float(len(text)), 0.0])

    papers = [
        {"id": "2501.00001", "title": "A", "authors": ["X"],
         "year": 2024, "abstract": "short"},
        {"id": "2501.00002", "title": "B", "authors": ["Y"],
         "year": 2024, "abstract": "a much longer abstract body"},
    ]
    corpus.ingest(papers)

    inserts = [e for e in fake_conn.executed if "INSERT INTO papers" in e[0]]
    assert len(inserts) == 2
    inserted_ids = {params[0] for _, params in inserts}
    assert inserted_ids == {"2501.00001", "2501.00002"}
    # authors are joined into a single string column
    joined_authors = {params[2] for _, params in inserts}
    assert "X" in joined_authors
    assert "Y" in joined_authors


def test_ingest_caps_clusters_at_paper_count(monkeypatch):
    """With N_CLUSTERS=8 but only 1 paper, k must drop to 1 or KMeans
    itself would raise -- this is the corpus-parsing edge case."""
    fake_conn = _FakeConn()
    monkeypatch.setattr(corpus, "_conn", lambda: fake_conn)
    monkeypatch.setattr(corpus, "embed_text", lambda text: [1.0, 2.0])

    papers = [{"id": "2501.00003", "title": "Solo", "authors": ["Z"],
               "year": 2023, "abstract": "one paper only"}]
    corpus.ingest(papers)  # must not raise

    inserts = [e for e in fake_conn.executed if "INSERT INTO papers" in e[0]]
    assert len(inserts) == 1
    assert inserts[0][1][0] == "2501.00003"


def test_get_known_ids_returns_id_set(monkeypatch):
    monkeypatch.setattr(corpus, "_conn", lambda: _FakeConn())
    ids = corpus.get_known_ids()
    assert ids == {"2501.00001", "2501.00002"}
