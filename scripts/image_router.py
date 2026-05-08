from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

KNOWN_SECTION_TYPES = {
    "hero", "intro", "numbered_reason", "proof_quote", "before_after",
    "expert_quote", "comparison_table", "mechanism_explainer",
    "lifestyle_routine", "cta_button", "risk_reversal", "final_verdict", "faq",
}

_ROUTING: dict[str, dict[str, str]] = {
    "hero": {"provider": "fal", "model": "flux-pro-1.1"},
    "numbered_reason": {"provider": "fal", "model": "flux-pro-1.1"},
    "before_after": {"provider": "fal", "model": "flux-pro-1.1"},
    "expert_quote": {"provider": "fal", "model": "flux-pro-1.1"},
    "lifestyle_routine": {"provider": "fal", "model": "flux-pro-1.1"},
    "mechanism_explainer": {"provider": "openai", "model": "gpt-image-1"},
    "proof_quote": {"provider": "fal", "model": "ideogram-v2"},
    "comparison_table": {"provider": "fal", "model": "ideogram-v2"},
}


class RouteDecision(BaseModel):
    provider: Literal["fal", "openai"]
    model: str


def route(section_type: str) -> RouteDecision | None:
    if section_type not in KNOWN_SECTION_TYPES:
        raise ValueError(f"Unknown section_type: {section_type}")
    cfg = _ROUTING.get(section_type)
    if cfg is None:
        return None
    return RouteDecision(provider=cfg["provider"], model=cfg["model"])  # type: ignore[arg-type]
