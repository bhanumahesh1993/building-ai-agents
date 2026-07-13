# builder/spec.py
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field

MAX_CRITERIA = 10   # spec-scope guardrail


class EarsPattern(str, Enum):
    """The five EARS acceptance-criteria templates."""
    UBIQUITOUS = "ubiquitous"
    EVENT = "event"
    STATE = "state"
    UNWANTED = "unwanted"
    OPTIONAL = "optional"


class AcceptanceCriterion(BaseModel):
    """One EARS-style, testable requirement."""
    id: str
    pattern: EarsPattern
    trigger: str | None = None
    response: str


class AppSpec(BaseModel):
    """The durable input: what, never how."""
    name: str
    goal: str
    acceptance_criteria: list[AcceptanceCriterion]
    non_goals: list[str] = Field(default_factory=list)
    max_iterations: int = 2

    def check_scope(self) -> None:
        """Refuse specs that are already gold-plating."""
        n = len(self.acceptance_criteria)
        if n > MAX_CRITERIA:
            raise ValueError(
                f"{n} criteria exceeds {MAX_CRITERIA} — "
                "split this into two specs")


def render_criterion(c: AcceptanceCriterion) -> str:
    """Render a criterion back into its EARS sentence."""
    r = c.response
    if c.pattern is EarsPattern.UBIQUITOUS:
        return f"The system shall {r}."
    if c.pattern is EarsPattern.EVENT:
        return f"When {c.trigger}, the system shall {r}."
    if c.pattern is EarsPattern.STATE:
        return f"While {c.trigger}, the system shall {r}."
    if c.pattern is EarsPattern.UNWANTED:
        return f"If {c.trigger}, then the system shall {r}."
    return f"Where {c.trigger}, the system shall {r}."
