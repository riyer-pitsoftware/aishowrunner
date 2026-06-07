"""SkillPort contract — the single internal port for invoking a showrunner skill.

The product calls every specialist skill through this port (TRD §4.1). Adapters
implement it over the agentic-harness Layer B substrate; rooms and gates depend
only on this interface, never on a concrete dispatch mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class Stance(str, Enum):
    """A specialist's position on the decision under review (TRD §8.4)."""

    SUPPORT = "support"
    CONCERN = "concern"
    BLOCK = "block"
    UNKNOWN = "unknown"


@dataclass
class SkillCallRequest:
    """Typed input for a single skill invocation."""

    skill_name: str
    message: str
    # Model selection (optional overrides; otherwise resolved from SKILL.md tier).
    model_tier: str | None = None
    model: str | None = None
    # Whether to wrap the task in the structured-contribution envelope (TRD §5.3).
    structured: bool = True
    # Attribution for the cost ledger / audit (TRD §5.4, §6.3).
    series_id: str | None = None
    episode_id: str | None = None
    decision_id: str | None = None
    room: str | None = None
    gate: str | None = None


@dataclass
class SkillContribution:
    """Parsed structured output of a contribution (TRD §5.3)."""

    summary: str | None = None
    stance: Stance = Stance.UNKNOWN
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    raw_text: str = ""
    parsed: bool = False


@dataclass
class SkillCallResult:
    """Typed output of a single skill invocation."""

    skill_name: str
    content: str
    model: str
    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    cached_tokens: int = 0
    tokens_estimated: bool = False
    duration_ms: float = 0.0
    status: str = "ok"  # "ok" | "failed"
    error: str | None = None
    content_hash: str = ""
    contribution: SkillContribution | None = None


@runtime_checkable
class SkillPort(Protocol):
    """Invoke a single skill and return a typed result. Implementations must not
    raise on model/dispatch failure — return ``status='failed'`` instead so a
    room fan-out degrades gracefully (TRD §4.4)."""

    async def invoke(self, req: SkillCallRequest) -> SkillCallResult: ...
