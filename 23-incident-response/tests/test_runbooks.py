# tests/test_runbooks.py
"""Runbook retrieval structure: copilot/runbooks.py is a small
RAG store -- a fixed corpus of runbooks, embedded once and
cached, searched by cosine similarity against a query vector
built from the root cause's hypothesis. These tests fake the
Voyage client so the retrieval logic (caching, ranking) is
proven deterministically, with no network call and no
VOYAGE_API_KEY."""
from __future__ import annotations

import pytest

from copilot import runbooks


class _FakeEmbedResponse:
    def __init__(self, embeddings):
        self.embeddings = embeddings


class _FakeVoyageClient:
    """Document embeds return one-hot vectors indexed by the
    RUNBOOKS corpus order; query embeds return whatever vector
    the test registered for that exact query text, so the
    nearest match is known in advance."""

    def __init__(self, query_vectors_by_text):
        self._query_vectors = query_vectors_by_text

    def embed(self, texts, model, input_type):
        if input_type == "document":
            n = len(texts)
            vectors = [
                [1.0 if i == j else 0.0 for j in range(n)]
                for i in range(n)]
            return _FakeEmbedResponse(vectors)
        text = texts[0]
        return _FakeEmbedResponse(
            [self._query_vectors[text]])


@pytest.fixture(autouse=True)
def _reset_corpus_cache(monkeypatch):
    """Each test gets a fresh embedding cache -- retrieve()
    caches the corpus vectors globally in the module."""
    monkeypatch.setattr(runbooks, "_corpus_vectors", None)
    monkeypatch.setattr(runbooks, "_client", None)
    yield
    monkeypatch.setattr(runbooks, "_corpus_vectors", None)
    monkeypatch.setattr(runbooks, "_client", None)


def _n_runbooks() -> int:
    return len(runbooks.RUNBOOKS)


def test_retrieve_returns_nearest_runbook_by_cosine_similarity(
        monkeypatch):
    """A query vector aligned with runbook index 2 (rb-033,
    dependency outage) must retrieve exactly that runbook, not
    merely the first or last entry in the corpus."""
    n = _n_runbooks()
    target_index = 2
    query = "downstream dependency looks unhealthy"
    query_vec = [0.0] * n
    query_vec[target_index] = 1.0

    fake = _FakeVoyageClient({query: query_vec})
    monkeypatch.setattr(runbooks, "_get_client", lambda: fake)

    result = runbooks.retrieve(query)
    assert result["id"] == runbooks.RUNBOOKS[target_index]["id"]
    assert result["id"] == "rb-033"
    assert result["action"] == "notify_only"


def test_retrieve_picks_highest_similarity_not_just_any_match(
        monkeypatch):
    """A query vector that leans mostly toward one runbook but
    slightly toward every other must still resolve to the
    highest-scoring one, proving this is a similarity ranking
    and not an arbitrary or first-match pick."""
    n = _n_runbooks()
    query = "deploy landed right before the error spike"
    query_vec = [0.05] * n
    query_vec[0] = 0.9  # rb-014: deploy regression / rollback

    fake = _FakeVoyageClient({query: query_vec})
    monkeypatch.setattr(runbooks, "_get_client", lambda: fake)

    result = runbooks.retrieve(query)
    assert result["id"] == "rb-014"
    assert result["action"] == "rollback_deploy"


def test_corpus_embedded_once_and_cached_across_calls(
        monkeypatch):
    """The runbook corpus should be embedded once and reused --
    retrieve() must not re-embed all five runbooks on every
    call, only the (much smaller) query."""
    calls = {"document": 0, "query": 0}
    n = _n_runbooks()

    class _CountingClient(_FakeVoyageClient):
        def embed(self, texts, model, input_type):
            calls[input_type] += 1
            return super().embed(texts, model, input_type)

    q1, q2 = "q one", "q two"
    vecs = {
        q1: [1.0] + [0.0] * (n - 1),
        q2: [0.0, 1.0] + [0.0] * (n - 2),
    }
    fake = _CountingClient(vecs)
    monkeypatch.setattr(runbooks, "_get_client", lambda: fake)

    runbooks.retrieve(q1)
    runbooks.retrieve(q2)

    assert calls["document"] == 1
    assert calls["query"] == 2


def test_every_runbook_has_action_and_blast_radius():
    """Structural completeness of the corpus: remediate.py
    trusts every runbook to carry an action and a stated blast
    radius, so a retrieval can never hand back a runbook that
    is missing either."""
    for rb in runbooks.RUNBOOKS:
        assert rb["action"]
        assert rb["blast_radius"]
        assert rb["steps"]


def test_get_client_raises_only_when_actually_called_without_key(
        monkeypatch):
    """Without VOYAGE_API_KEY, building the client must fail at
    call time, not at import time."""
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    monkeypatch.setattr(runbooks, "_client", None)
    with pytest.raises(KeyError):
        runbooks._get_client()
