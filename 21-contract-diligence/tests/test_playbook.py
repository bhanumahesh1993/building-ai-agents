# tests/test_playbook.py — the playbook-grounded flag
# logic: every grounded flag still carries the same
# verbatim clause-text quote it was flagged on, and
# grounding only adds a checkable deviation + citation,
# never softens or drops the underlying flag. No real
# pgvector or model call: retrieval and the LLM are both
# monkeypatched.
from __future__ import annotations

import contracts.playbook as playbook_mod
from evals.metrics import citation_to_source


class _FakeResp:
    def __init__(self, content: str):
        self.content = content


class _FakeLLM:
    def __init__(self, content: str):
        self._content = content

    def invoke(self, prompt):
        return _FakeResp(self._content)


CLAUSE = {
    "clause_id": "x1", "contract_id": "c1",
    "clause_type": "liability_cap", "heading": "H",
    "text": "Liability under this agreement shall not "
            "exceed fees paid in the preceding 12 months.",
}
FLAG = {
    "clause_id": "x1", "clause_type": "liability_cap",
    "severity": "high",
    "quote": "shall not exceed fees paid in the "
             "preceding 12 months",
    "rationale": "cap may be set below likely exposure",
}
POSITIONS = [
    {"id": "pb-12", "position_text": "Cap liability at "
     "12-24 months of fees, uncapped for gross negligence.",
     "source": "playbook v3"},
]


def test_playbook_node_grounds_flag_without_softening_or_dropping_it(
        monkeypatch):
    """Grounding adds a checkable deviation + citation but
    must not alter, soften, or drop the original flag."""
    calls: dict = {}

    def _fake_retrieve(clause_type, query_text, k=2):
        calls["clause_type"] = clause_type
        calls["query_text"] = query_text
        return POSITIONS

    monkeypatch.setattr(
        playbook_mod, "retrieve_standard_position", _fake_retrieve)
    monkeypatch.setattr(
        playbook_mod, "_get_llm",
        lambda: _FakeLLM(
            '{"deviation": "narrower", '
            '"playbook_ref": "pb-12", '
            '"grounded_rationale": "the clause caps at 12 '
            'months, narrower than the 12-24 month standard"}'
        ))

    out = playbook_mod.playbook_node(
        {"flag": FLAG, "clause": CLAUSE, "jurisdiction": "Delaware"})

    assert len(out["grounded"]) == 1
    g = out["grounded"][0]

    # Identity of the original flag is preserved.
    assert g["clause_id"] == FLAG["clause_id"]
    assert g["clause_type"] == FLAG["clause_type"]
    assert g["severity"] == FLAG["severity"]
    # The quote is untouched -- still the verbatim text the
    # flag was raised on, still a real substring of the clause.
    assert g["quote"] == FLAG["quote"]
    assert g["quote"] in CLAUSE["text"]

    # Grounding added a checkable deviation + citation.
    assert g["deviation"] == "narrower"
    assert g["playbook_ref"] == "pb-12"
    assert "narrower" in g["rationale"]

    # Retrieval was scoped to this clause's type and quote.
    assert calls["clause_type"] == "liability_cap"
    assert calls["query_text"] == FLAG["quote"]


def test_grounded_flag_passes_the_citation_to_source_metric():
    """The grounded flag's quote is a real substring of its
    own clause text -- the same structural guarantee the
    eval harness checks across a whole matter."""
    grounded = [{
        "clause_id": "x1", "quote": FLAG["quote"],
    }]
    clauses_by_id = {"x1": CLAUSE["text"]}

    assert citation_to_source(grounded, clauses_by_id) == 1.0


def test_playbook_system_prompt_never_softens_the_flag():
    """Static guard: the grounding prompt must keep
    forbidding the model from softening or removing a flag
    -- grounding only makes it checkable, it never launders
    a risk away."""
    normalized = " ".join(
        playbook_mod.PLAYBOOK_SYSTEM.split()).lower()
    assert "do not soften or remove the flag" in normalized
