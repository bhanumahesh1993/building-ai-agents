# tests/test_extract.py — clause-extraction structure,
# no real model call: the LLM client is monkeypatched.
from __future__ import annotations

import contracts.extract as extract_mod


class _FakeResp:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    """Returns one canned response per call, in order."""

    def __init__(self, contents: list[str]):
        self._contents = list(contents)
        self._i = 0

    def invoke(self, prompt):
        content = self._contents[self._i]
        self._i += 1
        return _FakeResp(content)


DOC_TEXT = (
    "\n1. INDEMNIFICATION\n"
    "Party A shall indemnify Party B fully and without "
    "limit for any and all claims arising hereunder.\n"
    "\n2. TERMINATION\n"
    "Either party may terminate this agreement for "
    "convenience upon 10 days written notice to the "
    "other party.\n"
)


def test_extract_clauses_returns_typed_located_clauses(monkeypatch):
    """Every extracted clause is typed, located (contract_id +
    heading), and carries a stable, predictable clause_id."""
    doc = {"contract_id": "c1", "filename": "f.txt",
           "text": DOC_TEXT}
    canned = [
        '{"clause_type": "indemnification", "text": '
        '"Party A shall indemnify Party B fully and without '
        'limit for any and all claims arising hereunder."}',
        '{"clause_type": "termination", "text": '
        '"Either party may terminate this agreement for '
        'convenience upon 10 days written notice to the '
        'other party."}',
    ]
    fake_llm = _FakeLLM(canned)
    monkeypatch.setattr(
        extract_mod, "_get_llm", lambda: fake_llm)

    clauses = extract_mod.extract_clauses(doc)

    assert len(clauses) == 2
    for i, c in enumerate(clauses):
        assert set(c) == {
            "clause_id", "contract_id", "clause_type",
            "heading", "text"}
        assert c["clause_id"] == f"c1-{i}"
        assert c["contract_id"] == "c1"
    assert clauses[0]["clause_type"] == "indemnification"
    assert clauses[0]["heading"] == "1. INDEMNIFICATION"
    assert clauses[1]["clause_type"] == "termination"
    assert clauses[1]["heading"] == "2. TERMINATION"


def test_extract_node_skips_short_boilerplate_without_a_model_call(
        monkeypatch):
    """Blocks under 40 chars (signature blocks, page numbers)
    never reach the model at all."""
    doc = {"contract_id": "c2", "filename": "f.txt",
           "text": "\n1. SIGNATURES\nshort\n"}
    calls: list[str] = []

    class _CountingLLM:
        def invoke(self, prompt):
            calls.append(prompt)
            return _FakeResp(
                '{"clause_type": "other", "text": "short"}')

    monkeypatch.setattr(
        extract_mod, "_get_llm", lambda: _CountingLLM())

    out = extract_mod.extract_node({"contracts": [doc]})

    assert out["clauses"] == []
    assert calls == []


def test_extract_node_aggregates_clauses_across_the_whole_set(
        monkeypatch):
    """extract_node fans across every contract in the matter
    and merges the typed clauses into one flat list."""
    docs = [
        {"contract_id": "c1", "filename": "a.txt",
         "text": DOC_TEXT},
        {"contract_id": "c3", "filename": "b.txt",
         "text": DOC_TEXT},
    ]
    canned = [
        '{"clause_type": "indemnification", "text": '
        '"Party A shall indemnify Party B fully and without '
        'limit for any and all claims arising hereunder."}',
        '{"clause_type": "termination", "text": '
        '"Either party may terminate this agreement for '
        'convenience upon 10 days written notice to the '
        'other party."}',
    ] * 2
    fake_llm = _FakeLLM(canned)
    monkeypatch.setattr(
        extract_mod, "_get_llm", lambda: fake_llm)

    out = extract_mod.extract_node({"contracts": docs})

    assert len(out["clauses"]) == 4
    ids = {c["clause_id"] for c in out["clauses"]}
    assert ids == {"c1-0", "c1-1", "c3-0", "c3-1"}
    by_id = {c["clause_id"]: c for c in out["clauses"]}
    assert by_id["c1-0"]["clause_type"] == "indemnification"
    assert by_id["c1-1"]["clause_type"] == "termination"
    assert by_id["c3-0"]["clause_type"] == "indemnification"
    assert by_id["c3-1"]["clause_type"] == "termination"
