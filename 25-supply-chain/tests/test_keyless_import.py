# tests/test_keyless_import.py -- every module in both agent
# packages (plus shared/) must import with NO environment
# variables set at all. Every external client -- the ADK agents,
# the MCPToolset/stdio subprocess wiring, the A2A Starlette apps,
# the sqlite DB connection -- is built lazily behind a _get_*()
# helper (or, for the module-level `app` object, a PEP 562
# module __getattr__), never as an import-time side effect.
#
# This is checked for real in a fresh subprocess with env -i, not
# just asserted against the current (possibly already-populated)
# test process environment.
from __future__ import annotations

import subprocess
import sys

import pytest

MODULES = [
    "shared.schemas",
    "inventory_agent.agent",
    "inventory_agent.mcp_server",
    "procurement_agent.agent",
    "procurement_agent.workflow",
    "procurement_agent.mcp_tools",
    "a2a_client",
]


@pytest.mark.parametrize("module", MODULES)
def test_module_imports_with_zero_env_vars(module):
    result = subprocess.run(
        ["env", "-i", f"PATH={sys.exec_prefix}/bin:/usr/bin:/bin",
         sys.executable, "-c", f"import {module}"],
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, (
        f"importing {module} with no env vars failed:\n"
        f"{result.stderr}")


def test_app_attribute_is_lazy_not_built_on_plain_import():
    """`import inventory_agent.agent` alone must not construct
    the MCPToolset / LlmAgent / Starlette app -- only actually
    touching `.app` should."""
    script = (
        "import sys\n"
        "import inventory_agent.agent as m\n"
        "assert m._app is None, "
        "'app was built as an import side effect'\n"
        "assert m._inventory_agent is None\n"
        "assert m._stock_tools is None\n"
        "m.app\n"  # now force it
        "assert m._app is not None\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(__import__("pathlib").Path(__file__).parent.parent),
        capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == 0, result.stderr
