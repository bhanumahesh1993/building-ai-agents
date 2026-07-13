# review/diff_utils.py
from __future__ import annotations

import re

from .state import Hunk

_FILE_RE = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)")


def parse_diff(diff_text: str) -> list[Hunk]:
    """Parse a unified diff into per-hunk records."""
    hunks: list[Hunk] = []
    path = ""
    lines: list[str] = []
    start = end = 0

    def flush() -> None:
        if lines:
            hunks.append({
                "path": path, "start_line": start,
                "end_line": end,
                "patch": "\n".join(lines),
            })

    for raw in diff_text.splitlines():
        file_m = _FILE_RE.match(raw)
        if file_m:
            flush()
            lines, path = [], file_m.group(1)
            continue
        hunk_m = _HUNK_RE.match(raw)
        if hunk_m:
            flush()
            lines = [raw]
            start = int(hunk_m.group(1))
            end = start
            continue
        if lines:
            lines.append(raw)
            added = raw.startswith("+")
            if added and not raw.startswith("+++"):
                end += 1
    flush()
    return hunks


def render_hunks(hunks: list[Hunk]) -> str:
    """Render hunks into one text block for a prompt."""
    blocks = []
    for h in hunks:
        blocks.append(
            f"### {h['path']} "
            f"(lines {h['start_line']}-{h['end_line']})\n"
            f"{h['patch']}")
    return "\n\n".join(blocks)
