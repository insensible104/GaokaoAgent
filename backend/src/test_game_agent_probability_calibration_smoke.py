"""Smoke test for game-agent runtime probability calibration wiring."""

from pathlib import Path

from agents.game_agent import _calibrate_online_probability


def test_game_agent_uses_versioned_probability_calibration_artifact() -> None:
    artifact_path = Path(__file__).parents[1] / "data" / "probability_calibration_2025.json"

    calibrated, metadata = _calibrate_online_probability(
        0.95,
        artifact_path,
        subject_group="历史",
    )

    physics_calibrated, physics_metadata = _calibrate_online_probability(
        0.95,
        artifact_path,
        subject_group="物理",
    )

    assert calibrated < physics_calibrated
    assert metadata["probability_is_calibrated"] is True
    assert metadata["probability_calibration_year"] == 2025
    assert metadata["probability_hazard_scale"] == 0.20
    assert metadata["raw_admission_prob"] == 0.95
    assert metadata["probability_method"] == "historical_beta_subject"
    assert physics_metadata["probability_method"] == "historical_beta_subject"


def test_game_agent_falls_back_without_artifact() -> None:
    calibrated, metadata = _calibrate_online_probability(
        0.72,
        Path("missing-calibration.json"),
        subject_group="历史",
    )

    assert calibrated == 0.72
    assert metadata["probability_is_calibrated"] is False
    assert metadata["probability_method"] == "historical_rank_monte_carlo_uncalibrated"


if __name__ == "__main__":
    test_game_agent_uses_versioned_probability_calibration_artifact()
    test_game_agent_falls_back_without_artifact()
    print("game agent probability calibration smoke tests passed")
