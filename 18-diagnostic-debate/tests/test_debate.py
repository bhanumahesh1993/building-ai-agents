# tests/test_debate.py
from panel.graph import route_after_moderate
from panel.graph import route_after_bias


def _hyp(name, conf, status="active"):
    return {"name": name, "rationale": "r",
            "confidence": conf, "status": status}


def test_route_stops_at_confidence_gap():
    state = {
        "hypotheses": [_hyp("a", 0.7), _hyp("b", 0.2)],
        "round": 1, "max_rounds": 3}
    assert route_after_moderate(state) == "bias_check"


def test_route_caps_at_max_rounds():
    state = {
        "hypotheses": [_hyp("a", 0.4), _hyp("b", 0.35)],
        "round": 3, "max_rounds": 3}
    assert route_after_moderate(state) == "bias_check"


def test_recheck_fires_only_once():
    state = {
        "force_recheck": True,
        "hypotheses": [_hyp("a", 0.5)],
        "findings": ["f"], "revealed_results": {},
        "round": 1}
    result = route_after_bias(state)
    assert isinstance(result, list)
    state["force_recheck"] = False
    assert route_after_bias(state) == "steward"
