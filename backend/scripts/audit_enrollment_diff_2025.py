"""Build a 2025 enrollment-plan diff report from public plan/history files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "backend" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from recommendation.enrollment_diff import EnrollmentDiffEvent, diff_enrollment_plans  # noqa: E402


def _clean_code(value) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _pick_column(df: pd.DataFrame, candidates: Iterable[str]) -> str | None:
    normalized = {column.replace("\r", "").replace("\n", ""): column for column in df.columns}
    for candidate in candidates:
        key = candidate.replace("\r", "").replace("\n", "")
        if key in normalized:
            return normalized[key]
    return None


def _value(row: pd.Series, column: str | None, default=""):
    if not column:
        return default
    value = row.get(column, default)
    if pd.isna(value):
        return default
    return value


def load_2025_plan_rows(path: Path) -> list[dict]:
    df = pd.read_csv(path, encoding="utf-8-sig")
    rows: list[dict] = []
    for _, row in df.iterrows():
        rows.append(
            {
                "school_code": _clean_code(_value(row, "院校代码")),
                "school_name": str(_value(row, "院校名称")).strip(),
                "subject_group": str(_value(row, "科类")).strip(),
                "major_group_code": _clean_code(_value(row, "专业组代码")),
                "major_code": _clean_code(_value(row, "专业序号")),
                "major_name": str(_value(row, "专业名称")).strip(),
                "plan_quota": _value(row, "计划招数", None),
                "tuition": _value(row, "学费", None),
                "remarks": " | ".join(
                    text
                    for text in [
                        str(_value(row, "专业备注")).strip(),
                        str(_value(row, "招生备注")).strip(),
                    ]
                    if text
                ),
            }
        )
    return rows


def load_2024_history_rows(paths: list[Path]) -> list[dict]:
    rows: list[dict] = []
    for path in paths:
        df = pd.read_csv(path, encoding="utf-8-sig")
        code_col = _pick_column(df, ["代码"])
        school_col = _pick_column(df, ["院校名称"])
        major_code_col = _pick_column(df, ["专业编号"])
        major_col = _pick_column(df, ["专业/类"])
        group_col = _pick_column(df, ["专业组"])
        quota_col = _pick_column(df, ["录取人数"])
        remark_col = _pick_column(df, ["备注"])
        subject = "物理" if "physics" in path.name else "历史"
        for _, row in df.iterrows():
            rows.append(
                {
                    "school_code": _clean_code(_value(row, code_col)),
                    "school_name": str(_value(row, school_col)).strip(),
                    "subject_group": subject,
                    "major_group_code": _clean_code(_value(row, group_col)),
                    "major_code": _clean_code(_value(row, major_code_col)),
                    "major_name": str(_value(row, major_col)).strip(),
                    "plan_quota": _value(row, quota_col, None),
                    "tuition": None,
                    "remarks": str(_value(row, remark_col)).strip(),
                }
            )
    return rows


def _event_to_dict(event: EnrollmentDiffEvent) -> dict:
    return {
        "change_type": event.change_type,
        "school_code": event.school_code,
        "school_name": event.school_name,
        "subject_group": event.subject_group,
        "major_group_code": event.major_group_code,
        "major_code": event.major_code,
        "major_name": event.major_name,
        "before": event.before,
        "after": event.after,
        "evidence": event.evidence,
    }


EVENT_PRIORITY = {
    "new_group": 0,
    "split_or_regroup": 1,
    "quota_increase": 2,
    "tuition_change": 3,
    "new_major": 4,
    "quota_decrease": 5,
    "removed_group": 6,
    "removed_major": 7,
    "campus_or_remark_change": 8,
}


def _md(value: object) -> str:
    return str(value or "").replace("|", "\\|").replace("\n", " ")


def write_markdown(path: Path, events: list[EnrollmentDiffEvent], summary: dict[str, int], limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# 2025 Enrollment Diff Report",
        "",
        f"Events: {summary.get('event_count', 0)}",
        "",
        "## Event Counts",
        "",
        "| Change | Count |",
        "| --- | ---: |",
    ]
    for key, value in sorted(summary.items()):
        if key.endswith("_count") and key not in {"event_count", "current_group_count", "previous_group_count"}:
            lines.append(f"| `{key[:-6]}` | {value} |")
    lines.extend([
        "",
        "| Change | School | Subject | Group | Major | Before | After | Evidence |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ])
    for event in events[:limit]:
        lines.append(
            "| "
            + " | ".join(
                [
                    _md(event.change_type),
                    _md(event.school_name),
                    _md(event.subject_group),
                    _md(event.major_group_code),
                    _md(event.major_name),
                    _md(event.before),
                    _md(event.after),
                    _md(event.evidence),
                ]
            )
            + " |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit 2025 enrollment-plan opportunity diffs.")
    parser.add_argument("--current-plan", default=str(ROOT / "backend" / "data" / "2025_enrollment_full.csv"))
    parser.add_argument(
        "--previous-history",
        nargs="*",
        default=[
            str(ROOT / "backend" / "data" / "2024_physics.csv"),
            str(ROOT / "backend" / "data" / "2024_history.csv"),
        ],
    )
    parser.add_argument("--output-json", default=str(ROOT / "logs" / "enrollment_diff_2025.json"))
    parser.add_argument("--report-md", default=str(ROOT / "docs" / "2025_enrollment_diff_report.md"))
    parser.add_argument("--report-limit", type=int, default=120)
    args = parser.parse_args()

    previous = load_2024_history_rows([Path(path) for path in args.previous_history])
    current = load_2025_plan_rows(Path(args.current_plan))
    report = diff_enrollment_plans(previous, current)

    events = sorted(
        report.events,
        key=lambda event: (
            EVENT_PRIORITY.get(event.change_type, 99),
            event.school_code,
            event.subject_group,
            event.major_group_code,
            event.major_code,
        ),
    )
    output = {
        "summary": report.summary,
        "events": [_event_to_dict(event) for event in events],
    }
    output_path = Path(args.output_json)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(Path(args.report_md), events, report.summary, args.report_limit)

    print(f"saved enrollment diff json -> {output_path}")
    print(f"saved enrollment diff report -> {args.report_md}")
    print(json.dumps(report.summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
