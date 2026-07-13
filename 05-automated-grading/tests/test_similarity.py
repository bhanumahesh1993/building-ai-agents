# tests/test_similarity.py
from __future__ import annotations

import importlib

import pytest

import grading.nodes.similarity as similarity_mod


def test_cosine_of_identical_vectors_is_one():
    v = [1.0, 2.0, 3.0]
    assert similarity_mod._cosine(v, v) == 1.0


def test_cosine_of_orthogonal_vectors_is_zero():
    a, b = [1.0, 0.0], [0.0, 1.0]
    assert abs(similarity_mod._cosine(a, b)) < 1e-9


def test_flag_threshold_reads_from_env(monkeypatch):
    monkeypatch.setenv("SIM_THRESHOLD", "0.5")
    reloaded = importlib.reload(similarity_mod)
    assert reloaded.FLAG_THRESHOLD == 0.5
    # restore module state for any test that runs after this one
    monkeypatch.delenv("SIM_THRESHOLD", raising=False)
    importlib.reload(similarity_mod)


def test_get_client_is_lazy_and_requires_key(monkeypatch):
    """The embedding client must not be built at import time, and
    must raise only when actually used without a key -- never on
    import, so the module stays importable offline."""
    monkeypatch.setattr(similarity_mod, "_vo", None)
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    with pytest.raises(KeyError):
        similarity_mod._get_client()
