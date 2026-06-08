"""Deterministic offline media providers (TRD §9.2).

These write a tiny, real placeholder file into ``output_dir`` and return a served
URL of the form ``/output/<filename>``. They let the full media DAG run with no
DashScope key (local dev, CI, offline demo) while exercising the same
``MediaArtifact`` contract as the live Wan / CosyVoice providers.

``units`` follows the billing convention so cost estimation stays exercised:
image → 1.0, video → seconds, tts → character count (priced per 1k chars).
"""

from __future__ import annotations

import uuid
from pathlib import Path

from chronocanvas.showrunner.media.base import MediaArtifact

_PROVIDER = "mock"

# Smallest valid 1x1 PNG (8-byte signature + IHDR + IDAT + IEND). Decodes cleanly.
_PNG_1X1 = bytes(
    [
        0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # signature
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR length + type
        0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,  # width=1, height=1
        0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4,  # bit depth/color/etc + crc
        0x89,
        0x00, 0x00, 0x00, 0x0D, 0x49, 0x44, 0x41, 0x54,  # IDAT length + type
        0x78, 0x9C, 0x62, 0x00, 0x01, 0x00, 0x00, 0x05,  # zlib stream
        0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4,              # + crc
        0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E, 0x44,  # IEND length + type
        0xAE, 0x42, 0x60, 0x82,                          # crc
    ]
)

# Minimal MP4 ftyp box — enough for a recognizable .mp4 stub (not a playable stream).
_MP4_STUB = bytes(
    [0x00, 0x00, 0x00, 0x18, 0x66, 0x74, 0x79, 0x70]  # box size + "ftyp"
) + b"isom" + bytes([0x00, 0x00, 0x02, 0x00]) + b"isomiso2"


def _wav_stub(ms: int = 100) -> bytes:
    """A minimal, valid silent PCM WAV (mono, 8kHz, 16-bit)."""
    sample_rate = 8000
    n_samples = max(1, int(sample_rate * ms / 1000))
    data = b"\x00\x00" * n_samples
    block_align = 2
    byte_rate = sample_rate * block_align
    return (
        b"RIFF"
        + (36 + len(data)).to_bytes(4, "little")
        + b"WAVE"
        + b"fmt "
        + (16).to_bytes(4, "little")
        + (1).to_bytes(2, "little")  # PCM
        + (1).to_bytes(2, "little")  # mono
        + sample_rate.to_bytes(4, "little")
        + byte_rate.to_bytes(4, "little")
        + block_align.to_bytes(2, "little")
        + (16).to_bytes(2, "little")  # bits per sample
        + b"data"
        + len(data).to_bytes(4, "little")
        + data
    )


def _write(output_dir: str, suffix: str, payload: bytes) -> tuple[str, str]:
    """Write ``payload`` to a uuid-named file under ``output_dir``.

    Returns ``(filename, served_url)``.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    (out / filename).write_bytes(payload)
    return filename, f"/output/{filename}"


class MockImageProvider:
    name = _PROVIDER

    async def is_available(self) -> bool:
        return True

    async def generate_image(
        self, prompt: str, *, output_dir: str, width: int = 1080, height: int = 1920, **kwargs
    ) -> MediaArtifact:
        _, url = _write(output_dir, ".png", _PNG_1X1)
        return MediaArtifact(
            kind="image",
            url=url,
            mime_type="image/png",
            units=1.0,
            provider=_PROVIDER,
            model="mock-image",
            width=width,
            height=height,
            meta={"prompt": prompt, "mock": True},
        )


class MockVideoProvider:
    name = _PROVIDER

    async def is_available(self) -> bool:
        return True

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
    ) -> MediaArtifact:
        _, url = _write(output_dir, ".mp4", _MP4_STUB)
        return MediaArtifact(
            kind="video",
            url=url,
            mime_type="video/mp4",
            units=float(seconds),
            provider=_PROVIDER,
            model="mock-video",
            width=width,
            height=height,
            duration_ms=float(seconds) * 1000.0,
            meta={"prompt": prompt, "image_url": image_url, "mock": True},
        )


class MockTTSProvider:
    name = _PROVIDER

    async def is_available(self) -> bool:
        return True

    async def synthesize(
        self, text: str, *, output_dir: str, voice: str | None = None, **kwargs
    ) -> MediaArtifact:
        _, url = _write(output_dir, ".wav", _wav_stub())
        return MediaArtifact(
            kind="tts",
            url=url,
            mime_type="audio/wav",
            units=float(len(text)),
            provider=_PROVIDER,
            model="mock-tts",
            meta={"text": text, "voice": voice, "mock": True},
        )
