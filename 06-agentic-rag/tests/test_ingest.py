# tests/test_ingest.py — chunking is pure and deterministic
from __future__ import annotations

from assistant.ingest import Chunk, _pack, structural_chunks


def test_pack_splits_on_budget():
    body = (
        "First sentence is short. "
        "Second sentence is also fairly short. "
        "Third one pushes past the budget here."
    )
    windows = _pack(body, budget=40)
    assert len(windows) > 1
    assert all(w for w in windows)


def test_pack_keeps_short_body_in_one_window():
    body = "Just one short sentence."
    windows = _pack(body, budget=900)
    assert windows == [body]


def test_structural_chunks_splits_on_headings():
    text = (
        "# Intro\n"
        "This is the intro paragraph.\n"
        "## Details\n"
        "This is the details paragraph.\n"
    )
    chunks = structural_chunks(text, doc_id="doc-1", budget=900)
    assert all(isinstance(c, Chunk) for c in chunks)
    sections = [c.section for c in chunks]
    assert sections == ["Intro", "Details"]
    assert all(c.doc_id == "doc-1" for c in chunks)
    assert all(c.acl_tags == ["public"] for c in chunks)


def test_structural_chunks_falls_back_to_sentences():
    text = "No headings here. Just plain sentences. Three of them."
    chunks = structural_chunks(text, doc_id="doc-2", budget=900)
    assert len(chunks) == 1
    assert chunks[0].section == "body"
    assert chunks[0].doc_id == "doc-2"


def test_structural_chunks_is_deterministic():
    text = "# Heading\nSome body text that repeats over and over.\n"
    first = structural_chunks(text, doc_id="doc-3")
    second = structural_chunks(text, doc_id="doc-3")
    assert [c.body for c in first] == [c.body for c in second]
