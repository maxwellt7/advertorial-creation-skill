import json
from unittest.mock import MagicMock

from scripts.intent_classifier import Intent, classify


def _fake_anthropic(json_output: dict):
    fake = MagicMock()
    fake.messages.create.return_value = MagicMock(
        content=[MagicMock(text=json.dumps(json_output))]
    )
    return fake


def test_classify_approve(monkeypatch):
    fake = _fake_anthropic({"action": "approve", "target": None, "modifier_note": None})
    monkeypatch.setattr("scripts.intent_classifier._get_anthropic", lambda: fake)
    intent = classify("approve", phase="design")
    assert intent.action == "approve"
    assert intent.target is None


def test_classify_targeted_regen(monkeypatch):
    fake = _fake_anthropic({
        "action": "regenerate",
        "target": "hero",
        "modifier_note": "more daylight, less cluttered counter",
    })
    monkeypatch.setattr("scripts.intent_classifier._get_anthropic", lambda: fake)
    intent = classify("regen hero — more daylight, less cluttered counter", phase="images")
    assert intent.action == "regenerate"
    assert intent.target == "hero"
    assert "daylight" in intent.modifier_note


def test_classify_swap_palette(monkeypatch):
    fake = _fake_anthropic({
        "action": "swap_palette",
        "target": None,
        "modifier_note": "warm neutral",
    })
    monkeypatch.setattr("scripts.intent_classifier._get_anthropic", lambda: fake)
    intent = classify("swap palette to warm neutral", phase="design")
    assert intent.action == "swap_palette"
    assert intent.modifier_note == "warm neutral"


def test_classify_restart_phase(monkeypatch):
    fake = _fake_anthropic({"action": "restart_phase", "target": None, "modifier_note": None})
    monkeypatch.setattr("scripts.intent_classifier._get_anthropic", lambda: fake)
    intent = classify("restart phase", phase="design")
    assert intent.action == "restart_phase"
