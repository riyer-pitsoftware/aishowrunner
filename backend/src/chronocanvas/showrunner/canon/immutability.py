"""Append-only immutability guards (TRD §10.2, §8.3).

CanonMutation and ApprovalGate are never updated or deleted. A selected
AudienceChoice (a committed decision) cannot be unset or deleted. We enforce this
at the ORM layer with SQLAlchemy mapper events so a stray UPDATE/DELETE fails
loudly rather than silently rewriting provenance.
"""

from __future__ import annotations

from sqlalchemy import event
from sqlalchemy.orm import Session


class ImmutableRecordError(RuntimeError):
    """Raised when code attempts to rewrite an append-only / committed record."""


def _block_update(mapper, connection, target) -> None:  # noqa: ANN001
    raise ImmutableRecordError(
        f"{type(target).__name__} is append-only and cannot be updated "
        f"(id={getattr(target, 'id', None)})."
    )


def _block_delete(mapper, connection, target) -> None:  # noqa: ANN001
    raise ImmutableRecordError(
        f"{type(target).__name__} is append-only and cannot be deleted "
        f"(id={getattr(target, 'id', None)})."
    )


def _block_committed_choice_update(mapper, connection, target) -> None:  # noqa: ANN001
    # An AudienceChoice may be updated until it is selected; once selected the
    # decision is canon and frozen.
    state = target.__dict__
    hist = getattr(target, "_sa_instance_state", None)
    was_selected = False
    if hist is not None:
        committed = hist.committed_state.get("selected")
        was_selected = bool(committed)
    if was_selected:
        raise ImmutableRecordError(
            "A selected AudienceChoice is a committed decision and cannot be changed."
        )
    _ = state  # keep linters calm


def install_canon_guards() -> None:
    """Idempotently attach immutability listeners. Call once at startup."""
    from chronocanvas.db.models.showrunner_episode import AudienceChoice
    from chronocanvas.db.models.showrunner_room import ApprovalGate
    from chronocanvas.db.models.showrunner_series import CanonMutation

    for model in (CanonMutation, ApprovalGate):
        if not event.contains(model, "before_update", _block_update):
            event.listen(model, "before_update", _block_update)
        if not event.contains(model, "before_delete", _block_delete):
            event.listen(model, "before_delete", _block_delete)

    if not event.contains(AudienceChoice, "before_update", _block_committed_choice_update):
        event.listen(AudienceChoice, "before_update", _block_committed_choice_update)
    if not event.contains(AudienceChoice, "before_delete", _block_delete):
        event.listen(AudienceChoice, "before_delete", _block_delete)


def append_only_session_guard(session: Session) -> None:
    """Optional belt-and-suspenders: reject dirty/deleted append-only rows on flush."""
    from chronocanvas.db.models.showrunner_series import CanonMutation

    for obj in session.dirty:
        if isinstance(obj, CanonMutation) and session.is_modified(obj):
            raise ImmutableRecordError("CanonMutation rows are append-only.")
    for obj in session.deleted:
        if isinstance(obj, CanonMutation):
            raise ImmutableRecordError("CanonMutation rows cannot be deleted.")
