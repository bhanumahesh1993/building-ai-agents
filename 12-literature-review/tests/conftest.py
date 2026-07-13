# tests/conftest.py
from __future__ import annotations

import os

# None of these are read at import time (every external client is
# lazily built behind a _get_*() helper), but setting harmless
# placeholders keeps any call-time os.environ[...] lookup from
# blowing up if a test forgets to monkeypatch it directly.
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost/test")
os.environ.setdefault("GOOGLE_API_KEY", "test-key-not-real")
