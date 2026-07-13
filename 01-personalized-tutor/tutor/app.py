# tutor/app.py
from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .agents import (
    get_diagnostic_agent, get_evaluator_agent, get_planner_agent,
    get_tutor_agent,
)
from .guardrails import is_off_syllabus, redirect, wants_the_answer
from .memory import (
    init_db, record_turn, recent_weak_areas, save_diagnostic,
    save_plan,
)
from .models import DiagnosticResult, LessonPlan, TurnFeedback
from .observability import setup_tracing
from .prompts import (
    DIAGNOSTIC_SYSTEM, EVAL_SYSTEM, PLANNER_SYSTEM, TUTOR_SYSTEM,
)

MAX_ATTEMPTS = 3   # guardrail: cap the adaptation loop per topic
MAX_TOPICS = 4
MAX_TURNS_PER_SESSION = 30   # guardrail: hard session ceiling
LADDER = ["easy", "medium", "hard"]

DIAGNOSTIC_BANK = [
    {"topic": "limits",
     "concept": "limit of a rational function at a hole",
     "question": ("What happens to (x^2 - 4) / (x - 2) "
                  "as x approaches 2?")},
    {"topic": "derivatives",
     "concept": "power rule",
     "question": "What is the derivative of x^3?"},
    {"topic": "chain_rule",
     "concept": "chain rule with a polynomial inside",
     "question": "If f(x) = sin(x^2), what is f'(x)?"},
]

app = FastAPI(title="Personalized Tutor API")
setup_tracing()
init_db()

SESSIONS: dict[str, dict] = {}   # session_id -> live state


class StartReq(BaseModel):
    student_id: str
    subject: str = "calculus: limits and derivatives"


class AnswerReq(BaseModel):
    answer: str


def _shift_difficulty(current: str, direction: str) -> str:
    i = LADDER.index(current)
    if direction == "harder":
        i = min(i + 1, len(LADDER) - 1)
    elif direction == "easier":
        i = max(i - 1, 0)
    return LADDER[i]


@app.post("/sessions")
def start(req: StartReq):
    """Create a session and ask the first diagnostic probe."""
    session_id = str(uuid.uuid4())
    recall = recent_weak_areas(req.student_id, req.subject)
    SESSIONS[session_id] = {
        "student_id": req.student_id,
        "subject": req.subject,
        "phase": "diagnostic",
        "probe_idx": 0,
        "transcript": [],
        "plan": None,
        "topic_idx": 0,
        "difficulty": "medium",
        "attempts": 0,
        "turn_count": 0,
        "last_question": None,
        "last_feedback": "none yet",
    }
    probe = DIAGNOSTIC_BANK[0]
    return {
        "session_id": session_id,
        "phase": "diagnostic",
        "question": probe["question"],
        "welcome_back": recall or None,
    }


async def _ask_next_question(state: dict) -> dict:
    topic = state["plan"][state["topic_idx"]]
    turn = await get_tutor_agent().run(TUTOR_SYSTEM.format(
        subject=state["subject"], topic=topic["name"],
        objective=topic["objective"], difficulty=state["difficulty"],
        recent=state["last_feedback"],
    ))
    state["last_question"] = turn.output.question
    state["turn_count"] += 1
    return {
        "phase": "teaching", "topic": topic["name"],
        "difficulty": state["difficulty"],
        "question": turn.output.question,
    }


async def _advance_diagnostic(state: dict, answer_text: str) -> dict:
    probe = DIAGNOSTIC_BANK[state["probe_idx"]]
    grade = await get_evaluator_agent().run(EVAL_SYSTEM.format(
        subject=state["subject"], question=probe["question"],
        concept=probe["concept"], answer=answer_text,
    ))
    feedback: TurnFeedback = grade.output
    state["transcript"].append({
        "topic": probe["topic"], "answer": answer_text,
        "correct": feedback.correct,
    })
    state["probe_idx"] += 1

    if state["probe_idx"] < len(DIAGNOSTIC_BANK):
        nxt = DIAGNOSTIC_BANK[state["probe_idx"]]
        return {"phase": "diagnostic", "question": nxt["question"]}

    transcript_text = "\n".join(
        f"- {t['topic']}: {'correct' if t['correct'] else 'wrong'}"
        for t in state["transcript"]
    )
    diag = await get_diagnostic_agent().run(DIAGNOSTIC_SYSTEM.format(
        subject=state["subject"], n=len(state["transcript"]),
        transcript=transcript_text,
    ))
    result: DiagnosticResult = diag.output
    save_diagnostic(state["student_id"], state["subject"], result)

    plan_resp = await get_planner_agent().run(PLANNER_SYSTEM.format(
        subject=state["subject"], max_topics=MAX_TOPICS,
        diagnostic=result.model_dump_json(),
    ))
    plan: LessonPlan = plan_resp.output
    save_plan(state["student_id"], state["subject"], plan)

    state["plan"] = [t.model_dump() for t in plan.topics]
    state["phase"] = "teaching"
    state["difficulty"] = plan.topics[0].difficulty
    first_q = await _ask_next_question(state)
    return first_q | {"diagnostic": result.model_dump()}


async def _advance_teaching(state: dict, answer_text: str) -> dict:
    if wants_the_answer(answer_text) or is_off_syllabus(answer_text):
        return {
            "phase": "teaching", "question": state["last_question"],
            "notice": redirect(state["subject"]),
        }

    topic = state["plan"][state["topic_idx"]]
    grade = await get_evaluator_agent().run(EVAL_SYSTEM.format(
        subject=state["subject"], question=state["last_question"],
        concept=topic["objective"], answer=answer_text,
    ))
    feedback: TurnFeedback = grade.output
    record_turn(
        state["student_id"], state["subject"], topic["name"],
        state["difficulty"], state["last_question"], answer_text,
        feedback,
    )
    state["attempts"] += 1
    state["last_feedback"] = (
        f"answered '{answer_text}' -- "
        + ("correct" if feedback.correct else "incorrect")
        + (f" ({feedback.misconception})"
           if feedback.misconception else "")
    )
    state["difficulty"] = _shift_difficulty(
        state["difficulty"], feedback.next_difficulty)

    advance = feedback.correct or state["attempts"] >= MAX_ATTEMPTS
    if advance:
        state["topic_idx"] += 1
        state["attempts"] = 0
        if (state["topic_idx"] >= len(state["plan"])
                or state["turn_count"] >= MAX_TURNS_PER_SESSION):
            state["phase"] = "done"
            return {"phase": "done", "feedback": feedback.model_dump()}
        state["difficulty"] = state["plan"][state["topic_idx"]][
            "difficulty"]

    nxt = await _ask_next_question(state)
    return nxt | {"feedback": feedback.model_dump()}


@app.post("/sessions/{session_id}/answer")
async def answer(session_id: str, req: AnswerReq):
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(404, "unknown session")
    if state["phase"] == "diagnostic":
        return await _advance_diagnostic(state, req.answer)
    if state["phase"] == "teaching":
        return await _advance_teaching(state, req.answer)
    raise HTTPException(400, "session already finished")
