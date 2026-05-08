from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


PhaseName = Literal[
    "intake", "copy", "design", "images", "assembly", "push", "complete"
]
RunStatus = Literal["in_progress", "awaiting_review", "paused", "complete", "error"]


class ArtifactRef(BaseModel):
    path: str
    hash: str
    version: int = 1


class IntakeData(BaseModel):
    product: str | None = None
    niche: str | None = None
    target_customer: str | None = None
    primary_problem: str | None = None
    desired_outcome: str | None = None
    unique_mechanism: str | None = None
    proof_assets: str | None = None
    offer: str | None = None
    voice_archetype: str | None = None
    layout_archetype: str | None = None
    headline_formula: str | None = None
    compliance_limits: str | None = None


class RunState(BaseModel):
    run_id: str
    created_at: str
    current_phase: PhaseName = "intake"
    status: RunStatus = "in_progress"
    intake: IntakeData = Field(default_factory=IntakeData)
    artifacts: dict[str, ArtifactRef] = Field(default_factory=dict)
    cost_usd: float = 0.0
    cost_ceiling_usd: float = 5.00
    errors: list[str] = Field(default_factory=list)

    def record_artifact(self, name: str, path: Path) -> None:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        existing = self.artifacts.get(name)
        version = (existing.version + 1) if existing else 1
        self.artifacts[name] = ArtifactRef(
            path=str(path), hash=digest, version=version
        )

    def artifact_changed_on_disk(self, name: str, path: Path) -> bool:
        if name not in self.artifacts:
            return True
        current = hashlib.sha256(path.read_bytes()).hexdigest()
        return current != self.artifacts[name].hash


def _state_path(run_dir: Path) -> Path:
    return run_dir / "state.json"


def init_run(run_dir: Path, run_id: str, cost_ceiling_usd: float = 5.00) -> RunState:
    run_dir.mkdir(parents=True, exist_ok=True)
    state = RunState(
        run_id=run_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        cost_ceiling_usd=cost_ceiling_usd,
    )
    save_state(run_dir, state)
    return state


def load_state(run_dir: Path) -> RunState:
    path = _state_path(run_dir)
    if not path.exists():
        raise FileNotFoundError(f"No state.json found at {path}")
    return RunState.model_validate_json(path.read_text())


def save_state(run_dir: Path, state: RunState) -> None:
    path = _state_path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = state.model_dump_json(indent=2)
    fd, tmp_path = tempfile.mkstemp(prefix="state.json.", dir=run_dir)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(payload)
        os.replace(tmp_path, path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
