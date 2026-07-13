# contracts/ingest.py
from __future__ import annotations

import re
import uuid

from llama_index.core import SimpleDirectoryReader

from .state import ContractDoc

HEADING_RE = re.compile(
    r"\n\s*(\d{1,2}\.\s+[A-Z][A-Z \-/&]{3,60})\s*\n")


def load_contracts(folder: str) -> list[ContractDoc]:
    """Parse every file in folder into raw contract text."""
    docs = SimpleDirectoryReader(folder).load_data()
    out: list[ContractDoc] = []
    for d in docs:
        out.append({
            "contract_id": str(uuid.uuid4())[:8],
            "filename": d.metadata.get("file_name", "?"),
            "text": d.text,
        })
    return out


def split_candidates(text: str) -> list[tuple[str, str]]:
    """Split raw text into (heading, body) candidates."""
    marks = list(HEADING_RE.finditer(text))
    if not marks:
        return [("PREAMBLE", text)]
    blocks: list[tuple[str, str]] = []
    n = len(marks)
    for i, m in enumerate(marks):
        start = m.end()
        end = marks[i + 1].start() if i + 1 < n \
            else len(text)
        heading = m.group(1).strip()
        body = text[start:end].strip()
        blocks.append((heading, body))
    return blocks
