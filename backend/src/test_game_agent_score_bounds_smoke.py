"""Smoke tests for game-agent score normalization."""

from agents.game_agent import _normalize_percent_score


def test_normalize_percent_score_clamps_to_schema_range() -> None:
    assert _normalize_percent_score(102.86) == 1.0
    assert _normalize_percent_score(72.5) == 0.725
    assert _normalize_percent_score(-4.0) == 0.0


if __name__ == "__main__":
    test_normalize_percent_score_clamps_to_schema_range()
    print("game agent score bounds smoke tests passed")
