"""Smoke tests for explicit recommendation data-vintage boundaries."""

from pathlib import Path
from tempfile import TemporaryDirectory
from importlib import import_module
from importlib.util import find_spec

assert find_spec("recommendation.data_vintage") is not None
data_vintage = import_module("recommendation.data_vintage")
from models.game_matrix import GameMatrix
from agents import report_agent


def test_detects_latest_years_and_blocks_missing_target_year_plan() -> None:
    assert hasattr(data_vintage, "inspect_recommendation_data_vintage")

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for name in (
            "2023_physics.csv",
            "2024_physics.csv",
            "2025_enrollment_full.csv",
            "2025_物理_yifenyiduan.csv",
        ):
            (root / name).write_text("placeholder", encoding="utf-8")

        vintage = data_vintage.inspect_recommendation_data_vintage(root, target_year=2026)

    assert vintage.target_year == 2026
    assert vintage.latest_historical_admission_year == 2024
    assert vintage.enrollment_plan_year == 2025
    assert vintage.rank_table_year == 2025
    assert vintage.formal_recommendation_ready is False
    assert "2026 enrollment plan" in " ".join(vintage.limitations)


def test_target_year_files_make_vintage_formally_ready() -> None:
    assert hasattr(data_vintage, "inspect_recommendation_data_vintage")

    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        for name in (
            "2025_physics.csv",
            "2026_enrollment_full.csv",
            "2026_物理_yifenyiduan.csv",
        ):
            (root / name).write_text("placeholder", encoding="utf-8")

        vintage = data_vintage.inspect_recommendation_data_vintage(root, target_year=2026)

    assert vintage.formal_recommendation_ready is True
    assert vintage.limitations == []


def test_game_matrix_serializes_data_vintage_for_clients() -> None:
    vintage = data_vintage.RecommendationDataVintage(
        target_year=2026,
        latest_historical_admission_year=2024,
        enrollment_plan_year=2025,
        rank_table_year=2025,
        formal_recommendation_ready=False,
        limitations=["Missing 2026 enrollment plan; latest available plan is 2025."],
    )
    matrix = GameMatrix(data_vintage=vintage.model_dump())

    assert matrix.data_vintage is not None
    assert matrix.model_dump()["data_vintage"]["target_year"] == 2026


def test_game_agent_attaches_runtime_data_vintage() -> None:
    source = (Path(__file__).parent / "agents" / "game_agent.py").read_text(encoding="utf-8")

    assert "inspect_recommendation_data_vintage" in source
    assert "data_vintage=data_vintage.model_dump()" in source


def test_report_exposes_data_vintage_limitation() -> None:
    assert hasattr(report_agent, "_data_vintage_warning")
    matrix = GameMatrix(
        data_vintage={
            "target_year": 2026,
            "latest_historical_admission_year": 2024,
            "enrollment_plan_year": 2025,
            "rank_table_year": 2025,
            "formal_recommendation_ready": False,
            "limitations": ["Missing 2026 enrollment plan; latest available plan is 2025."],
        }
    )

    warning = report_agent._data_vintage_warning(matrix)

    assert "2026" in warning
    assert "2025" in warning
    assert "正式填报" in warning


if __name__ == "__main__":
    test_detects_latest_years_and_blocks_missing_target_year_plan()
    test_target_year_files_make_vintage_formally_ready()
    test_game_matrix_serializes_data_vintage_for_clients()
    test_game_agent_attaches_runtime_data_vintage()
    test_report_exposes_data_vintage_limitation()
    print("data vintage smoke tests passed")
