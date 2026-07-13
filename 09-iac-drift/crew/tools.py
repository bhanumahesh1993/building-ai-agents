# crew/tools.py
from __future__ import annotations

import json
import subprocess

import hcl2
from crewai.tools import tool

_ALLOWED = {"init", "validate", "fmt", "plan"}


def _run_terraform(args: list[str], cwd: str) -> str:
    """Guarded subprocess wrapper. Raises before the
    call if anyone ever passes apply or destroy - the
    concrete, code-level version of 'plan-only'."""
    sub = args[0] if args else ""
    if sub not in _ALLOWED:
        raise ValueError(
            f"terraform subcommand '{sub}' is not "
            f"allowed - only {sorted(_ALLOWED)}")
    result = subprocess.run(
        ["terraform", *args], cwd=cwd,
        capture_output=True, text=True, timeout=60)
    return result.stdout + result.stderr


def hcl_validate(cwd: str) -> dict:
    """Syntax and internal-consistency check. Zero
    cloud API calls - init with no backend, then
    validate. Deterministic, no model involved."""
    _run_terraform(["init", "-backend=false",
                     "-input=false"], cwd)
    out = _run_terraform(["validate", "-json"], cwd)
    report = json.loads(out)
    return {
        "valid": report.get("valid", False),
        "error_count": report.get("error_count", 0),
        "diagnostics": report.get("diagnostics", []),
    }


def parse_hcl_resources(hcl_text: str) -> list[dict]:
    """Parse HCL into a flat resource list - ground
    truth for policy, cost, and drift. Never trust the
    Generator's own claim of what it wrote; re-derive
    structure from the artifact it actually produced."""
    parsed = hcl2.loads(hcl_text)
    out: list[dict] = []
    for block in parsed.get("resource", []):
        for r_type, insts in block.items():
            for name, attrs in insts.items():
                out.append({
                    "type": r_type,
                    "name": name,
                    "tags": attrs.get("tags", {}),
                    "encrypted": bool(
                        attrs.get("storage_encrypted")
                        or attrs.get("encrypted")),
                    "acl": attrs.get("acl", "private"),
                    "ingress": attrs.get("ingress", []),
                    "attrs": attrs,
                })
    return out


_INSTANCE_USD = {
    "t3.micro": 7.59, "t3.small": 15.18,
    "t3.medium": 30.37, "m5.large": 70.08,
}
_DB_USD = {
    "db.t3.micro": 12.41, "db.t3.small": 24.82,
    "db.t3.medium": 49.64, "db.m5.large": 140.16,
}
_STORAGE_PER_GB = 0.115
_NAT_GATEWAY_USD = 32.85


@tool("Cost Table Lookup")
def cost_table(resources_json: str) -> str:
    """Rough monthly USD for a parsed resource list.
    A static rate card, not a live pricing API - swap
    for the AWS Price List API in a real deployment."""
    resources = json.loads(resources_json)
    lines: list[dict] = []
    for r in resources:
        kind = r.get("type", "")
        attrs = r.get("attrs", {})
        if kind == "aws_instance":
            it = attrs.get("instance_type", "t3.micro")
            lines.append({
                "resource": r["name"],
                "monthly_usd": _INSTANCE_USD.get(it, 30.0),
            })
        elif kind == "aws_db_instance":
            ic = attrs.get("instance_class", "db.t3.micro")
            gb = attrs.get("allocated_storage", 20)
            lines.append({
                "resource": r["name"],
                "monthly_usd": (_DB_USD.get(ic, 25.0)
                                + gb * _STORAGE_PER_GB),
            })
        elif kind == "aws_nat_gateway":
            lines.append({
                "resource": r["name"],
                "monthly_usd": _NAT_GATEWAY_USD,
            })
    total = sum(l["monthly_usd"] for l in lines)
    return json.dumps({"lines": lines,
                        "total_monthly_usd": total})


@tool("HCL Resource Parser")
def parse_resources(hcl_text: str) -> str:
    """Wraps parse_hcl_resources for agent tool use."""
    return json.dumps(parse_hcl_resources(hcl_text))


@tool("Deterministic Policy Check")
def check_policy(resources_json: str) -> str:
    """Wraps policies.run_deterministic for agent
    tool use - always runs before any model judgment."""
    from .policies import run_deterministic
    resources = json.loads(resources_json)
    return json.dumps(run_deterministic(resources))


@tool("Validate HCL")
def validate_hcl(cwd: str) -> str:
    """Wraps hcl_validate - the Generator's own
    pre-flight check before handing off."""
    return json.dumps(hcl_validate(cwd))


@tool("State Diff")
def diff_state(declared_json: str, live_json: str) -> str:
    """Wraps state_diff for the Drift Detective."""
    declared = json.loads(declared_json)
    live = json.loads(live_json)
    return json.dumps(state_diff(declared, live))


def state_diff(declared: list[dict],
               live: dict) -> list[dict]:
    """Compare declared resources against a live-state
    snapshot. Read-only on both sides - this never
    touches a real cloud API, only a JSON fixture."""
    entries: list[dict] = []
    for res in declared:
        actual = live.get(res["name"])
        if actual is None:
            entries.append({
                "resource": res["name"],
                "field": "existence",
                "declared": "present",
                "actual": "not found in live state",
                "severity": "high",
                "remediation": (
                    "resource was never created, or was "
                    "deleted outside Terraform - run "
                    "terraform plan yourself to confirm"),
            })
            continue
        for field in ("instance_type", "encrypted",
                       "acl"):
            want = res.get(field)
            have = actual.get(field)
            if want is not None and want != have:
                entries.append({
                    "resource": res["name"],
                    "field": field,
                    "declared": str(want),
                    "actual": str(have),
                    "severity": (
                        "high" if field == "encrypted"
                        else "medium"),
                    "remediation": (
                        f"reconcile manually, or update "
                        f"the HCL to match reality and "
                        f"re-review with the crew - do "
                        f"not auto-apply this diff"),
                })
    return entries
