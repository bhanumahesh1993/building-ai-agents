# analyst/sql_agent.py
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_ai import Agent, RunContext

MODEL = os.getenv(
    "ANALYST_MODEL", "anthropic:claude-sonnet-4-5")

DDL_DML = re.compile(
    r"\b(insert|update|delete|drop|alter|create|"
    r"pragma|call|export|import|install|load|copy)\b",
    re.IGNORECASE)

FILE_FUNCS = (
    "read_csv", "read_parquet", "read_json",
    "attach", "httpfs", "glob(")


class SQLQuery(BaseModel):
    """One validated, read-only analytical query."""
    sql: str = Field(
        description="A single SELECT statement.")
    intent: str = Field(
        description="One sentence: what this answers.")
    chart_kind: Literal[
        "none", "bar", "line", "hist", "scatter"
    ] = "none"

    @field_validator("sql")
    @classmethod
    def must_be_safe(cls, v: str) -> str:
        head = v.strip().lower()
        if not (head.startswith("select")
                or head.startswith("with")):
            raise ValueError(
                "Only SELECT or WITH...SELECT allowed.")
        if DDL_DML.search(head):
            raise ValueError(
                "Query touches a banned DDL/DML word.")
        if any(f in head for f in FILE_FUNCS):
            raise ValueError(
                "Query touches a banned file/extension "
                "function.")
        return v


@dataclass
class AnalystDeps:
    schema_context: str


SYSTEM = """You are a careful data analyst. Write
exactly one read-only SELECT (or WITH ... SELECT)
statement against the schema below. Never write DDL
or DML. Never reference a table or column that is not
listed. If the question can't be answered from this
schema, say so in `intent` and return
`SELECT 1 WHERE false`.

Schema:
{schema}"""

_agent: Agent[AnalystDeps, SQLQuery] | None = None


def get_agent() -> Agent[AnalystDeps, SQLQuery]:
    """Lazily build the agent so the module imports
    without a key present (tests, offline use)."""
    global _agent
    if _agent is None:
        _agent = Agent(
            MODEL,
            output_type=SQLQuery,
            deps_type=AnalystDeps,
        )

        @_agent.system_prompt
        def build_prompt(
                ctx: RunContext[AnalystDeps]) -> str:
            return SYSTEM.format(
                schema=ctx.deps.schema_context)
    return _agent
