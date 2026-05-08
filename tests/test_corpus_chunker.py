from pathlib import Path

from scripts.corpus_chunker import Chunk, parse_advertorial, parse_fb_ad

FIXTURE = Path(__file__).parent / "fixtures" / "sample_advertorial.md"
FB_FIXTURE = Path(__file__).parent / "fixtures" / "sample_fb_ad.md"


def test_parse_advertorial_extracts_hook_headline():
    chunks = parse_advertorial(FIXTURE)
    hook_chunks = [c for c in chunks if c.chunk_type == "hook_headline"]
    assert len(hook_chunks) == 1
    assert "Pee Pads" in hook_chunks[0].text


def test_parse_advertorial_extracts_voice_examples():
    chunks = parse_advertorial(FIXTURE)
    voice_chunks = [c for c in chunks if c.chunk_type == "voice_example"]
    assert len(voice_chunks) == 3
    assert any("12 years" in c.text for c in voice_chunks)


def test_parse_advertorial_extracts_structural_beats():
    chunks = parse_advertorial(FIXTURE)
    beat_chunks = [c for c in chunks if c.chunk_type == "structural_beat"]
    assert len(beat_chunks) == 2
    assert any("open loop" in c.text for c in beat_chunks)


def test_parse_advertorial_extracts_image_prompts():
    chunks = parse_advertorial(FIXTURE)
    image_chunks = [c for c in chunks if c.chunk_type == "image_prompt"]
    assert len(image_chunks) == 1
    assert "kitchen floor" in image_chunks[0].text


def test_parse_advertorial_extracts_cta_pattern():
    chunks = parse_advertorial(FIXTURE)
    cta_chunks = [c for c in chunks if c.chunk_type == "cta_pattern"]
    assert len(cta_chunks) >= 1
    assert any("benefit-first" in c.text for c in cta_chunks)


def test_chunks_carry_metadata():
    chunks = parse_advertorial(FIXTURE)
    for c in chunks:
        assert c.metadata.niche == "pet / home goods"
        assert c.metadata.rank == 1
        assert c.metadata.source_corpus == "advertorial"
        assert c.metadata.source_file.endswith("sample_advertorial.md")


def test_parse_fb_ad_extracts_hook():
    chunks = parse_fb_ad(FB_FIXTURE)
    hooks = [c for c in chunks if c.chunk_type == "fb_hook"]
    assert len(hooks) == 1
    assert "shelter dogs" in hooks[0].text


def test_parse_fb_ad_extracts_headline_and_primary_text():
    chunks = parse_fb_ad(FB_FIXTURE)
    types = {c.chunk_type for c in chunks}
    assert "fb_headline" in types
    assert "fb_primary_text" in types


def test_parse_fb_ad_extracts_image_prompt():
    chunks = parse_fb_ad(FB_FIXTURE)
    img = [c for c in chunks if c.chunk_type == "fb_image_prompt"]
    assert len(img) == 1
    assert "UGC-style" in img[0].text


def test_parse_fb_ad_extracts_voice_examples():
    chunks = parse_fb_ad(FB_FIXTURE)
    voice = [c for c in chunks if c.chunk_type == "fb_voice_example"]
    assert len(voice) == 1


def test_parse_fb_ad_extracts_bridge():
    chunks = parse_fb_ad(FB_FIXTURE)
    bridge = [c for c in chunks if c.chunk_type == "fb_bridge"]
    assert len(bridge) == 1


def test_fb_ad_chunks_carry_source_corpus_metadata():
    chunks = parse_fb_ad(FB_FIXTURE)
    for c in chunks:
        assert c.metadata.source_corpus == "fb_ad"
