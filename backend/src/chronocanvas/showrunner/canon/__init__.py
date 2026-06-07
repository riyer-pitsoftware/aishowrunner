"""Canon: append-only mutation log + fold to current state (TRD §10)."""

from chronocanvas.showrunner.canon.immutability import (
    ImmutableRecordError,
    install_canon_guards,
)
from chronocanvas.showrunner.canon.state import (
    CanonState,
    MutationType,
    apply_mutation,
    fold,
)

__all__ = [
    "CanonState", "MutationType", "apply_mutation", "fold",
    "ImmutableRecordError", "install_canon_guards",
]
