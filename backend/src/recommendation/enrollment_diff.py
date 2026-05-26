"""Diff 2025 enrollment-plan rows against a previous plan snapshot."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable, Mapping

from evaluation.major_normalizer import normalize_major_name


@dataclass(frozen=True)
class EnrollmentDiffEvent:
    change_type: str
    school_code: str
    school_name: str
    subject_group: str
    major_group_code: str
    major_code: str = ""
    major_name: str = ""
    before: object = None
    after: object = None
    evidence: str = ""


@dataclass(frozen=True)
class EnrollmentDiffReport:
    events: list[EnrollmentDiffEvent] = field(default_factory=list)
    summary: dict[str, int] = field(default_factory=dict)


def _text(row: Mapping[str, object], key: str) -> str:
    value = row.get(key, "")
    text = str(value or "").strip()
    if text.lower() == "nan":
        return ""
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _num(row: Mapping[str, object], key: str) -> float | None:
    value = row.get(key)
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _group_key(row: Mapping[str, object]) -> tuple[str, str, str]:
    return (_text(row, "school_code"), _text(row, "subject_group"), _text(row, "major_group_code"))


def _major_key(row: Mapping[str, object]) -> tuple[str, str, str, str]:
    code = _text(row, "major_code")
    if not code:
        code = normalize_major_name(_text(row, "major_name"))
    return (*_group_key(row), code)


def _row_event(change_type: str, row: Mapping[str, object], **kwargs) -> EnrollmentDiffEvent:
    return EnrollmentDiffEvent(
        change_type=change_type,
        school_code=_text(row, "school_code"),
        school_name=_text(row, "school_name"),
        subject_group=_text(row, "subject_group"),
        major_group_code=_text(row, "major_group_code"),
        major_code=_text(row, "major_code"),
        major_name=_text(row, "major_name"),
        **kwargs,
    )


def diff_enrollment_plans(
    previous_rows: Iterable[Mapping[str, object]],
    current_rows: Iterable[Mapping[str, object]],
    *,
    quota_change_threshold: float = 0.25,
) -> EnrollmentDiffReport:
    """Detect opportunity-relevant plan changes from normalized row dicts."""
    previous = list(previous_rows)
    current = list(current_rows)
    prev_groups = {_group_key(row) for row in previous}
    curr_groups = {_group_key(row) for row in current}
    prev_major_index = {_major_key(row): row for row in previous}
    curr_major_index = {_major_key(row): row for row in current}
    events: list[EnrollmentDiffEvent] = []

    for key in sorted(curr_groups - prev_groups):
        row = next(row for row in current if _group_key(row) == key)
        events.append(_row_event("new_group", row, evidence="group absent from previous snapshot"))

    for key in sorted(prev_groups - curr_groups):
        row = next(row for row in previous if _group_key(row) == key)
        events.append(_row_event("removed_group", row, evidence="group absent from current snapshot"))

    for key, row in curr_major_index.items():
        if key not in prev_major_index:
            events.append(_row_event("new_major", row, evidence="major absent from previous snapshot"))

    for key, row in prev_major_index.items():
        if key not in curr_major_index:
            events.append(_row_event("removed_major", row, evidence="major absent from current snapshot"))

    for key in sorted(set(prev_major_index) & set(curr_major_index)):
        before_row = prev_major_index[key]
        after_row = curr_major_index[key]
        before_quota = _num(before_row, "plan_quota")
        after_quota = _num(after_row, "plan_quota")
        if before_quota and after_quota is not None:
            ratio = (after_quota - before_quota) / max(before_quota, 1.0)
            if ratio >= quota_change_threshold:
                events.append(
                    _row_event(
                        "quota_increase",
                        after_row,
                        before=before_quota,
                        after=after_quota,
                        evidence=f"quota increased by {ratio:.0%}",
                    )
                )
            elif ratio <= -quota_change_threshold:
                events.append(
                    _row_event(
                        "quota_decrease",
                        after_row,
                        before=before_quota,
                        after=after_quota,
                        evidence=f"quota decreased by {abs(ratio):.0%}",
                    )
                )

        before_tuition = _num(before_row, "tuition")
        after_tuition = _num(after_row, "tuition")
        if before_tuition is not None and after_tuition is not None and before_tuition != after_tuition:
            events.append(
                _row_event("tuition_change", after_row, before=before_tuition, after=after_tuition)
            )

        before_remarks = _text(before_row, "remarks")
        after_remarks = _text(after_row, "remarks")
        if before_remarks != after_remarks:
            events.append(
                _row_event("campus_or_remark_change", after_row, before=before_remarks, after=after_remarks)
            )

    prev_by_school_major = {
        (_text(row, "school_code"), _text(row, "subject_group"), _text(row, "major_code")): _text(row, "major_group_code")
        for row in previous
        if _text(row, "major_code")
    }
    for row in current:
        key = (_text(row, "school_code"), _text(row, "subject_group"), _text(row, "major_code"))
        previous_group = prev_by_school_major.get(key)
        if previous_group and previous_group != _text(row, "major_group_code"):
            events.append(
                _row_event(
                    "split_or_regroup",
                    row,
                    before=previous_group,
                    after=_text(row, "major_group_code"),
                    evidence="major moved across groups",
                )
            )

    type_counts: dict[str, int] = {}
    for event in events:
        type_counts[event.change_type] = type_counts.get(event.change_type, 0) + 1

    summary = {
        "previous_group_count": len(prev_groups),
        "current_group_count": len(curr_groups),
        "new_group_count": len(curr_groups - prev_groups),
        "removed_group_count": len(prev_groups - curr_groups),
        "event_count": len(events),
    }
    for change_type, count in sorted(type_counts.items()):
        summary[f"{change_type}_count"] = count
    return EnrollmentDiffReport(events=events, summary=summary)
