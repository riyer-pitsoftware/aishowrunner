"""CosyVoice / Qwen-TTS narration via DashScope (TRD §9.2).

Synthesizes speech from text using DashScope's audio synthesis service and saves
a WAV under ``output_dir``, returning a served ``/output/<file>`` URL. ``units``
is the character count (priced per 1k chars by the cost layer).

Endpoint path and request shape are kept in clearly-marked constants — exact
pricing and endpoint verification land in Sprint 7 (asr-av5).
"""

from __future__ import annotations

import uuid
from pathlib import Path

import httpx

from chronocanvas.config import settings
from chronocanvas.showrunner.media.base import MediaArtifact

_PROVIDER = "dashscope-tts"

# DashScope audio synthesis endpoint. <verify against live DashScope docs> (asr-av5)
_TTS_PATH = "/services/aigc/text2speech/speech-synthesis"  # <verify against live DashScope docs>
_HTTP_TIMEOUT_S = 60.0


class TTSError(RuntimeError):
    """Raised when DashScope TTS fails or the API is unreachable."""


def _headers() -> dict[str, str]:
    if not settings.dashscope_api_key:
        raise TTSError("dashscope_api_key is not configured")
    return {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }


class DashScopeTTSProvider:
    name = _PROVIDER

    def __init__(self) -> None:
        self.model = settings.tts_provider_model
        self.voice = settings.tts_provider_voice

    async def is_available(self) -> bool:
        return bool(settings.dashscope_api_key)

    async def synthesize(
        self, text: str, *, output_dir: str, voice: str | None = None, **kwargs
    ) -> MediaArtifact:
        chosen_voice = voice or settings.tts_provider_voice
        # CosyVoice/Qwen-TTS request shape. <verify against live DashScope docs>
        payload = {
            "model": settings.tts_provider_model,
            "input": {"text": text},
            "parameters": {"voice": chosen_voice, "format": "wav"},
        }
        async with httpx.AsyncClient(
            base_url=settings.dashscope_base_url, timeout=_HTTP_TIMEOUT_S
        ) as client:
            try:
                resp = await client.post(_TTS_PATH, json=payload, headers=_headers())
                resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise TTSError(f"DashScope TTS request failed: {exc}") from exc

            audio_url = resp.json().get("output", {}).get("audio_url")
            if not audio_url:
                raise TTSError(f"DashScope TTS returned no audio_url: {resp.text}")

            try:
                audio_resp = await client.get(audio_url, headers={})
                audio_resp.raise_for_status()
            except httpx.HTTPError as exc:
                raise TTSError(f"DashScope TTS audio download failed: {exc}") from exc

            out = Path(output_dir)
            out.mkdir(parents=True, exist_ok=True)
            filename = f"{uuid.uuid4().hex}.wav"
            (out / filename).write_bytes(audio_resp.content)
            url = f"/output/{filename}"

        return MediaArtifact(
            kind="tts",
            url=url,
            mime_type="audio/wav",
            units=float(len(text)),
            provider=_PROVIDER,
            model=settings.tts_provider_model,
            meta={"text": text, "voice": chosen_voice},
        )
