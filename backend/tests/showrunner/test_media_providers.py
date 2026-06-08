"""Media provider tests (asr-2in.6) — mock providers + registry resolution.

Only the deterministic mock providers touch the filesystem here; no network is
made. Registry selection is verified by monkeypatching the DashScope key.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from chronocanvas.config import settings
from chronocanvas.showrunner.media import registry
from chronocanvas.showrunner.media.base import MediaArtifact
from chronocanvas.showrunner.media.providers.dashscope_tts import DashScopeTTSProvider
from chronocanvas.showrunner.media.providers.mock import (
    MockImageProvider,
    MockTTSProvider,
    MockVideoProvider,
)
from chronocanvas.showrunner.media.providers.wan import WanImageProvider, WanVideoProvider


def _written_file(artifact: MediaArtifact, output_dir: str) -> Path:
    assert artifact.url.startswith("/output/")
    path = Path(output_dir) / artifact.url.removeprefix("/output/")
    assert path.is_file(), f"expected file written at {path}"
    assert path.stat().st_size > 0
    return path


# ── Mock providers (no network) ──────────────────────────────────────────────

async def test_mock_image(tmp_path):
    artifact = await MockImageProvider().generate_image(
        "a temple at dawn", output_dir=str(tmp_path), width=1080, height=1920
    )
    assert artifact.kind == "image"
    assert artifact.mime_type == "image/png"
    assert artifact.units == 1.0
    assert artifact.provider == "mock"
    assert (artifact.width, artifact.height) == (1080, 1920)
    path = _written_file(artifact, str(tmp_path))
    assert path.read_bytes().startswith(b"\x89PNG")


async def test_mock_video(tmp_path):
    artifact = await MockVideoProvider().generate_video(
        "pan across the courtyard", output_dir=str(tmp_path), seconds=6.0
    )
    assert artifact.kind == "video"
    assert artifact.mime_type == "video/mp4"
    assert artifact.units == 6.0
    assert artifact.duration_ms == 6000.0
    assert artifact.provider == "mock"
    _written_file(artifact, str(tmp_path))


async def test_mock_tts(tmp_path):
    text = "Once upon a time in the Chola kingdom."
    artifact = await MockTTSProvider().synthesize(text, output_dir=str(tmp_path), voice="longxiaochun")
    assert artifact.kind == "tts"
    assert artifact.mime_type == "audio/wav"
    assert artifact.units == float(len(text))
    assert artifact.provider == "mock"
    path = _written_file(artifact, str(tmp_path))
    assert path.read_bytes().startswith(b"RIFF")


async def test_mock_filenames_unique(tmp_path):
    p = MockImageProvider()
    a = await p.generate_image("x", output_dir=str(tmp_path))
    b = await p.generate_image("x", output_dir=str(tmp_path))
    assert a.url != b.url


async def test_mock_always_available():
    assert await MockImageProvider().is_available() is True
    assert await MockVideoProvider().is_available() is True
    assert await MockTTSProvider().is_available() is True


# ── Registry resolution ──────────────────────────────────────────────────────

def test_registry_returns_mock_without_key(monkeypatch):
    monkeypatch.setattr(settings, "dashscope_api_key", "")
    assert isinstance(registry.get_image_provider(), MockImageProvider)
    assert isinstance(registry.get_video_provider(), MockVideoProvider)
    assert isinstance(registry.get_tts_provider(), MockTTSProvider)


def test_registry_returns_dashscope_with_key(monkeypatch):
    monkeypatch.setattr(settings, "dashscope_api_key", "sk-test-key")
    assert isinstance(registry.get_image_provider(), WanImageProvider)
    assert isinstance(registry.get_video_provider(), WanVideoProvider)
    assert isinstance(registry.get_tts_provider(), DashScopeTTSProvider)


async def test_dashscope_availability_tracks_key(monkeypatch):
    monkeypatch.setattr(settings, "dashscope_api_key", "")
    assert await WanImageProvider().is_available() is False
    monkeypatch.setattr(settings, "dashscope_api_key", "sk-test-key")
    assert await WanVideoProvider().is_available() is True
    assert await DashScopeTTSProvider().is_available() is True
