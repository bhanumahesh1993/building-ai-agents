# tests/conftest.py
from __future__ import annotations

import os

# None of these are read at import time -- every external client
# (the ADK agents, the A2A Starlette apps, the MCP toolset/server,
# the sqlite connection) is lazily built behind a _get_*() helper
# or a per-call function, never at module import. Setting harmless
# placeholders here just keeps any call-time os.getenv(...) default
# from mattering if a test forgets to monkeypatch something
# directly, and mirrors the pattern used in
# ../12-literature-review/tests/conftest.py and
# ../04-support-deflection.
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-real")
os.environ.setdefault("BUYER_MODEL", "gemini-2.5-flash")
os.environ.setdefault("SUPPLIER_MODEL", "gemini-2.5-flash")
os.environ.setdefault("SOFT_SPEND_CAP", "5000")
os.environ.setdefault("HARD_SPEND_CAP", "25000")
