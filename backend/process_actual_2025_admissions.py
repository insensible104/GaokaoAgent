"""Normalize 2025 Guangdong actual admission outcomes.

The source workbook contains two outcome levels:

- major-level admission rows
- school-major-group filing rows

This script exports both normalized layers and a merged CSV that can be loaded
by `evaluation.backtest_2025.load_actual_outcomes_csv`.
"""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import pandas as pd


HISTORY = "\u5386\u53f2"
PHYSICS = "\u7269\u7406"

MAJOR_SHEETS = {
    HISTORY: 1,
    PHYSICS: 2,
}
GROUP_SHEETS = {
    HISTORY: 3,
    PHYSICS: 4,
}


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def _clean_id(value: Any, width: int | None = None) -> str:
    text = _clean_text(value)
    if not text:
        return ""
    try:
        if "e" in text.lower():
            text = str(int(float(text)))
    except ValueError:
        pass
    if width and text.isdigit():
        return text.zfill(width)
    return text


def _to_int(value: Any) -> int | None:
    text = _clean_text(value).replace(",", "")
    if not text:
        return None
    try:
        return int(float(text))
    except ValueError:
        return None


def _find_default_input() -> Path:
    downloads = Path.home() / "Downloads"
    matches = sorted(downloads.glob("*26430.xlsx"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not matches:
        raise FileNotFoundError(
            "No default source workbook found. Pass --input with the Anto 2025 admission workbook path."
        )
    return matches[0]


def load_major_rows(source: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for subject_group, sheet_index in MAJOR_SHEETS.items():
        df = pd.read_excel(source, sheet_name=sheet_index, dtype=object)
        out = pd.DataFrame(
            {
                "subject_group": subject_group,
                "school_code": df.iloc[:, 0].map(lambda v: _clean_id(v, 5)),
                "school_name": df.iloc[:, 1].map(_clean_text),
                "major_code": df.iloc[:, 2].map(lambda v: _clean_id(v, 3)),
                "major_name": df.iloc[:, 3].map(_clean_text),
                "selection_requirement": df.iloc[:, 4].map(_clean_text),
                "actual_major_max_score": df.iloc[:, 5].map(_to_int),
                "actual_major_min_score": df.iloc[:, 6].map(_to_int),
                "actual_major_min_rank": df.iloc[:, 7].map(_to_int),
                "major_group_code": df.iloc[:, 8].map(lambda v: _clean_id(v, 3)),
                "college_department": df.iloc[:, 9].map(_clean_text),
                "actual_major_avg_score": df.iloc[:, 10].map(_to_int),
                "actual_major_admit_count": df.iloc[:, 11].map(_to_int),
                "major_note": df.iloc[:, 12].map(_clean_text),
            }
        )
        frames.append(out)

    major_rows = pd.concat(frames, ignore_index=True)
    return major_rows[
        (major_rows["school_code"] != "")
        & (major_rows["school_name"] != "")
        & (major_rows["major_group_code"] != "")
        & (major_rows["major_name"] != "")
    ].copy()


def load_group_rows(source: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for subject_group, sheet_index in GROUP_SHEETS.items():
        df = pd.read_excel(source, sheet_name=sheet_index, dtype=object)
        out = pd.DataFrame(
            {
                "subject_group": subject_group,
                "school_code": df.iloc[:, 0].map(lambda v: _clean_id(v, 5)),
                "school_name": df.iloc[:, 1].map(_clean_text),
                "major_group_code": df.iloc[:, 2].map(lambda v: _clean_id(v, 3)),
                "selection_requirement": df.iloc[:, 3].map(_clean_text),
                "group_majors_text": df.iloc[:, 4].map(_clean_text),
                "actual_group_min_score": df.iloc[:, 5].map(_to_int),
                "actual_group_min_rank": df.iloc[:, 6].map(_to_int),
                "actual_group_plan_count": df.iloc[:, 7].map(_to_int),
                "actual_group_filing_count": df.iloc[:, 8].map(_to_int),
                "actual_group_vacancy_count": df.iloc[:, 9].map(_to_int),
                "group_note": df.iloc[:, 10].map(_clean_text),
                "group_major_count": df.iloc[:, 11].map(_to_int),
            }
        )
        frames.append(out)

    group_rows = pd.concat(frames, ignore_index=True)
    return group_rows[
        (group_rows["school_code"] != "")
        & (group_rows["school_name"] != "")
        & (group_rows["major_group_code"] != "")
    ].copy()


def build_pipeline_rows(major_rows: pd.DataFrame, group_rows: pd.DataFrame) -> pd.DataFrame:
    group_columns = [
        "subject_group",
        "school_code",
        "school_name",
        "major_group_code",
        "actual_group_min_score",
        "actual_group_min_rank",
        "actual_group_plan_count",
        "actual_group_filing_count",
        "actual_group_vacancy_count",
        "group_note",
        "group_major_count",
    ]
    merged = major_rows.merge(
        group_rows[group_columns],
        on=["subject_group", "school_code", "school_name", "major_group_code"],
        how="left",
        indicator=True,
    )
    unmatched = int((merged["_merge"] != "both").sum())
    if unmatched:
        raise ValueError(f"{unmatched} major rows did not match a group filing row.")
    merged = merged.drop(columns=["_merge"])

    ordered_columns = [
        "subject_group",
        "school_code",
        "school_name",
        "major_group_code",
        "actual_group_min_score",
        "actual_group_min_rank",
        "major_code",
        "major_name",
        "actual_major_min_score",
        "actual_major_min_rank",
        "actual_major_max_score",
        "actual_major_avg_score",
        "actual_major_admit_count",
        "selection_requirement",
        "college_department",
        "major_note",
        "actual_group_plan_count",
        "actual_group_filing_count",
        "actual_group_vacancy_count",
        "group_note",
        "group_major_count",
    ]
    return merged[ordered_columns].copy()


def build_quality_summary(
    *,
    source: Path,
    major_rows: pd.DataFrame,
    group_rows: pd.DataFrame,
    pipeline_rows: pd.DataFrame,
) -> dict[str, Any]:
    major_groups = major_rows[
        ["subject_group", "school_code", "school_name", "major_group_code"]
    ].drop_duplicates()
    group_keys = group_rows[
        ["subject_group", "school_code", "school_name", "major_group_code"]
    ].drop_duplicates()
    duplicate_major_names = major_rows[
        major_rows.duplicated(
            ["subject_group", "school_code", "major_group_code", "major_name"],
            keep=False,
        )
    ]
    return {
        "source": str(source),
        "major_rows": int(len(major_rows)),
        "group_rows": int(len(group_rows)),
        "pipeline_rows": int(len(pipeline_rows)),
        "schools": int(pipeline_rows["school_name"].nunique()),
        "major_groups_from_major_rows": int(len(major_groups)),
        "major_groups_from_group_rows": int(len(group_keys)),
        "subject_major_rows": {
            str(k): int(v) for k, v in major_rows["subject_group"].value_counts().to_dict().items()
        },
        "subject_group_rows": {
            str(k): int(v) for k, v in group_rows["subject_group"].value_counts().to_dict().items()
        },
        "missing_major_min_rank": int(major_rows["actual_major_min_rank"].isna().sum()),
        "missing_group_min_rank": int(group_rows["actual_group_min_rank"].isna().sum()),
        "duplicate_major_keys": int(
            major_rows.duplicated(
                ["subject_group", "school_code", "major_group_code", "major_code", "major_name"]
            ).sum()
        ),
        "duplicate_group_keys": int(
            group_rows.duplicated(["subject_group", "school_code", "major_group_code"]).sum()
        ),
        "duplicate_major_name_rows_within_group": int(len(duplicate_major_names)),
        "duplicate_major_name_groups_within_group": int(
            duplicate_major_names[
                ["subject_group", "school_code", "major_group_code", "major_name"]
            ].drop_duplicates().shape[0]
        ),
        "note": (
            "Rows with duplicate major names inside the same group are preserved in CSV. "
            "The backtest loader aggregates them by major name using the largest cutoff rank."
        ),
    }


def process_actual_2025_admissions(source: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    major_rows = load_major_rows(source)
    group_rows = load_group_rows(source)
    pipeline_rows = build_pipeline_rows(major_rows, group_rows)
    summary = build_quality_summary(
        source=source,
        major_rows=major_rows,
        group_rows=group_rows,
        pipeline_rows=pipeline_rows,
    )

    major_path = output_dir / "actual_2025_major_admissions.csv"
    group_path = output_dir / "actual_2025_group_admissions.csv"
    pipeline_path = output_dir / "actual_2025.csv"
    summary_path = output_dir / "actual_2025_data_quality.json"
    source_copy = output_dir / "actual_2025_source_antoshengya.xlsx"

    major_rows.to_csv(major_path, index=False, encoding="utf-8-sig")
    group_rows.to_csv(group_path, index=False, encoding="utf-8-sig")
    pipeline_rows.to_csv(pipeline_path, index=False, encoding="utf-8-sig")
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    if source.resolve() != source_copy.resolve():
        shutil.copy2(source, source_copy)

    summary["outputs"] = {
        "major_csv": str(major_path),
        "group_csv": str(group_path),
        "pipeline_csv": str(pipeline_path),
        "quality_json": str(summary_path),
        "source_copy": str(source_copy),
    }
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize 2025 actual admission outcome workbook.")
    parser.add_argument("--input", type=Path, default=None, help="Source .xlsx path.")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Output data directory.")
    args = parser.parse_args()

    source = args.input or _find_default_input()
    summary = process_actual_2025_admissions(source=source, output_dir=args.output_dir)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
