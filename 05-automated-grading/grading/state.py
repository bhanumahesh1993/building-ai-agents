# grading/state.py
from __future__ import annotations

from typing import Annotated, TypedDict


class Submission(TypedDict):
    """One student's raw essay."""
    student_id: str
    essay_id: str
    text: str


class RubricScore(TypedDict):
    """One criterion's points, with proof."""
    criterion: str
    points: int
    max_points: int
    evidence: str


class GradedEssay(TypedDict, total=False):
    """One essay's full record as it moves
    through score -> feedback -> similarity ->
    review."""
    essay_id: str
    student_id: str
    text: str
    scores: list[RubricScore]
    total: int
    feedback: str
    similarity_flag: bool
    similarity_notes: str
    status: str


def merge_graded(
    a: list[GradedEssay], b: list[GradedEssay],
) -> list[GradedEssay]:
    """Reducer: b's entries replace a's by essay_id,
    so a re-scored essay overwrites its old record
    instead of duplicating it."""
    by_id = {g["essay_id"]: g for g in a}
    for g in b:
        by_id[g["essay_id"]] = g
    return list(by_id.values())


class BatchState(TypedDict, total=False):
    """The graph's shared memory for one batch."""
    prompt: str
    submissions: list[Submission]
    graded: Annotated[list[GradedEssay], merge_graded]
    loops: int
    max_loops: int
    released: list[GradedEssay]
    class_summary: dict


class EssayWorkerState(TypedDict):
    """Private state handed to one score worker."""
    submission: Submission
    prompt: str


class FeedbackWorkerState(TypedDict):
    """Private state handed to one feedback worker."""
    graded: GradedEssay
    prompt: str
