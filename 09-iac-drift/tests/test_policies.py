# tests/test_policies.py
from __future__ import annotations

from crew.policies import run_deterministic

SEEDED = [
    {"type": "aws_db_instance", "name": "bad-db",
     "tags": {"environment": "staging",
              "owner": "x", "cost-center": "y"},
     "encrypted": False},
    {"type": "aws_s3_bucket", "name": "bad-bucket",
     "tags": {"environment": "staging",
              "owner": "x", "cost-center": "y"},
     "acl": "public-read"},
    {"type": "aws_security_group", "name": "bad-sg",
     "tags": {"environment": "staging",
              "owner": "x", "cost-center": "y"},
     "ingress": [{"from_port": 22,
                  "cidr": "0.0.0.0/0"}]},
]


def test_all_seeded_violations_caught():
    findings = run_deterministic(SEEDED)
    flagged = {f["resource"] for f in findings}
    assert flagged == {"bad-db", "bad-bucket", "bad-sg"}


def test_clean_resource_passes():
    clean = [{
        "type": "aws_instance", "name": "web-1",
        "tags": {"environment": "staging",
                 "owner": "x", "cost-center": "y"},
    }]
    assert run_deterministic(clean) == []
