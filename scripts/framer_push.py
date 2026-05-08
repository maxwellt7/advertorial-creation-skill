from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

VALID_SECTION_TYPES = {
    "hero", "intro", "numbered_reason", "proof_quote", "before_after",
    "expert_quote", "comparison_table", "mechanism_explainer",
    "lifestyle_routine", "cta_button", "risk_reversal", "final_verdict", "faq",
}


class SectionPayload(BaseModel):
    parent_slug: str
    order_index: int
    section_type: str
    heading: str = ""
    body: str = ""
    image_local_path: str | None = None
    cta_text: str | None = None
    cta_url: str | None = None
    design_emphasis: Literal["low", "normal", "high"] = "normal"

    @field_validator("section_type")
    @classmethod
    def _valid_type(cls, v: str) -> str:
        if v not in VALID_SECTION_TYPES:
            raise ValueError(f"Invalid section_type: {v}")
        return v


class ParentPayload(BaseModel):
    slug: str
    headline: str
    subhead: str
    byline_name: str
    byline_role: str
    published_date: str
    niche: str
    voice_archetype: str
    layout_archetype: str
    palette_primary: str
    palette_accent: str
    palette_cta: str
    font_heading: str
    font_body: str
    hero_image_local_path: str
    final_cta_text: str
    final_cta_url: str


class AdvertorialPayload(BaseModel):
    parent: ParentPayload
    sections: list[SectionPayload] = Field(default_factory=list)


def build_payload(assembly: dict) -> AdvertorialPayload:
    parent = ParentPayload(
        slug=assembly["slug"],
        headline=assembly["headline"],
        subhead=assembly["subhead"],
        byline_name=assembly["byline_name"],
        byline_role=assembly["byline_role"],
        published_date=assembly["published_date"],
        niche=assembly["niche"],
        voice_archetype=assembly["voice_archetype"],
        layout_archetype=assembly["layout_archetype"],
        palette_primary=assembly["palette_primary"],
        palette_accent=assembly["palette_accent"],
        palette_cta=assembly["palette_cta"],
        font_heading=assembly["font_heading"],
        font_body=assembly["font_body"],
        hero_image_local_path=assembly["hero_image"],
        final_cta_text=assembly["final_cta_text"],
        final_cta_url=assembly["final_cta_url"],
    )
    sections: list[SectionPayload] = []
    for i, s in enumerate(assembly.get("sections") or []):
        sections.append(
            SectionPayload(
                parent_slug=parent.slug,
                order_index=i,
                section_type=s["section_type"],
                heading=s.get("heading", ""),
                body=s.get("body", ""),
                image_local_path=s.get("image"),
                cta_text=s.get("cta_text"),
                cta_url=s.get("cta_url"),
                design_emphasis=s.get("design_emphasis", "normal"),
            )
        )
    return AdvertorialPayload(parent=parent, sections=sections)
