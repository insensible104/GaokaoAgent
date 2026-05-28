"""Attach enrollment-plan diff signals to recommendation rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from models.game_matrix import MajorGroupRow
from recommendation.enrollment_diff import EnrollmentDiffEvent


CHANGE_WEIGHTS = {
    "new_group": 0.42,
    "split_or_regroup": 0.36,
    "quota_increase": 0.28,
    "new_major": 0.20,
    "tuition_change": 0.16,
    "campus_or_remark_change": 0.10,
    "quota_decrease": -0.12,
    "removed_group": -0.30,
    "removed_major": -0.18,
}


def _norm(value: object) -> str:
    text = str(value or "").strip().lower()
    if text in {"physics", "物理类", "物理", "物"}:
        return "physics"
    if text in {"history", "历史类", "历史", "历"}:
        return "history"
    if text.endswith(".0"):
        text = text[:-2]
    return text


def _event_key(event: EnrollmentDiffEvent) -> tuple[str, str, str]:
    return (_norm(event.school_code), _norm(event.subject_group), _norm(event.major_group_code))


def _row_key(row: MajorGroupRow, subject_group: str | None) -> tuple[str, str, str]:
    return (_norm(row.school_code), _norm(subject_group), _norm(row.major_group_code))


def _score_events(events: list[EnrollmentDiffEvent], row: MajorGroupRow) -> float:
    unique_types = {event.change_type for event in events}
    raw = sum(CHANGE_WEIGHTS.get(change_type, 0.0) for change_type in unique_types)
    raw += min(0.12, max(0, len(events) - len(unique_types)) * 0.015)
    if row.tail_assignment_risk >= 0.60:
        raw -= 0.25
    if row.is_blacklist_risk:
        raw -= 0.20
    if row.admission_prob < 0.35:
        raw -= 0.10
    return max(0.0, min(1.0, raw))


def attach_plan_change_signals(
    rows: Iterable[MajorGroupRow],
    events: Iterable[EnrollmentDiffEvent],
    *,
    subject_group: str | None = None,
) -> list[MajorGroupRow]:
    """Attach opportunity-relevant enrollment-plan changes to matching rows."""
    index: dict[tuple[str, str, str], list[EnrollmentDiffEvent]] = defaultdict(list)
    for event in events:
        index[_event_key(event)].append(event)

    updated = list(rows)
    for row in updated:
        matching_events = index.get(_row_key(row, subject_group), [])
        if not matching_events:
            continue

        row.plan_change_score = _score_events(matching_events, row)
        row.plan_change_types = sorted({event.change_type for event in matching_events})
        row.plan_change_evidence = [
            (
                f"{event.change_type}: {event.major_name or event.major_group_code}"
                + (f" ({event.evidence})" if event.evidence else "")
            )
            for event in matching_events[:8]
        ]
        if row.plan_change_score >= 0.35 and "plan_change_pool" not in row.opportunity_pools:
            row.opportunity_pools.append("plan_change_pool")
        if row.plan_change_score >= 0.35:
            note = f"plan_change_signal:{','.join(row.plan_change_types[:3])}"
            if note not in row.market_behavior_notes:
                row.market_behavior_notes.append(note)
    return updated
