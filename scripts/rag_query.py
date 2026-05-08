from __future__ import annotations

import os
from functools import lru_cache
from typing import Sequence

from openai import OpenAI
from pinecone import Pinecone
from pydantic import BaseModel

EMBED_MODEL = "text-embedding-3-large"


class RagResult(BaseModel):
    text: str
    score: float
    chunk_type: str
    niche: str | None = None
    source_corpus: str | None = None
    source_file: str | None = None


@lru_cache(maxsize=1)
def _get_index():
    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    return pc.Index(os.environ.get("PINECONE_INDEX_NAME", "advertorial-corpus"))


@lru_cache(maxsize=1)
def _get_openai() -> OpenAI:
    return OpenAI(api_key=os.environ["OPENAI_API_KEY"])


def _embed(text: str) -> list[float]:
    client = _get_openai()
    resp = client.embeddings.create(model=EMBED_MODEL, input=[text])
    return resp.data[0].embedding


def _build_filter(
    chunk_types: Sequence[str] | None,
    niche: str | None,
    voice_archetype: str | None,
    source_corpus: str | None,
) -> dict | None:
    f: dict = {}
    if chunk_types:
        f["chunk_type"] = {"$in": list(chunk_types)}
    if niche:
        f["niche"] = {"$eq": niche}
    if voice_archetype:
        f["voice_archetype"] = {"$eq": voice_archetype}
    if source_corpus:
        f["source_corpus"] = {"$eq": source_corpus}
    return f or None


def query(
    text: str,
    chunk_types: Sequence[str] | None = None,
    niche: str | None = None,
    voice_archetype: str | None = None,
    source_corpus: str | None = None,
    top_k: int = 5,
) -> list[RagResult]:
    vec = _embed(text)
    index = _get_index()
    kwargs: dict = {"vector": vec, "top_k": top_k, "include_metadata": True}
    f = _build_filter(chunk_types, niche, voice_archetype, source_corpus)
    if f:
        kwargs["filter"] = f
    resp = index.query(**kwargs)
    return [
        RagResult(
            text=m.metadata.get("text", ""),
            score=float(m.score),
            chunk_type=m.metadata.get("chunk_type", ""),
            niche=m.metadata.get("niche"),
            source_corpus=m.metadata.get("source_corpus"),
            source_file=m.metadata.get("source_file"),
        )
        for m in resp.matches
    ]
