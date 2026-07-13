# contracts/playbook.py
from __future__ import annotations

import json
import os

import psycopg
from llama_index.embeddings.openai import (
    OpenAIEmbedding)
from langchain_anthropic import ChatAnthropic
from psycopg.rows import dict_row

from .state import GroundedFlag, PlaybookWorkerState

DB_URL = os.environ["PLAYBOOK_DB_URL"]
WORKER_MODEL = os.getenv(
    "WORKER_MODEL", "claude-sonnet-4-5")

_embed = OpenAIEmbedding(model="text-embedding-3-large")
_llm = ChatAnthropic(model=WORKER_MODEL, temperature=0)

PLAYBOOK_SYSTEM = """You are grounding a risk flag
against this firm's standard playbook positions. Given
the flagged clause and the retrieved standard positions,
say how far the clause deviates and cite which position
you used. Do NOT soften or remove the flag -- only
ground it in something checkable.

Flagged clause: {quote}
Flag rationale: {rationale}

Standard positions:
{positions}

Return ONLY JSON:
{{"deviation": "aligned|narrower|broader|silent",
  "playbook_ref": "id of the position used",
  "grounded_rationale": "one grounded paragraph"}}"""


def _conn():
    return psycopg.connect(DB_URL, row_factory=dict_row)


def retrieve_standard_position(
    clause_type: str, query_text: str, k: int = 2,
) -> list[dict]:
    """Top-k standard positions for this clause type."""
    vec = _embed.get_text_embedding(query_text)
    sql = """
        SELECT id, position_text, source
        FROM playbook_positions
        WHERE clause_type = %s
        ORDER BY embedding <=> %s::vector
        LIMIT %s
    """
    with _conn() as c, c.cursor() as cur:
        cur.execute(sql, (clause_type, vec, k))
        return cur.fetchall()


def playbook_node(state: PlaybookWorkerState) -> dict:
    """Ground one flagged clause against the playbook."""
    flag = state["flag"]
    hits = retrieve_standard_position(
        flag["clause_type"], flag["quote"])
    positions = "\n".join(
        f"[{h['id']}] {h['position_text']} "
        f"(source: {h['source']})" for h in hits
    ) or "none on file for this clause type"
    prompt = PLAYBOOK_SYSTEM.format(
        quote=flag["quote"], rationale=flag["rationale"],
        positions=positions)
    resp = _llm.invoke(prompt)
    parsed = json.loads(resp.content)
    grounded: GroundedFlag = {
        **flag,
        "deviation": parsed["deviation"],
        "playbook_ref": parsed["playbook_ref"],
        "rationale": parsed["grounded_rationale"],
    }
    return {"grounded": [grounded]}
