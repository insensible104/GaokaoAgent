"""Smoke tests for 2025 frozen-plan profile generation coverage."""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from generate_frozen_plans_2025 import PHYSICS_RANKS, HISTORY_RANKS, generate_profiles


def test_generate_profiles_can_exceed_static_rank_grid(tmp_path: Path) -> None:
    requested = len(PHYSICS_RANKS) + len(HISTORY_RANKS) + 20

    profiles = generate_profiles(data_dir=tmp_path, num_cases=requested, seed=20250521)
    case_ids = [case_id for case_id, _ in profiles]
    ranks = [profile.rank for _, profile in profiles]

    assert len(profiles) == requested
    assert len(set(case_ids)) == requested
    assert len(set(ranks)) > len(PHYSICS_RANKS) + len(HISTORY_RANKS)
    assert all(profile.score > 0 for _, profile in profiles)
