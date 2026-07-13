# analyst/app.py
from __future__ import annotations

import os
from dataclasses import dataclass

import duckdb
import pandas as pd
from langfuse import observe
from pydantic_ai import Agent

from . import charts, critic, runner, schema
from .sql_agent import AnalystDeps, SQLQuery, get_agent

DB_PATH = os.getenv(
    "ANALYST_DB", "data/bikeshare.duckdb")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "2"))
MAX_QUERIES = int(
    os.getenv("MAX_QUERIES_PER_SESSION", "40"))
NARRATOR_MODEL = os.getenv(
    "NARRATOR_MODEL", "anthropic:claude-sonnet-4-5")

_narrator: Agent[None, str] | None = None


def _get_narrator() -> Agent[None, str]:
    """Lazily build the narrator so the module imports
    without a key present (tests, offline use)."""
    global _narrator
    if _narrator is None:
        _narrator = Agent(NARRATOR_MODEL, output_type=str)
    return _narrator

NARRATE_SYSTEM = """Narrate this data result in 2-3
plain sentences. State only what the numbers show.
If WARNINGS is non-empty, your last sentence must
honestly surface the most important one - never
smooth it over. Never invent a number that is not
in the result.

Question: {question}
Result:
{result}
Warnings:
{warnings}"""


@dataclass
class PipelineResult:
    query: SQLQuery | None
    df: pd.DataFrame
    report: critic.CriticReport


@observe(name="answer_question")
def run_pipeline(
        con, deps: AnalystDeps,
        question: str) -> PipelineResult:
    """Draft -> execute -> self-correct -> critique."""
    messages = None
    error = None
    query = None
    df = pd.DataFrame()
    for _ in range(MAX_RETRIES + 1):
        prompt = question if error is None else (
            f"That query failed with: {error}\n"
            "Write a corrected SELECT.")
        result = get_agent().run_sync(
            prompt, deps=deps, message_history=messages)
        query = result.output
        messages = result.new_messages()
        try:
            df = runner.execute(con, query.sql)
            error = None
            break
        except runner.SandboxError as exc:
            error = str(exc)

    if error is not None:
        report = critic.CriticReport(warnings=[
            f"Gave up after {MAX_RETRIES + 1} tries: "
            f"{error}"])
    else:
        report = critic.check(df)
    return PipelineResult(query, df, report)


def narrate(question: str, pr: PipelineResult) -> str:
    if pr.query is None:
        return "I could not draft a safe query for that."
    prose = _get_narrator().run_sync(NARRATE_SYSTEM.format(
        question=question,
        result=pr.df.head(10).to_string(index=False)
        if not pr.df.empty else "(no rows)",
        warnings="\n".join(pr.report.warnings)
        or "(none)",
    )).output
    lines = [prose]
    if pr.query.chart_kind != "none" and not pr.df.empty:
        path = charts.render(
            pr.df, pr.query.chart_kind, pr.query.intent)
        if path:
            lines += ["", f"Chart: {path}"]
    return "\n".join(lines)


def answer(con, deps: AnalystDeps, question: str) -> str:
    return narrate(
        question, run_pipeline(con, deps, question))


def main() -> None:
    con = duckdb.connect(DB_PATH, read_only=True)
    deps = AnalystDeps(
        schema_context=schema.describe_schema(con))
    print(f"Connected to {DB_PATH}. Ask a question, "
          "or type 'quit'.")
    n = 0
    while True:
        question = input("\n> ").strip()
        if question.lower() in {"quit", "exit"}:
            break
        if n >= MAX_QUERIES:
            print("Session query cap reached.")
            break
        n += 1
        print(answer(con, deps, question))


if __name__ == "__main__":
    main()
