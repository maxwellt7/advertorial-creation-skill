from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import fal_client
import httpx
from openai import OpenAI


@dataclass
class GenResult:
    path: Path
    provider: Literal["fal", "openai"]
    model: str


def _save_url(url: str, dest: Path) -> Path:
    with httpx.stream("GET", url, timeout=120.0, follow_redirects=True) as r:
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return dest


def gen_flux(prompt: str, dest: Path, aspect_ratio: str = "4:3") -> GenResult:
    """Flux Pro 1.1 via fal."""
    handler = fal_client.submit(
        "fal-ai/flux-pro/v1.1",
        arguments={"prompt": prompt, "aspect_ratio": aspect_ratio, "num_images": 1},
    )
    out = handler.get()
    url = out["images"][0]["url"]
    _save_url(url, dest)
    return GenResult(path=dest, provider="fal", model="flux-pro-1.1")


def gen_ideogram(prompt: str, dest: Path, aspect_ratio: str = "1:1") -> GenResult:
    """Ideogram v2 via fal — best for text-in-image."""
    handler = fal_client.submit(
        "fal-ai/ideogram/v2",
        arguments={"prompt": prompt, "aspect_ratio": aspect_ratio, "style": "design"},
    )
    out = handler.get()
    url = out["images"][0]["url"]
    _save_url(url, dest)
    return GenResult(path=dest, provider="fal", model="ideogram-v2")


def gen_openai_image(prompt: str, dest: Path, size: str = "1024x1024") -> GenResult:
    """gpt-image-1 — best for diagrams and infographics."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    resp = client.images.generate(model="gpt-image-1", prompt=prompt, size=size, n=1)
    b64 = resp.data[0].b64_json
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(base64.b64decode(b64))
    return GenResult(path=dest, provider="openai", model="gpt-image-1")


def generate(provider: str, model: str, prompt: str, dest: Path, aspect_ratio: str = "4:3") -> GenResult:
    """Single dispatch entrypoint used by the orchestrator."""
    if provider == "fal" and model == "flux-pro-1.1":
        return gen_flux(prompt, dest, aspect_ratio)
    if provider == "fal" and model == "ideogram-v2":
        return gen_ideogram(prompt, dest, aspect_ratio)
    if provider == "openai" and model == "gpt-image-1":
        size_map = {"4:3": "1536x1024", "1:1": "1024x1024", "16:9": "1536x1024"}
        return gen_openai_image(prompt, dest, size=size_map.get(aspect_ratio, "1024x1024"))
    raise ValueError(f"Unsupported provider/model: {provider}/{model}")
