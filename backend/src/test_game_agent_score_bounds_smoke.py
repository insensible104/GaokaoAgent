"""Smoke tests for game-agent score normalization."""

import pandas as pd

from agents.game_agent import _limit_precision_candidates, _normalize_percent_score
from models.user_profile import UserProfile


def test_normalize_percent_score_clamps_to_schema_range() -> None:
    assert _normalize_percent_score(102.86) == 1.0
    assert _normalize_percent_score(72.5) == 0.725
    assert _normalize_percent_score(-4.0) == 0.0


def test_precision_candidate_limit_keeps_rank_bands() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州", "深圳"],
        preferred_majors=["计算机"],
    )
    rows = []
    for idx, min_rank in enumerate(range(2000, 50000, 1200)):
        rows.append(
            {
                "school": "深圳大学" if idx % 7 == 0 else f"测试大学{idx}",
                "school_code": f"{10000 + idx}",
                "major_group": str(200 + idx),
                "major": ["计算机类"] if idx % 5 == 0 else ["管理类"],
                "min_rank": min_rank,
                "quota": 20 + idx,
            }
        )

    limited = _limit_precision_candidates(
        pd.DataFrame(rows),
        profile,
        total_recommend=2,
        max_candidates=12,
    )

    assert len(limited) == 12
    rank_diffs = limited["min_rank"] - profile.rank
    assert any(rank_diffs < 0)
    assert any((rank_diffs >= 0) & (rank_diffs <= 6000))
    assert any(rank_diffs > 6000)


if __name__ == "__main__":
    test_normalize_percent_score_clamps_to_schema_range()
    test_precision_candidate_limit_keeps_rank_bands()
    print("game agent score bounds smoke tests passed")
