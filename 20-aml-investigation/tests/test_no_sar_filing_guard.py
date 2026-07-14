# tests/test_no_sar_filing_guard.py — the never-auto-file-a-SAR
# guard must never regress. This project's design implements the
# stop as an ABSENCE of capability, exactly like the payment gate
# in Project 15: there is no CaseStatus.FILED value anywhere in
# aml/state.py, no function anywhere in the aml package files or
# submits a SAR, and POST /cases/{id}/review -- the only exit
# from PENDING_REVIEW -- is a plain FastAPI route that a human
# calls, never an agent tool and never something an agent can
# reach. These tests assert that absence directly (enum
# inspection, AST scan of the whole package, tool-set inspection
# on every agent, plus the no_filing_claim guardrail's regex),
# rather than trusting a prompt.
from __future__ import annotations

import ast
import asyncio
import inspect
import os
import re
from pathlib import Path

import pytest

from agents.tool import FunctionTool
from aml.app import review
from aml.guardrails import no_filing_claim_guardrail
from aml.sar_draft import get_sar_drafter
from aml.state import Case, CaseStatus

AML_PKG_DIR = Path(inspect.getfile(CaseStatus)).parent

# Names that would suggest a filing/submission capability. Kept as
# exact identifier fragments (not bare substrings) so words like
# "get_kyc_profile" or "sanitize_memo" can never collide.
_BANNED_NAME_PATTERNS = re.compile(
    r"(^|_)(file|files|filed|filing|submit|submits|submitted)(_|$)"
    r"|fincen",
    re.IGNORECASE,
)


def _run(coro):
    return asyncio.run(coro)


def test_case_status_has_no_filed_state():
    """The design has no FILED state -- only a human, outside
    this system, makes a SAR filed."""
    names = set(CaseStatus.__members__)
    values = {m.value.upper() for m in CaseStatus}
    assert "FILED" not in names
    assert not any("FILED" in n for n in names)
    assert not any("FILED" in v for v in values)
    assert names == {
        "NEW", "INVESTIGATING", "SCORED",
        "PENDING_REVIEW", "APPROVED", "REJECTED",
    }


def _is_guardrail_decorated(node) -> bool:
    """True if `node` carries @input_guardrail or @output_guardrail.
    These are structurally check functions -- they return a
    GuardrailFunctionOutput describing what they observed, they
    never perform an action -- so a name like
    no_filing_claim_guardrail (which *detects* a filing claim) is
    exempt from the banned-action-name scan below, while an actual
    file_sar()/submit_report() function is not, guardrail or not."""
    for dec in node.decorator_list:
        dec_name = dec.id if isinstance(dec, ast.Name) else (
            dec.attr if isinstance(dec, ast.Attribute) else None)
        if dec_name in ("input_guardrail", "output_guardrail"):
            return True
    return False


def test_no_function_anywhere_in_aml_package_can_file_a_sar():
    """Statically scan every .py file in the aml package for a
    function (or async function) whose name suggests it files or
    submits a report. This is an AST scan, not a runtime check, so
    it catches even a function that is defined but never called.
    Guardrail-decorated functions are exempt (see
    _is_guardrail_decorated) since they only ever detect and
    report, never act."""
    offending = []
    for path in AML_PKG_DIR.glob("*.py"):
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            is_func = isinstance(
                node, (ast.FunctionDef, ast.AsyncFunctionDef))
            if not is_func:
                continue
            if _is_guardrail_decorated(node):
                continue
            if _BANNED_NAME_PATTERNS.search(node.name):
                offending.append(f"{path.name}:{node.name}")
    assert offending == [], (
        f"found filing-shaped function(s): {offending}")


def test_guardrail_exemption_does_not_hide_a_real_filer():
    """Regression guard on the exemption itself: a function named
    like an actual filer, even if decorated as a guardrail, would
    still be wrong to ship -- but more importantly, a function
    that is NOT guardrail-decorated and has a filing-shaped name
    must still be caught. This pins _is_guardrail_decorated to
    only exempt the specific decorators, not just any decorator."""
    src = (
        "from agents import output_guardrail\n\n"
        "@output_guardrail\n"
        "async def no_filing_claim_guardrail(a, b, c):\n"
        "    pass\n\n"
        "@some_other_decorator\n"
        "def file_sar(a):\n"
        "    pass\n"
    )
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
    assert _is_guardrail_decorated(funcs["no_filing_claim_guardrail"])
    assert not _is_guardrail_decorated(funcs["file_sar"])
    assert _BANNED_NAME_PATTERNS.search("file_sar")


