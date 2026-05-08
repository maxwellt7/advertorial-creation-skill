from __future__ import annotations

import re
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


def _extract_scalar_fields(text: str) -> dict:
    """Lenient line-by-line extraction of top-level scalar fields.
    Used as a fallback when yaml.safe_load fails on malformed corpus YAML
    (unquoted colons, unterminated quotes, weird tags, etc.).
    Captures only flat key:value pairs at the document root — nested
    structures (voice_profile, structural_beats, images) are lost for
    files that fall through to this path.
    """
    out: dict = {}
    for line in text.splitlines():
        # Skip blanks, indented (nested), comments, list items
        if not line or line[0] in (" ", "\t", "#", "-"):
            continue
        m = re.match(r"^(\w+):\s*(.*)$", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2).rstrip()
        if not val:
            continue
        # Strip surrounding quotes if balanced
        if len(val) >= 2 and (
            (val[0] == '"' and val[-1] == '"')
            or (val[0] == "'" and val[-1] == "'")
        ):
            val = val[1:-1]
        out[key] = val
    return out


def _load_yaml_frontmatter(path: Path) -> dict:
    """Pull the YAML block delimited by --- markers at top of the markdown file.
    On YAML parse failure, falls back to lenient line-based scalar extraction."""
    text = path.read_text()
    if not text.startswith("---"):
        return {}
    end = text.find("---", 3)
    if end == -1:
        return {}
    body = text[3:end]
    try:
        loaded = yaml.safe_load(body)
        if isinstance(loaded, dict):
            return loaded
        return {}
    except yaml.YAMLError:
        return _extract_scalar_fields(body)


def _is_str(v) -> bool:
    return isinstance(v, str) and v.strip() != ""


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

    hook = data.get("hook_headline")
    if _is_str(hook):
        chunks.append(Chunk(text=hook, chunk_type="hook_headline", metadata=meta("hook_headline")))

    voice_profile = data.get("voice_profile")
    voice = (voice_profile or {}).get("example_sentences") if isinstance(voice_profile, dict) else []
    for sentence in voice or []:
        if _is_str(sentence):
            chunks.append(Chunk(text=sentence, chunk_type="voice_example", metadata=meta("voice_example")))

    for beat in data.get("structural_beats") or []:
        if not isinstance(beat, dict):
            continue
        beat_text = f"{beat.get('beat', '')}: {beat.get('verbatim', '')}".strip(": ")
        if beat_text:
            chunks.append(Chunk(text=beat_text, chunk_type="structural_beat", metadata=meta("structural_beat")))

    for image in data.get("images") or []:
        if not isinstance(image, dict):
            continue
        prompt = image.get("reverse_engineered_prompt")
        if _is_str(prompt):
            chunks.append(Chunk(text=prompt, chunk_type="image_prompt", metadata=meta("image_prompt")))

    conversion = data.get("conversion_psychology")
    cta = conversion.get("cta_strategy") if isinstance(conversion, dict) else None
    if _is_str(cta):
        chunks.append(Chunk(text=cta, chunk_type="cta_pattern", metadata=meta("cta_pattern")))

    return chunks


def parse_fb_ad(path: Path) -> list[Chunk]:
    data = _load_yaml_frontmatter(path)
    chunks: list[Chunk] = []

    def meta(chunk_type: ChunkType) -> ChunkMetadata:
        return ChunkMetadata(
            source_file=path.name,
            chunk_type=chunk_type,
            source_corpus="fb_ad",
        )

    hook = data.get("primary_hook")
    if _is_str(hook):
        chunks.append(Chunk(text=hook, chunk_type="fb_hook", metadata=meta("fb_hook")))

    copy = data.get("copy") if isinstance(data.get("copy"), dict) else {}
    headline = copy.get("headline")
    if _is_str(headline):
        chunks.append(Chunk(text=headline, chunk_type="fb_headline", metadata=meta("fb_headline")))
    primary = copy.get("primary_text")
    if _is_str(primary):
        chunks.append(Chunk(text=primary, chunk_type="fb_primary_text", metadata=meta("fb_primary_text")))

    img = data.get("reverse_engineered_image_prompt")
    if _is_str(img):
        chunks.append(Chunk(text=img, chunk_type="fb_image_prompt", metadata=meta("fb_image_prompt")))

    voice_profile = data.get("voice_profile")
    voice = (voice_profile or {}).get("example_sentences") if isinstance(voice_profile, dict) else []
    for sentence in voice or []:
        if _is_str(sentence):
            chunks.append(Chunk(text=sentence, chunk_type="fb_voice_example", metadata=meta("fb_voice_example")))

    bridge = data.get("hook_to_advertorial_bridge")
    if _is_str(bridge):
        chunks.append(Chunk(text=bridge, chunk_type="fb_bridge", metadata=meta("fb_bridge")))

    return chunks
