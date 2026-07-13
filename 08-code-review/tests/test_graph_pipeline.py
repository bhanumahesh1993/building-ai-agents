# tests/test_graph_pipeline.py
"""End-to-end graph tests with the LLM clients replaced by
deterministic fakes -- no network access, no API key required.

These exercise the real gather -> review -> verify -> consolidate
-> gate wiring (only the two LLM calls are stubbed), so they cover:

  * seeded-bug detection: a reviewer citing a bug that is genuinely
    present in the diff survives adversarial verification and blocks.
  * false-positive rate: a hallucinated finding (evidence that does
    not appear in the diff) is refuted by verification and never
    reaches the gate as "confirmed".
"""
from __future__ import annotations

import json

import review.nodes.reviewers as reviewers_mod
import review.nodes.verify as verify_mod
from review.graph import build_graph

from .fixtures import CLEAN_DIFF, SEEDED_BUG_DIFF, SEEDED_BUG_EVIDENCE

HALLUCINATED_LINE = 999
HALLUCINATED_EVIDENCE = "THIS_TEXT_DOES_NOT_EXIST_IN_ANY_DIFF"


class _FakeResp:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeReviewerLLM:
    """Stands in for every reviewer role's ChatAnthropic instance.

    Reports the seeded bug only when the correctness reviewer looks
    at a diff that actually contains it, and always has the style
    reviewer hallucinate an unrelated finding -- so every test run
    also exercises the verifier's ability to refute a false claim.
    """

    def invoke(self, prompt: str) -> _FakeResp:
        findings = []
        if ("a correctness reviewer" in prompt
                and SEEDED_BUG_EVIDENCE in prompt):
            findings.append({
                "path": "app.py", "line": 9,
                "severity": "critical",
                "claim": "eval() executes untrusted input",
                "evidence": SEEDED_BUG_EVIDENCE,
            })
        if "style and maintainability" in prompt:
            findings.append({
                "path": "app.py", "line": HALLUCINATED_LINE,
                "severity": "low",
                "claim": "hallucinated nitpick not actually in diff",
                "evidence": HALLUCINATED_EVIDENCE,
            })
        return _FakeResp(json.dumps({"findings": findings}))


class _FakeVerifierLLM:
    """Confirms a finding only if its cited evidence genuinely
    appears in the diff context it was handed -- the same test a
    real adversarial verifier is meant to apply."""

    def invoke(self, prompt: str) -> _FakeResp:
        finding_block = prompt.split("Finding:\n", 1)[1]
        finding_json, _, rest = finding_block.partition(
            "\n\nDiff context it refers to:\n")
        context, _, _ = rest.partition("\n\nReturn ONLY JSON:")
        finding = json.loads(finding_json)
        verdict = ("confirmed" if finding["evidence"] in context
                   else "refuted")
        return _FakeResp(json.dumps({
            "verdict": verdict,
            "rationale": "fake deterministic check",
        }))


def _patched_graph(monkeypatch):
    monkeypatch.setattr(
        reviewers_mod, "_get_llm", lambda: _FakeReviewerLLM())
    monkeypatch.setattr(
        verify_mod, "_get_llm", lambda: _FakeVerifierLLM())
    return build_graph()


def test_seeded_bug_survives_verification_and_blocks(monkeypatch):
    graph = _patched_graph(monkeypatch)
    cfg = {"configurable": {"thread_id": "seeded-1"}}
    state = graph.invoke(
        {"pr_id": "pr-seeded-1", "diff": SEEDED_BUG_DIFF}, config=cfg)

    confirmed = [v for v in state["verified"]
                 if v["verdict"] == "confirmed"]
    refuted = [v for v in state["verified"]
               if v["verdict"] == "refuted"]

    assert any(
        v["finding"]["evidence"] == SEEDED_BUG_EVIDENCE
        for v in confirmed)
    # The hallucinated finding must be caught and refuted, not
    # confirmed alongside the real bug.
    assert any(
        v["finding"]["line"] == HALLUCINATED_LINE for v in refuted)
    assert not any(
        v["finding"]["line"] == HALLUCINATED_LINE for v in confirmed)
    assert state["decision"] == "block"


def test_clean_diff_has_zero_confirmed_false_positives(monkeypatch):
    graph = _patched_graph(monkeypatch)
    cfg = {"configurable": {"thread_id": "clean-1"}}
    state = graph.invoke(
        {"pr_id": "pr-clean-1", "diff": CLEAN_DIFF}, config=cfg)

    confirmed = [v for v in state["verified"]
                 if v["verdict"] == "confirmed"]
    # False-positive rate: the only reviewer finding on a clean diff
    # is the hallucinated one, and verification must refute it.
    assert confirmed == []
    assert state["decision"] == "approve_with_comments"