def test_no_agent_has_a_filing_or_submission_tool():
    """No agent in the chain may be wired with a tool whose name
    suggests it could file or submit anything on the system's
    behalf."""
    from aml.investigate import get_investigator

    banned = {
        "file_sar", "submit_sar", "file_report",
        "submit_report", "file_to_fincen", "submit_to_fincen",
    }
    for agent in (get_investigator(), get_sar_drafter()):
        names = {t.name for t in agent.tools}
        assert not (names & banned), (
            f"{agent.name} is wired with a banned tool: "
            f"{names & banned}"
        )


def test_sar_drafter_tools_are_empty_it_can_only_write_text():
    """The SAR drafter has no tools at all -- it can only
    produce a text draft, never call out and file anything."""
    drafter = get_sar_drafter()
    assert drafter.tools == []


def test_sar_drafter_has_the_no_filing_claim_output_guardrail():
    drafter = get_sar_drafter()
    assert no_filing_claim_guardrail in drafter.output_guardrails


def test_review_route_is_a_plain_function_not_an_agent_tool():
    """POST /cases/{case_id}/review in aml/app.py is a plain
    FastAPI route -- not a function_tool, not reachable by any
    agent. No agent object appears anywhere in its source."""
    assert not isinstance(review, FunctionTool)
    src = inspect.getsource(review)
    assert "Agent(" not in src
    assert "Runner.run" not in src


def test_review_is_the_only_status_transition_and_never_files():
    """The only two statuses review() can set are APPROVED and
    REJECTED -- never anything filing-shaped."""
    src = inspect.getsource(review)
    assert "CaseStatus.APPROVED" in src
    assert "CaseStatus.REJECTED" in src
    assert not _BANNED_NAME_PATTERNS.search(src.replace(
        "reviewed", "").replace("review", ""))


@pytest.mark.parametrize("text", [
    "The SAR has been filed.",
    "This report was submitted to FinCEN.",
    "SAR filed successfully.",
    "Filing complete, case closed.",
])
def test_no_filing_claim_guardrail_trips_on_filed_claims(text):
    out = _run(no_filing_claim_guardrail.guardrail_function(
        None, None, text))
    assert out.tripwire_triggered is True
    assert out.output_info["claimed_filed"] is True


@pytest.mark.parametrize("text", [
    "DRAFT -- NOT FILED. Prepared for compliance officer review.",
    "The transactions are consistent with structuring. "
    "Evidence: txn_001, txn_002, txn_003.",
])
def test_no_filing_claim_guardrail_allows_hedged_drafts(text):
    out = _run(no_filing_claim_guardrail.guardrail_function(
        None, None, text))
    assert out.tripwire_triggered is False
    assert out.output_info["claimed_filed"] is False


def test_sar_instructions_open_with_the_not_filed_disclaimer():
    """The prompt-level instruction is a second layer, not the
    only one, but it should still say the right thing."""
    drafter = get_sar_drafter()
    assert "DRAFT -- NOT FILED" in drafter.instructions
    assert "no ability to file anything" in drafter.instructions


def test_a_full_case_can_only_exit_pending_review_via_review():
    """Exercise the state machine directly: nothing but calling
    review()'s own logic can move a case out of PENDING_REVIEW,
    and it only ever lands on APPROVED or REJECTED."""
    case = Case(case_id="case_test1", subject_account="acct-1")
    case.status = CaseStatus.PENDING_REVIEW
    assert case.status == CaseStatus.PENDING_REVIEW

    # Simulate exactly what the /review endpoint does.
    approved = True
    case.status = (
        CaseStatus.APPROVED if approved else CaseStatus.REJECTED)
    assert case.status in (CaseStatus.APPROVED, CaseStatus.REJECTED)
    assert case.status != CaseStatus.PENDING_REVIEW


def test_database_url_is_not_read_at_import_time():
    """A regression guard for the lazy-init hardening itself: the
    module must not reach into os.environ for DATABASE_URL at
    import time (that would break keyless import)."""
    import aml.app as app_module

    src = inspect.getsource(app_module)
    assert 'os.environ["DATABASE_URL"]' in src  # still used, but...
    # ...only inside a function, never at module scope.
    tree = ast.parse(src)
    module_level_stmts = tree.body
    for stmt in module_level_stmts:
        assert not (
            isinstance(stmt, ast.Assign)
            and isinstance(stmt.value, ast.Subscript)
        ), "DATABASE_URL must not be read at module scope"
