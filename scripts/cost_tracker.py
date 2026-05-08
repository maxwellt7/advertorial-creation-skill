from __future__ import annotations

from enum import Enum
from pathlib import Path

from scripts.state import load_state, save_state

WARN_THRESHOLD = 0.80


class CostStatus(str, Enum):
    OK = "ok"
    WARN = "warn"
    BLOCKED = "blocked"


def status_for(run_dir: Path) -> CostStatus:
    state = load_state(run_dir)
    ratio = state.cost_usd / state.cost_ceiling_usd if state.cost_ceiling_usd else 0
    if state.cost_usd >= state.cost_ceiling_usd:
        return CostStatus.BLOCKED
    if ratio >= WARN_THRESHOLD:
        return CostStatus.WARN
    return CostStatus.OK


def charge(run_dir: Path, amount_usd: float, reason: str) -> CostStatus:
    state = load_state(run_dir)
    state.cost_usd = round(state.cost_usd + amount_usd, 6)
    save_state(run_dir, state)
    return status_for(run_dir)
