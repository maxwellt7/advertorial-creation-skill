from pathlib import Path

import pytest

from scripts.framer_push import (
    AdvertorialPayload,
    SectionPayload,
    build_payload,
)


def test_build_payload_from_assembly(tmp_path: Path):
    assembly = {
        "slug": "puppy-pee-pad-2026-05-08",
        "headline": "Why Shelters Are Switching To These Pee Pads",
        "subhead": "They literally attract dogs.",
        "byline_name": "Mary Ross",
        "byline_role": "Editor",
        "published_date": "2026-05-08",
        "niche": "pet / home goods",
        "voice_archetype": "first_person_tester",
        "layout_archetype": "product_review_listicle",
        "palette_primary": "#FFFFFF",
        "palette_accent": "#1A1A1A",
        "palette_cta": "#E84C00",
        "font_heading": "Fraunces",
        "font_body": "Inter",
        "hero_image": str(tmp_path / "images" / "hero.png"),
        "final_cta_text": "Try PuppyPad Today",
        "final_cta_url": "https://puppypad.example/checkout",
        "sections": [
            {
                "section_type": "hero",
                "heading": "Why Shelters Are Switching",
                "body": "Hook body.",
                "image": str(tmp_path / "images" / "hero.png"),
                "design_emphasis": "high",
            },
            {
                "section_type": "numbered_reason",
                "heading": "Reason #1: It Attracts Dogs",
                "body": "Body 1.",
                "image": str(tmp_path / "images" / "reason-1.png"),
                "design_emphasis": "normal",
            },
            {
                "section_type": "cta_button",
                "heading": "",
                "body": "",
                "cta_text": "See Today's Offer",
                "cta_url": "https://puppypad.example/checkout",
                "design_emphasis": "normal",
            },
        ],
    }

    payload = build_payload(assembly)

    assert isinstance(payload, AdvertorialPayload)
    assert payload.parent.slug == "puppy-pee-pad-2026-05-08"
    assert len(payload.sections) == 3
    assert payload.sections[0].order_index == 0
    assert payload.sections[1].order_index == 1
    assert payload.sections[2].order_index == 2
    assert payload.sections[0].section_type == "hero"
    assert payload.sections[2].cta_text == "See Today's Offer"


def test_build_payload_validates_section_type(tmp_path: Path):
    assembly = {
        "slug": "x", "headline": "x", "subhead": "x", "byline_name": "x", "byline_role": "x",
        "published_date": "2026-05-08", "niche": "pet / home goods",
        "voice_archetype": "first_person_tester", "layout_archetype": "product_review_listicle",
        "palette_primary": "#FFF", "palette_accent": "#000", "palette_cta": "#F00",
        "font_heading": "Inter", "font_body": "Inter",
        "hero_image": "x.png", "final_cta_text": "x", "final_cta_url": "https://x",
        "sections": [
            {"section_type": "totally_invalid", "heading": "x", "body": "x", "design_emphasis": "normal"},
        ],
    }
    with pytest.raises(ValueError):
        build_payload(assembly)
