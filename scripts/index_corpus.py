"""One-shot indexer: parse all advertorial + fb_ad markdown files,
embed each chunk via OpenAI, upsert to Pinecone."""
from __future__ import annotations

import os
import sys
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone, ServerlessSpec

from scripts.corpus_chunker import Chunk, parse_advertorial, parse_fb_ad

# Load env early so EMBED_DIM picks up any custom value from .env
load_dotenv()

EMBED_MODEL = "text-embedding-3-large"
EMBED_DIM = int(os.environ.get("EMBEDDING_DIMENSIONS", "2048"))
BATCH = 96


def _embed_batch(client: OpenAI, texts: list[str]) -> list[list[float]]:
    resp = client.embeddings.create(model=EMBED_MODEL, input=texts, dimensions=EMBED_DIM)
    return [d.embedding for d in resp.data]


def _ensure_index(pc: Pinecone, name: str, region: str) -> None:
    existing = {idx.name for idx in pc.list_indexes()}
    if name not in existing:
        pc.create_index(
            name=name,
            dimension=EMBED_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region=region),
        )
        while not pc.describe_index(name).status.get("ready"):
            time.sleep(2)


def _gather_chunks(corpus_path: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    advertorials = sorted((corpus_path / "advertorials").glob("*.md"))
    fb_ads = sorted((corpus_path / "facebook_ads").glob("*.md"))
    for p in advertorials:
        try:
            chunks.extend(parse_advertorial(p))
        except Exception as e:
            print(f"  WARN: skipped {p.name}: {e}", file=sys.stderr)
    for p in fb_ads:
        try:
            chunks.extend(parse_fb_ad(p))
        except Exception as e:
            print(f"  WARN: skipped {p.name}: {e}", file=sys.stderr)
    return chunks


def main() -> int:
    corpus_path = Path(os.environ["ADVERTORIAL_CORPUS_PATH"])
    index_name = os.environ.get("PINECONE_INDEX_NAME", "advertorial-corpus")
    region = os.environ.get("PINECONE_ENVIRONMENT", "us-east-1")

    print(f"Gathering chunks from {corpus_path}...")
    chunks = _gather_chunks(corpus_path)
    print(f"  {len(chunks)} chunks gathered")

    pc = Pinecone(api_key=os.environ["PINECONE_API_KEY"])
    _ensure_index(pc, index_name, region)
    index = pc.Index(index_name)
    openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    for i in range(0, len(chunks), BATCH):
        batch = chunks[i:i + BATCH]
        texts = [c.text for c in batch]
        vectors = _embed_batch(openai, texts)
        records = [
            {
                "id": str(uuid.uuid4()),
                "values": vec,
                "metadata": {
                    "text": c.text,
                    **{k: v for k, v in c.metadata.model_dump().items() if v is not None},
                },
            }
            for c, vec in zip(batch, vectors)
        ]
        index.upsert(vectors=records)
        print(f"  upserted {i + len(batch)}/{len(chunks)}")

    print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
