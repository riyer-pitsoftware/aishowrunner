"""Media provider registry (TRD §9.2).

Resolves the concrete provider for each media kind lazily from settings at call
time: the DashScope-backed Alibaba/Qwen providers (Wan, CosyVoice/Qwen-TTS) when
``settings.dashscope_api_key`` is set, otherwise the deterministic mock providers
so the full media DAG runs offline / in CI.

``produce.py`` and ``regenerate.py`` import the three getters below.
"""

from __future__ import annotations

from chronocanvas.config import settings
from chronocanvas.showrunner.media.base import ImageProvider, TTSProvider, VideoProvider
from chronocanvas.showrunner.media.providers.dashscope_tts import DashScopeTTSProvider
from chronocanvas.showrunner.media.providers.mock import (
    MockImageProvider,
    MockTTSProvider,
    MockVideoProvider,
)
from chronocanvas.showrunner.media.providers.wan import WanImageProvider, WanVideoProvider


def _dashscope_enabled() -> bool:
    return bool(settings.dashscope_api_key)


def get_image_provider() -> ImageProvider:
    if _dashscope_enabled():
        return WanImageProvider()
    return MockImageProvider()


def get_video_provider() -> VideoProvider:
    if _dashscope_enabled():
        return WanVideoProvider()
    return MockVideoProvider()


def get_tts_provider() -> TTSProvider:
    if _dashscope_enabled():
        return DashScopeTTSProvider()
    return MockTTSProvider()
