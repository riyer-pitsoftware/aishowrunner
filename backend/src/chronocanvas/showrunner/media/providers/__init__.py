"""Concrete media generation providers (TRD §9.2).

- ``mock``  — deterministic offline/CI providers that write tiny placeholder files.
- ``wan``   — Alibaba Wan text-to-image / text-to-video via DashScope async tasks.
- ``dashscope_tts`` — CosyVoice / Qwen-TTS narration via DashScope.

Selection happens in ``media.registry`` based on whether a DashScope key is set.
"""

from __future__ import annotations

from chronocanvas.showrunner.media.providers.dashscope_tts import DashScopeTTSProvider
from chronocanvas.showrunner.media.providers.mock import (
    MockImageProvider,
    MockTTSProvider,
    MockVideoProvider,
)
from chronocanvas.showrunner.media.providers.wan import WanImageProvider, WanVideoProvider

__all__ = [
    "MockImageProvider",
    "MockVideoProvider",
    "MockTTSProvider",
    "WanImageProvider",
    "WanVideoProvider",
    "DashScopeTTSProvider",
]
