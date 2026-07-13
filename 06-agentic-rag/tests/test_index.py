# tests/test_index.py — RRF fusion math, no DB required
from __future__ import annotations

from assistant.index import RRF_K, rrf_fuse


def test_rrf_fuse_boosts_items_ranked_in_both_lists():
    vector_ranked = ["a", "b", "c"]
    keyword_ranked = ["b", "a", "d"]
    fused = rrf_fuse(vector_ranked, keyword_ranked, k=10)
    ids = [cid for cid, _ in fused]
    # "a" and "b" appear near the top of both lists, so they
    # should outrank items that only appear in one list.
    assert ids[0] in {"a", "b"}
    assert ids[1] in {"a", "b"}
    assert set(ids) == {"a", "b", "c", "d"}


def test_rrf_fuse_matches_manual_formula():
    fused = rrf_fuse(["x"], ["x"], k=10, rrf_k=60)
    assert fused[0][0] == "x"
    expected = 1.0 / (60 + 1) + 1.0 / (60 + 1)
    assert fused[0][1] == expected


def test_rrf_fuse_respects_top_k():
    vector_ranked = [str(i) for i in range(10)]
    keyword_ranked = [str(i) for i in range(10)]
    fused = rrf_fuse(vector_ranked, keyword_ranked, k=3)
    assert len(fused) == 3


def test_rrf_fuse_is_deterministic():
    vector_ranked = ["a", "b", "c"]
    keyword_ranked = ["c", "b", "a"]
    first = rrf_fuse(vector_ranked, keyword_ranked)
    second = rrf_fuse(vector_ranked, keyword_ranked)
    assert first == second


def test_default_rrf_k_matches_sql_constant():
    # Guards against the pure helper and the live SQL
    # query in hybrid_search() drifting out of sync.
    assert RRF_K == 60
