import pytest

from scripts.image_router import RouteDecision, route


def test_hero_routes_to_flux():
    d = route("hero")
    assert d.provider == "fal"
    assert d.model == "flux-pro-1.1"


def test_proof_quote_routes_to_ideogram():
    d = route("proof_quote")
    assert d.provider == "fal"
    assert d.model == "ideogram-v2"


def test_comparison_table_routes_to_ideogram():
    d = route("comparison_table")
    assert d.provider == "fal"
    assert d.model == "ideogram-v2"


def test_mechanism_explainer_routes_to_openai():
    d = route("mechanism_explainer")
    assert d.provider == "openai"
    assert d.model == "gpt-image-1"


def test_numbered_reason_routes_to_flux():
    d = route("numbered_reason")
    assert d.provider == "fal"
    assert d.model == "flux-pro-1.1"


def test_lifestyle_routine_routes_to_flux():
    d = route("lifestyle_routine")
    assert d.provider == "fal"
    assert d.model == "flux-pro-1.1"


def test_non_image_section_returns_none():
    assert route("intro") is None
    assert route("cta_button") is None
    assert route("final_verdict") is None
    assert route("risk_reversal") is None
    assert route("faq") is None


def test_unknown_section_raises():
    with pytest.raises(ValueError):
        route("totally_made_up")
