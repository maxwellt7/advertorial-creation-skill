import json
from pathlib import Path

import pytest

from scripts.state import RunState, load_state, save_state, init_run


def test_init_run_creates_state_file(tmp_path: Path):
    run_dir = tmp_path / "run-001"
    state = init_run(run_dir, run_id="run-001")
    assert (run_dir / "state.json").exists()
    assert state.run_id == "run-001"
    assert state.current_phase == "intake"
    assert state.status == "in_progress"
    assert state.cost_usd == 0.0


def test_save_and_load_round_trip(tmp_path: Path):
    run_dir = tmp_path / "run-002"
    state = init_run(run_dir, run_id="run-002")
    state.current_phase = "copy"
    state.status = "awaiting_review"
    state.cost_usd = 0.42
    save_state(run_dir, state)

    loaded = load_state(run_dir)
    assert loaded.current_phase == "copy"
    assert loaded.status == "awaiting_review"
    assert loaded.cost_usd == 0.42


def test_save_state_is_atomic(tmp_path: Path):
    run_dir = tmp_path / "run-003"
    state = init_run(run_dir, run_id="run-003")
    save_state(run_dir, state)
    # No leftover temp files (mkstemp uses prefix "state.json." with random suffix)
    leftovers = [
        f for f in run_dir.iterdir()
        if f.name.startswith("state.json.") and f.name != "state.json"
    ]
    assert leftovers == []


def test_init_run_raises_when_state_already_exists(tmp_path: Path):
    run_dir = tmp_path / "run-existing"
    init_run(run_dir, run_id="run-existing")
    with pytest.raises(FileExistsError):
        init_run(run_dir, run_id="run-existing")


def test_load_state_raises_on_missing(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        load_state(tmp_path / "nonexistent")


def test_artifact_hash_record(tmp_path: Path):
    run_dir = tmp_path / "run-004"
    state = init_run(run_dir, run_id="run-004")
    artifact = run_dir / "copy.md"
    artifact.write_text("hello world")
    state.record_artifact("copy.md", artifact)
    save_state(run_dir, state)

    loaded = load_state(run_dir)
    assert "copy.md" in loaded.artifacts
    assert loaded.artifacts["copy.md"].hash == state.artifacts["copy.md"].hash
    assert len(loaded.artifacts["copy.md"].hash) == 64  # sha256 hex


def test_artifact_hash_change_detection(tmp_path: Path):
    run_dir = tmp_path / "run-005"
    state = init_run(run_dir, run_id="run-005")
    artifact = run_dir / "copy.md"
    artifact.write_text("v1 content")
    state.record_artifact("copy.md", artifact)
    save_state(run_dir, state)

    artifact.write_text("v2 user-edited content")
    loaded = load_state(run_dir)
    assert loaded.artifact_changed_on_disk("copy.md", artifact) is True


from scripts.state import (
    advance_phase,
    current_run_dir,
    generate_run_id,
    set_current_run,
)


def test_generate_run_id_is_url_safe():
    rid = generate_run_id("Why Shelters Are Switching To These Pee Pads")
    assert rid.startswith("2")
    assert "/" not in rid
    assert " " not in rid
    assert rid.lower() == rid


def test_current_run_pointer(tmp_path: Path, monkeypatch):
    pointer = tmp_path / "current"
    monkeypatch.setattr("scripts.state.CURRENT_RUN_POINTER", pointer)
    target = tmp_path / "runs" / "abc"
    target.mkdir(parents=True)
    set_current_run(target)
    assert current_run_dir() == target


def test_advance_phase_transitions_status(tmp_path: Path):
    run_dir = tmp_path / "run-advance"
    init_run(run_dir, run_id="run-advance")
    advance_phase(run_dir, to_phase="copy", status="awaiting_review")
    state = load_state(run_dir)
    assert state.current_phase == "copy"
    assert state.status == "awaiting_review"
