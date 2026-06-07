"""Budget evaluation + reserve→commit enforcement (TRD §6.4–6.6).

Pure ``evaluate`` / ``estimate_production`` (fully unit-testable) plus a
``BudgetService`` that persists the reserve→commit protocol with TTL'd
reservations so crashed jobs don't leak budget.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from chronocanvas.showrunner.cost.pricing import load_pricing

DEFAULT_SOFT_PCT = 0.8
RESERVATION_TTL_MIN = 30


@dataclass
class BudgetCheck:
    outcome: str  # "allow" | "warn" | "block"
    projected: float
    limit: float
    over_soft: bool
    over_hard: bool

    def as_error(self) -> dict:
        return {
            "error": "budget_exceeded",
            "projected_usd": round(self.projected, 6),
            "limit_usd": round(self.limit, 6),
        }


def evaluate(
    limit: float,
    spent: float,
    reserved: float,
    amount: float,
    *,
    soft_pct: float = DEFAULT_SOFT_PCT,
    hard_behavior: str = "block",
) -> BudgetCheck:
    """Decide whether ``amount`` may be reserved against a budget.

    limit <= 0 means "no cap" (always allow). Local Ollama ($0 amounts) never
    blocks a positive cap.
    """
    projected = spent + reserved + amount
    if limit <= 0:
        return BudgetCheck("allow", projected, limit, False, False)
    over_hard = projected > limit
    over_soft = projected >= soft_pct * limit
    if over_hard and hard_behavior == "block":
        outcome = "block"
    elif over_hard or over_soft:
        outcome = "warn"
    else:
        outcome = "allow"
    return BudgetCheck(outcome, projected, limit, over_soft, over_hard)


def estimate_production(
    *,
    num_skill_calls: int = 0,
    num_images: int = 0,
    num_video_seconds: int = 0,
    num_tts_chars: int = 0,
    skill_model: str = "ollama/qwen2.5-coder:14b",
    pricing: dict | None = None,
) -> float:
    """Deterministic pre-flight production estimate (TRD §6.5). The enforcement
    number — Fin's envelope is advisory, this is authoritative."""
    from chronocanvas.showrunner.cost.pricing import media_cost, text_cost

    pricing = pricing if pricing is not None else load_pricing()
    est = (pricing or {}).get("estimate", {})
    in_tok = int(est.get("avg_skill_input_tokens", 1200))
    out_tok = int(est.get("avg_skill_output_tokens", 500))

    total = num_skill_calls * text_cost(skill_model, in_tok, out_tok, pricing)
    total += media_cost("image", num_images, pricing)[1]
    total += media_cost("video", num_video_seconds, pricing)[1]
    total += media_cost("tts", num_tts_chars, pricing)[1]
    return round(total, 8)


class BudgetExceeded(Exception):  # noqa: N818  (idiomatic; payload key is budget_exceeded)
    def __init__(self, check: BudgetCheck):
        self.check = check
        super().__init__(f"budget exceeded: projected {check.projected} > limit {check.limit}")


class BudgetService:
    """Persistent reserve→commit budget enforcement."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(
        self,
        scope: str,
        scope_id: uuid.UUID,
        *,
        limit_usd: float = 0.0,
        soft_pct: float = DEFAULT_SOFT_PCT,
        hard_behavior: str = "block",
    ):
        from chronocanvas.db.models.showrunner_cost import Budget

        rows = await self.session.execute(
            select(Budget).where(Budget.scope == scope, Budget.scope_id == scope_id)
        )
        budget = rows.scalar_one_or_none()
        if budget is None:
            budget = Budget(
                scope=scope, scope_id=scope_id, limit_usd=limit_usd,
                soft_pct=soft_pct, hard_behavior=hard_behavior,
                spent_usd=0.0, reserved_usd=0.0,
            )
            self.session.add(budget)
            await self.session.flush()
        return budget

    async def reserve(
        self, scope: str, scope_id: uuid.UUID, amount: float, *, job_id: str
    ):
        """Reserve ``amount``. Raises BudgetExceeded if a hard cap would break."""
        from chronocanvas.db.models.showrunner_cost import BudgetReservation

        budget = await self.get_or_create(scope, scope_id)
        check = evaluate(
            budget.limit_usd, budget.spent_usd, budget.reserved_usd, amount,
            soft_pct=budget.soft_pct, hard_behavior=budget.hard_behavior,
        )
        if check.outcome == "block":
            raise BudgetExceeded(check)
        budget.reserved_usd += amount
        reservation = BudgetReservation(
            budget_id=budget.id, amount_usd=amount, job_id=job_id, status="active",
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=RESERVATION_TTL_MIN),
        )
        self.session.add(reservation)
        await self.session.flush()
        return reservation, check

    async def commit(self, reservation_id: uuid.UUID, actual_usd: float):
        from chronocanvas.db.models.showrunner_cost import Budget, BudgetReservation

        res = await self.session.get(BudgetReservation, reservation_id)
        if res is None or res.status != "active":
            return
        budget = await self.session.get(Budget, res.budget_id)
        budget.reserved_usd = max(0.0, budget.reserved_usd - res.amount_usd)
        budget.spent_usd += actual_usd
        res.status = "committed"
        res.committed_usd = actual_usd
        await self.session.flush()

    async def release(self, reservation_id: uuid.UUID):
        from chronocanvas.db.models.showrunner_cost import Budget, BudgetReservation

        res = await self.session.get(BudgetReservation, reservation_id)
        if res is None or res.status != "active":
            return
        budget = await self.session.get(Budget, res.budget_id)
        budget.reserved_usd = max(0.0, budget.reserved_usd - res.amount_usd)
        res.status = "released"
        await self.session.flush()

    async def expire_stale(self, now: datetime | None = None) -> int:
        """Release reservations past their TTL (crash-safety). Returns count."""
        from chronocanvas.db.models.showrunner_cost import Budget, BudgetReservation

        now = now or datetime.now(timezone.utc)
        rows = await self.session.execute(
            select(BudgetReservation).where(
                BudgetReservation.status == "active", BudgetReservation.expires_at < now
            )
        )
        count = 0
        for res in rows.scalars().all():
            budget = await self.session.get(Budget, res.budget_id)
            budget.reserved_usd = max(0.0, budget.reserved_usd - res.amount_usd)
            res.status = "expired"
            count += 1
        await self.session.flush()
        return count
