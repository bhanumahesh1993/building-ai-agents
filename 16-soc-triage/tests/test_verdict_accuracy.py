# tests/test_verdict_accuracy.py
"""Verdict quality on a small labeled set, using the same
scoring code the offline eval harness (evals/run_evals.py)
uses. Everything here is deterministic: the verdict LLM and
the MCP stub calls are faked, so this proves the graph +
scoring wiring is correct without touching a real model, a
real Anthropic key, or a subprocess MCP server."""
from __future__ import annotations

from triage.nodes import verdict as verdict_mod
from triage.nodes import enrich as enrich_mod
from triage.nodes import correlate as correlate_mod
from triage.nodes import respond as respond_mod

from evals.run_evals import run_one, score


async def _fake_mcp_call(params, tool: str, args: dict) -> str:
    if tool == "get_asset_info":
        return "jdoe-laptop: owner=jdoe os=Windows 11 patched=True"
    if tool == "get_user_context":
        return "jdoe: dept=Finance mfa_enrolled=True vip=False"
    if tool == "check_reputation":
        return "203.0.113.44: score=high-risk"
    if tool == "query_related_alerts":
        return ""
    if tool == "disable_account":
        return f"Disabled {args['user_id']} (ticket {args['ticket_id']})."
    if tool == "isolate_host":
        return f"Isolated {args['host_id']} (ticket {args['ticket_id']})."
    return ""


class _FakeResponse:
    def __init__(self, content: str):
        self.content = content


class _FakeVerdictLLM:
    """Looks up the canned verdict JSON by matching the rule
    name embedded in the prompt — lets one fake LLM instance
    serve a whole labeled dataset deterministically."""
    def __init__(self, by_rule: dict[str, str]):
        self._by_rule = by_rule

    def invoke(self, prompt):
        for rule, content in self._by_rule.items():
            if f"Rule: {rule}" in prompt:
                return _FakeResponse(content)
        raise AssertionError(
            f"no canned verdict registered for prompt: "
            f"{prompt[:200]!r}")


# A small labeled set. One case ("unusual-login") is
# deliberately mis-triaged by the canned verdict — the model
# calls it "needs_investigation" when it is really a
# true_positive — so this test also proves the accuracy /
# false-negative-rate math, not just a trivially perfect run.
DATASET = [
    {
        "alert_id": "L1", "rule_name": "mfa-fatigue",
        "raw": "user=jdoe host=jdoe-laptop",
        "true_label": "true_positive",
    },
    {
        "alert_id": "L2", "rule_name": "port-scan",
        "raw": "host=jdoe-laptop",
        "true_label": "false_positive",
    },
    {
        "alert_id": "L3", "rule_name": "unusual-login",
        "raw": "user=jdoe src_ip=203.0.113.44",
        "true_label": "true_positive",
    },
    {
        "alert_id": "L4", "rule_name": "dns-tunnel",
        "raw": "host=jdoe-laptop src_ip=203.0.113.44",
        "true_label": "needs_investigation",
    },
]

CANNED_VERDICTS = {
    "mfa-fatigue": (
        '{"label": "true_positive", "confidence": 0.9, '
        '"evidence": ["mfa fatigue then new device"], '
        '"recommended_action": "disable_account"}'),
    "port-scan": (
        '{"label": "false_positive", "confidence": 0.8, '
        '"evidence": ["known internal vuln scanner"], '
        '"recommended_action": "none"}'),
    # Deliberately soft-called — this is the false negative.
    "unusual-login": (
        '{"label": "needs_investigation", "confidence": 0.5, '
        '"evidence": ["ambiguous, needs analyst review"], '
        '"recommended_action": "notify_soc"}'),
    "dns-tunnel": (
        '{"label": "needs_investigation", "confidence": 0.6, '
        '"evidence": ["suspicious dns pattern"], '
        '"recommended_action": "notify_soc"}'),
}


def test_labeled_set_accuracy_and_false_negative_rate(monkeypatch):
    monkeypatch.setattr(enrich_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(correlate_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(respond_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(
        verdict_mod, "_get_llm",
        lambda: _FakeVerdictLLM(CANNED_VERDICTS))

    rows = [run_one(record) for record in DATASET]
    result = score(rows)

    # 3 of 4 predictions match the label: L1, L2, L4 correct;
    # L3 (unusual-login) is called needs_investigation instead
    # of true_positive.
    assert result["accuracy"] == 0.75

    # Of the 2 actual true_positive cases (L1, L3), 1 was
    # missed (L3) -> false-negative rate 0.5. A miss here means
    # a real attack was under-triaged, which is exactly what
    # this metric exists to catch before it ships silently.
    assert result["false_negative_rate"] == 0.5

    # Every alert still got all three read-only enrichment
    # workers, regardless of verdict outcome.
    assert result["enrichment_completeness"] == 1.0


def test_false_negative_rate_is_zero_when_all_positives_caught(
        monkeypatch):
    """Sanity check on the metric itself: fix the mis-triaged
    case and the false-negative rate must drop to 0."""
    monkeypatch.setattr(enrich_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(correlate_mod, "_call", _fake_mcp_call)
    monkeypatch.setattr(respond_mod, "_call", _fake_mcp_call)

    fixed = dict(CANNED_VERDICTS)
    fixed["unusual-login"] = (
        '{"label": "true_positive", "confidence": 0.85, '
        '"evidence": ["credential-stuffing source, mfa fatigue"], '
        '"recommended_action": "isolate_host"}')
    monkeypatch.setattr(
        verdict_mod, "_get_llm",
        lambda: _FakeVerdictLLM(fixed))

    rows = [run_one(record) for record in DATASET]
    result = score(rows)

    assert result["accuracy"] == 1.0
    assert result["false_negative_rate"] == 0.0
