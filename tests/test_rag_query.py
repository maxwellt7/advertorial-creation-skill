from unittest.mock import MagicMock

from scripts.rag_query import RagResult, query


def test_query_builds_filter_and_returns_results(monkeypatch):
    fake_index = MagicMock()
    fake_index.query.return_value = MagicMock(
        matches=[
            MagicMock(score=0.9, metadata={"text": "hook for pet niche", "niche": "pet / home goods", "chunk_type": "hook_headline", "source_corpus": "advertorial"}),
            MagicMock(score=0.85, metadata={"text": "another hook", "niche": "pet / home goods", "chunk_type": "hook_headline", "source_corpus": "advertorial"}),
        ]
    )
    fake_openai = MagicMock()
    fake_openai.embeddings.create.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 3072)])

    monkeypatch.setattr("scripts.rag_query._get_index", lambda: fake_index)
    monkeypatch.setattr("scripts.rag_query._get_openai", lambda: fake_openai)

    results = query(
        text="hook for puppy pee pad solving accidents",
        chunk_types=["hook_headline"],
        niche="pet / home goods",
        source_corpus="advertorial",
        top_k=5,
    )

    assert len(results) == 2
    assert isinstance(results[0], RagResult)
    assert results[0].text == "hook for pet niche"

    call_args = fake_index.query.call_args
    filt = call_args.kwargs["filter"]
    assert filt["chunk_type"]["$in"] == ["hook_headline"]
    assert filt["niche"]["$eq"] == "pet / home goods"
    assert filt["source_corpus"]["$eq"] == "advertorial"
    assert call_args.kwargs["top_k"] == 5


def test_query_omits_filter_when_no_constraints(monkeypatch):
    fake_index = MagicMock()
    fake_index.query.return_value = MagicMock(matches=[])
    fake_openai = MagicMock()
    fake_openai.embeddings.create.return_value = MagicMock(data=[MagicMock(embedding=[0.1] * 3072)])
    monkeypatch.setattr("scripts.rag_query._get_index", lambda: fake_index)
    monkeypatch.setattr("scripts.rag_query._get_openai", lambda: fake_openai)

    query(text="x", chunk_types=None, niche=None, source_corpus=None, top_k=3)

    call_args = fake_index.query.call_args
    assert "filter" not in call_args.kwargs or call_args.kwargs["filter"] in (None, {})
