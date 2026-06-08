"""Media provider contracts (TRD §7.1, §9.2).

Generation providers return a ``MediaArtifact`` describing the produced file plus
the billable ``units`` used (images, video seconds, or 1k-char blocks for TTS).
Cost is *not* computed here — the produce/regenerate services price ``units``
through ``chronocanvas.showrunner.cost.pricing.media_cost`` so pricing stays a
single source of truth.

Providers are resolved via ``media.registry`` so the Alibaba/Qwen implementations
(Wan, CosyVoice/Qwen-TTS) can be swapped for deterministic mocks when no
DashScope key is configured (local dev, CI, offline demo).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pydantic import BaseModel, Field


class MediaArtifact(BaseModel):
    """Output of one generation call."""

    kind: str  # image|video|tts
    url: str  # served path ("/output/...") or remote uri
    mime_type: str
    units: float = 0.0  # images | video seconds | char count (priced per_1k_chars)
    provider: str = ""
    model: str | None = None
    width: int | None = None
    height: int | None = None
    duration_ms: float = 0.0
    meta: dict = Field(default_factory=dict)


@runtime_checkable
class ImageProvider(Protocol):
    name: str

    async def generate_image(
        self, prompt: str, *, output_dir: str, width: int = 1080, height: int = 1920, **kwargs
    ) -> MediaArtifact: ...

    async def is_available(self) -> bool: ...


@runtime_checkable
class VideoProvider(Protocol):
    name: str

    async def generate_video(
        self,
        prompt: str,
        *,
        output_dir: str,
        seconds: float = 8.0,
        image_url: str | None = None,
        width: int = 1080,
        height: int = 1920,
        **kwargs,
    ) -> MediaArtifact: ...

    async def is_available(self) -> bool: ...


@runtime_checkable
class TTSProvider(Protocol):
    name: str

    async def synthesize(
        self, text: str, *, output_dir: str, voice: str | None = None, **kwargs
    ) -> MediaArtifact: ...

    async def is_available(self) -> bool: ...
