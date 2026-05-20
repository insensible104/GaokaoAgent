"""Smoke checks that prediction-time generation cannot read 2025 outcome labels."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pandas as pd

from agents.game_agent import _resolve_runtime_data_dir
from engines.quant_engine import GaokaoQuantEngine


def _write_history_csv(path: Path, school: str) -> None:
    pd.DataFrame(
        [
            {
                "院校名称": school,
                "代码": "10001",
                "专业/类": "计算机类",
                "最低分平均排位": 12000,
                "录取人数": 10,
                "专业组": "201",
                "年份": 2024,
                "选科": "物+化",
            }
        ]
    ).to_csv(path, index=False, encoding="utf-8-sig")


def test_quant_engine_excludes_actual_2025_csv_files() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        data_dir = Path(tmp)
        _write_history_csv(data_dir / "2024_physics.csv", "Prediction University")
        _write_history_csv(data_dir / "actual_2025.csv", "Outcome Label University")
        _write_history_csv(data_dir / "actual_2025_major_admissions.csv", "Outcome Major University")

        engine = GaokaoQuantEngine(data_dir=str(data_dir))

        assert "Prediction University" in set(engine.df["school"])
        assert "Outcome Label University" not in set(engine.df["school"])
        assert "Outcome Major University" not in set(engine.df["school"])


def test_game_agent_prefers_backend_prediction_data_over_root_actual_data() -> None:
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        root_data = root / "data"
        backend_data = root / "backend" / "data"
        root_data.mkdir(parents=True)
        backend_data.mkdir(parents=True)

        _write_history_csv(root_data / "actual_2025.csv", "Outcome Label University")
        _write_history_csv(backend_data / "2024_physics.csv", "Prediction University")
        (backend_data / "2025_enrollment_full.csv").write_text(
            "院校代码,院校名称,科类,专业组代码,专业序号,专业名称\n",
            encoding="utf-8",
        )

        try:
            os.chdir(root)
            resolved = Path(_resolve_runtime_data_dir()).resolve()
        finally:
            os.chdir(original_cwd)

        assert resolved == backend_data.resolve()


if __name__ == "__main__":
    test_quant_engine_excludes_actual_2025_csv_files()
    test_game_agent_prefers_backend_prediction_data_over_root_actual_data()
    print("prediction data boundary smoke tests passed")
