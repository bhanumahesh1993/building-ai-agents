# tests/conftest.py
from __future__ import annotations

import os
import tempfile

# Point the app's SQLite DB at a throwaway file before any test
# module imports tutor.app / tutor.memory, so running the offline
# test suite doesn't create/pollute a tutor.db in the project root.
os.environ.setdefault(
    "TUTOR_DB_PATH",
    os.path.join(tempfile.gettempdir(), "tutor_test_offline.db"),
)
