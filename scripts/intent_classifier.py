from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel

PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "intent-classifier.md"


class Intent(BaseModel):
    action: Literal[
        "approve", "regenerate", "swap_palette", "swap_archetype",
        "edit", "restart_phase", "unknown",
    ]
    target: str | None = None
    modifier_note: str | None = None


@lru_cache(maxsize=1)
def _get_anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def _render_prompt(user_text: str, phase: str) -> str:
    template = PROMPT_PATH.read_text()
    return template.replace("{phase}", phase).replace("{user_text}", user_text)


def classify(user_text: str, phase: str) -> Intent:
    client = _get_anthropic()
    prompt = _render_prompt(user_text, phase)
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    raw = resp.content[0].text.strip()
    data = json.loads(raw)
    return Intent.model_validate(data)
