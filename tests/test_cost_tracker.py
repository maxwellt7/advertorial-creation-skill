from pathlib import Path

import pytest

from scripts.cost_tracker import CostStatus, charge, status_for
from scripts.state import init_run, load_state


def test_charge_increments_cost(tmp_path: Path):
    run_dir = tmp_path / "run"
    init_run(run_dir, run_id="run")
    charge(run_dir, amount_usd=0.10, reason="anthropic copy")
    state = load_state(run_dir)
    assert state.cost_usd == 0.10


def test_charge_under_ceiling_returns_ok(tmp_path: Path):
    run_dir = tmp_path / "run"
    init_run(run_dir, run_id="run", cost_ceiling_usd=5.00)
    s = charge(run_dir, amount_usd=1.00, reason="x")
    assert s == CostStatus.OK


def test_charge_at_warning_threshold(tmp_path: Path):
    run_dir = tmp_path / "run"
    init_run(run_dir, run_id="run", cost_ceiling_usd=5.00)
    s = charge(run_dir, amount_usd=4.10, reason="x")
    assert s == CostStatus.WARN


def test_charge_at_ceiling_returns_blocked(tmp_path: Path):
    run_dir = tmp_path / "run"
    init_run(run_dir, run_id="run", cost_ceiling_usd=5.00)
    s = charge(run_dir, amount_usd=5.00, reason="x")
    assert s == CostStatus.BLOCKED


def test_status_for_returns_current_status(tmp_path: Path):
    run_dir = tmp_path / "run"
    init_run(run_dir, run_id="run", cost_ceiling_usd=5.00)
    charge(run_dir, amount_usd=2.00, reason="x")
    assert status_for(run_dir) == CostStatus.OK
