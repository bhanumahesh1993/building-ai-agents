# tests/test_drift.py
from __future__ import annotations

from crew.tools import state_diff

DECLARED = [
    {"name": "staging-web-1", "type": "aws_instance",
     "instance_type": "t3.medium", "encrypted": False,
     "acl": "private"},
    {"name": "staging-db", "type": "aws_db_instance",
     "instance_type": None, "encrypted": True,
     "acl": "private"},
]


def test_missing_resource_is_reported_high_severity():
    live = {"staging-db": {"encrypted": True,
                            "acl": "private"}}
    entries = state_diff(DECLARED, live)
    missing = [e for e in entries
               if e["field"] == "existence"]
    assert len(missing) == 1
    assert missing[0]["resource"] == "staging-web-1"
    assert missing[0]["severity"] == "high"


def test_field_drift_detected_and_encryption_is_high_severity():
    live = {
        "staging-web-1": {"instance_type": "t3.large",
                           "encrypted": False,
                           "acl": "private"},
        "staging-db": {"instance_type": None,
                       "encrypted": False,
                       "acl": "private"},
    }
    entries = state_diff(DECLARED, live)
    by_field = {(e["resource"], e["field"]): e
                for e in entries}
    assert ("staging-web-1", "instance_type") in by_field
    assert by_field[("staging-web-1",
                      "instance_type")]["severity"] == "medium"
    assert ("staging-db", "encrypted") in by_field
    assert by_field[("staging-db",
                      "encrypted")]["severity"] == "high"


def test_no_drift_when_state_matches():
    live = {
        "staging-web-1": {"instance_type": "t3.medium",
                           "encrypted": False,
                           "acl": "private"},
        "staging-db": {"instance_type": None,
                       "encrypted": True,
                       "acl": "private"},
    }
    assert state_diff(DECLARED, live) == []
