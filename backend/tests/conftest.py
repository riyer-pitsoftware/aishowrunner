"""Pytest bootstrap — load test env defaults before app config is imported.

Keeps DATABASE_URL / SECRET_KEY (and other test toggles) out of the pytest
invocation: values live in ``backend/.env.test`` (non-secret, test-only). This
runs at collection start, before ``chronocanvas.config`` instantiates its
``Settings`` singleton, so a bare ``pytest`` works with no inline env vars.
"""

from __future__ import annotations

import os
from pathlib import Path

_ENV_TEST = Path(__file__).resolve().parents[1] / ".env.test"

if _ENV_TEST.is_file():
    for _line in _ENV_TEST.read_text().splitlines():
        _line = _line.strip()
        if not _line or _line.startswith("#") or "=" not in _line:
            continue
        _key, _, _val = _line.partition("=")
        # setdefault: a real env var (CI / shell) always wins over the file.
        os.environ.setdefault(_key.strip(), _val.strip())
