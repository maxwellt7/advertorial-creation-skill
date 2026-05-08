from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel


ChunkType = Literal[
    "hook_headline",
    "voice_example",
    "structural_beat",
    "proof_block",
    "image_prompt",
    "cta_pattern",
    "fb_hook",
    "fb_headline",
    "fb_primary_text",
    "fb_image_prompt",
    "fb_voice_example",
    "fb_bridge",
]


class ChunkMetadata(BaseModel):
    niche: str | None = None
    rank: int | None = None
    voice_archetype: str | None = None
    source_file: str
    chunk_type: ChunkType
    source_corpus: Literal["advertorial", "fb_ad"]


class Chunk(BaseModel):
    text: str
    chunk_type: ChunkType
    metadata: ChunkMetadata


def _load_yaml_frontmatter(path: Path) -> dict:
    """Pull the YAML block delimited by --- markers at top of the markdown file."""
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    return yaml.safe_load(text[3:end]) or {}


def parse_advertorial(path: Path) -> list[Chunk]:
    data = _load_yaml_frontmatter(path)
    chunks: list[Chunk] = []

    def meta(chunk_type: ChunkType) -> ChunkMetadata:
        return ChunkMetadata(
            niche=data.get("niche"),
            rank=data.get("rank"),
            source_file=path.name,
            chunk_type=chunk_type,
            source_corpus="advertorial",
        )

    if hook := data.get("hook_headline"):
        chunks.append(Chunk(text=hook, chunk_type="hook_headline", metadata=meta("hook_headline")))

    voice = (data.get("voice_profile") or {}).get("example_sentences") or []
    for sentence in voice:
        if sentence:
            chunks.append(Chunk(text=sentence, chunk_type="voice_example", metadata=meta("voice_example")))

    for beat in data.get("structural_beats") or []:
        beat_text = f"{beat.get('beat', '')}: {beat.get('verbatim', '')}".strip(": ")
        if beat_text:
            chunks.append(Chunk(text=beat_text, chunk_type="structural_beat", metadata=meta("structural_beat")))

    for image in data.get("images") or []:
        prompt = image.get("reverse_engineered_prompt")
        if prompt:
            chunks.append(Chunk(text=prompt, chunk_type="image_prompt", metadata=meta("image_prompt")))

    cta = (data.get("conversion_psychology") or {}).get("cta_strategy")
    if cta:
        chunks.append(Chunk(text=cta, chunk_type="cta_pattern", metadata=meta("cta_pattern")))

    return chunks
