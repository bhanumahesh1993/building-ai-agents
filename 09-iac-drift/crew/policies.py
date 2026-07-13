# crew/policies.py
from __future__ import annotations

import re

NAME_RE = re.compile(r"^[a-z][a-z0-9-]{2,40}$")
REQUIRED_TAGS = ("environment", "owner", "cost-center")
ENCRYPTABLE = (
    "aws_db_instance", "aws_ebs_volume",
    "aws_s3_bucket",
)


def check_naming(resource: dict) -> str | None:
    """Lowercase, hyphenated, 3-40 chars. No model
    call - a regex cannot be talked out of matching."""
    name = resource.get("name", "")
    if not NAME_RE.match(name):
        return (
            f"'{name}' fails naming convention "
            "(lowercase, hyphens, 3-40 chars)")
    return None


def check_tagging(resource: dict) -> str | None:
    """Every resource needs the three required tags."""
    tags = resource.get("tags", {})
    missing = [t for t in REQUIRED_TAGS if t not in tags]
    if missing:
        return f"missing required tags: {missing}"
    return None


def check_encryption(resource: dict) -> str | None:
    """Storage resources must declare encryption."""
    kind = resource.get("type", "")
    if kind in ENCRYPTABLE:
        if not resource.get("encrypted", False):
            return (
                f"{kind} '{resource.get('name')}' is "
                "not encrypted at rest")
    return None


def check_no_public_s3(resource: dict) -> str | None:
    """S3 buckets must not be publicly readable."""
    if resource.get("type") == "aws_s3_bucket":
        acl = resource.get("acl", "private")
        if acl in ("public-read", "public-read-write"):
            return (
                f"bucket '{resource.get('name')}' has "
                f"public ACL '{acl}'")
    return None


def check_no_open_ingress(resource: dict) -> str | None:
    """Security groups must not open SSH to the world."""
    if resource.get("type") == "aws_security_group":
        for rule in resource.get("ingress", []):
            wide = "0.0.0.0/0" in rule.get("cidr", "")
            ssh = rule.get("from_port") == 22
            if wide and ssh:
                return (
                    f"'{resource.get('name')}' opens "
                    "SSH (22) to 0.0.0.0/0")
    return None


DETERMINISTIC_CHECKS = (
    check_naming, check_tagging, check_encryption,
    check_no_public_s3, check_no_open_ingress,
)


def run_deterministic(resources: list[dict]) -> list[dict]:
    """Run every rule against every resource. This is
    the layer that runs first, full stop, and whose
    output the model layer may only narrow, never
    override."""
    findings = []
    for r in resources:
        for check in DETERMINISTIC_CHECKS:
            msg = check(r)
            if msg:
                findings.append({
                    "rule": check.__name__,
                    "resource": r.get("name", "?"),
                    "severity": "high",
                    "message": msg,
                })
    return findings
