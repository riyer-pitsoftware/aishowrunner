"""Alibaba Wan media providers via DashScope (TRD §9.2).

Wan uses DashScope's *async task* pattern: POST a task (with the
``X-DashScope-Async: enable`` header), receive a ``task_id``, poll the task GET
endpoint until status is ``SUCCEEDED``, then download the produced asset and save
it under ``output_dir``. We return a served ``/output/<file>`` URL so the rest of
the media DAG treats Wan output identically to the mock provider.

Endpoint paths and request shapes are kept in clearly-marked constants — exact
pricing and endpoint verification land in Sprint 7 (asr-av5).
"""

from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

import httpx

from chronocanvas.config import settings
from chronocanvas.showrunner.media.base import MediaArtifact

_PROVIDER = "wan"

# DashScope endpoints. <verify against live DashScope docs> (asr-av5, Sprint 7)
_T2I_PATH = "/services/aigc/text2image/image-synthesis"  # <verify against live DashScope docs>
_T2V_PATH = "/services/aigc/video-generation/video-synthesis"  # <verify against live DashScope docs>
_TASK_PATH = "/tasks/{task_id}"  # <verify against live DashScope docs>

# Task polling tuning.
_POLL_INTERVAL_S = 3.0
_POLL_TIMEOUT_S = 600.0
_HTTP_TIMEOUT_S = 60.0


class WanError(RuntimeError):
    """Raised when a Wan/DashScope task fails or the API is unreachable."""


def _headers(*, async_enable: bool = False) -> dict[str, str]:
    if not settings.dashscope_api_key:
        raise WanError("dashscope_api_key is not configured")
    headers = {
        "Authorization": f"Bearer {settings.dashscope_api_key}",
        "Content-Type": "application/json",
    }
    if async_enable:
        headers["X-DashScope-Async"] = "enable"
    return headers


async def _create_task(client: httpx.AsyncClient, path: str, payload: dict) -> str:
    """POST an async task and return its ``task_id``."""
    try:
        resp = await client.post(path, json=payload, headers=_headers(async_enable=True))
        resp.raise_for_status()
    except httpx.HTTPError as exc:  # network, timeout, non-2xx
        raise WanError(f"DashScope task create failed: {exc}") from exc
    body = resp.json()
    task_id = body.get("output", {}).get("task_id")
    if not task_id:
        raise WanError(f"DashScope task create returned no task_id: {body}")
    return task_id


async def _poll_task(client: httpx.AsyncClient, task_id: str) -> dict:
    """Poll the task until SUCCEEDED; return the ``output`` dict."""
    deadline = asyncio.get_event_loop().time() + _POLL_TIMEOUT_S
    path = _TASK_PATH.format(task_id=task_id)
    while True:
        try:
            resp = await client.get(path, headers=_headers())
            resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise WanError(f"DashScope task poll failed: {exc}") from exc
        body = resp.json()
        output = body.get("output", {})
        status = output.get("task_status")
        if status == "SUCCEEDED":
            return output
        if status in ("FAILED", "CANCELED", "UNKNOWN"):
            raise WanError(f"DashScope task {task_id} ended with status={status}: {body}")
        if asyncio.get_event_loop().time() > deadline:
            raise WanError(f"DashScope task {task_id} timed out after {_POLL_TIMEOUT_S}s")
        await asyncio.sleep(_POLL_INTERVAL_S)


async def _download(client: httpx.AsyncClient, url: str, output_dir: str, suffix: str) -> str:
    """Download a remote asset to a uuid-named file; return ``/output/<file>``."""
    try:
        resp = await client.get(url, headers={}, timeout=_HTTP_TIMEOUT_S)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise WanError(f"DashScope asset download failed: {exc}") from exc
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    (out / filename).write_bytes(resp.content)
    return f"/output/{filename}"


def _first_result_url(output: dict) -> str:
    """Extract the produced asset URL from a SUCCEEDED task output."""
    # Image tasks return output.results[].url; video tasks return output.video_url.
    results = output.get("results")
    if results:
        url = results[0].get("url")
        if url:
            return url
    video_url = output.get("video_url")
    if video_url:
        return video_url
    raise WanError(f"DashScope task output had no asset url: {output}")


class WanImageProvider:
    name = _PROVIDER

    def __init__(self) -> None:
        self.model = settings.wan_image_model

    async def is_available(self) -> bool:
        return bool(settings.dashscope_api_key)

    async def generate_image(
        self, prompt: str, *, output_dir: str, width: int = 1080, height: int = 1920, **kwargs
    ) -> MediaArtifact:
        # DashScope expects size as "WIDTH*HEIGHT". <verify against live DashScope docs>
        payload = {
            "model": settings.wan_image_model,
            "input": {"prompt": prompt},
            "parameters": {"size": f"{width}*{height}", "n": 1},
        }
        async with httpx.AsyncClient(
            base_url=settings.dashscope_base_url, timeout=_HTTP_TIMEOUT_S
        ) as client:
            task_id = await _create_task(client, _T2I_PATH, payload)
            output = await _poll_task(client, task_id)
            url = await _download(client, _first_result_url(output), output_dir, ".png")
        return MediaArtifact(
            kind="image",
            url=url,
            mime_type="image/png",
            units=1.0,
            provider=_PROVIDER,
            model=settings.wan_image_model,
            width=width,
            height=height,
            meta={"prompt": prompt, "task_id": task_id},
        )


class WanVideoProvider:
    name = _PROVIDER

    def __init__(self) -> None:
        self.model = settings.wan_video_model

    async def is_available(self) -> bool:
        return bool(settings.dashscope_api_key)

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
        # image_url present → image-to-video; otherwise text-to-video.
        # <verify against live DashScope docs>
        wan_input: dict = {"prompt": prompt}
        if image_url:
            wan_input["img_url"] = image_url
        payload = {
            "model": settings.wan_video_model,
            "input": wan_input,
            "parameters": {"size": f"{width}*{height}", "duration": int(seconds)},
        }
        async with httpx.AsyncClient(
            base_url=settings.dashscope_base_url, timeout=_HTTP_TIMEOUT_S
        ) as client:
            task_id = await _create_task(client, _T2V_PATH, payload)
            output = await _poll_task(client, task_id)
            url = await _download(client, _first_result_url(output), output_dir, ".mp4")
        return MediaArtifact(
            kind="video",
            url=url,
            mime_type="video/mp4",
            units=float(seconds),
            provider=_PROVIDER,
            model=settings.wan_video_model,
            width=width,
            height=height,
            duration_ms=float(seconds) * 1000.0,
            meta={"prompt": prompt, "image_url": image_url, "task_id": task_id},
        )
