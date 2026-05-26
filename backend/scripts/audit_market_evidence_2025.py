"""Audit market-evidence signals against post-hoc 2025 outcomes.

This script must only be run after frozen plans are generated. It reads actual
2025 labels for evaluation, not for recommendation.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from evaluation.backtest_2025 import load_actual_outcomes_csv  # noqa: E402
from evaluation.metrics import _index_outcomes, _lookup_outcome, evaluate_volunteer_plan  # noqa: E402
from models.game_matrix import MajorGroupRow, VolunteerChoice, VolunteerPlan  # noqa: E402


def _auc(pairs: Iterable[tuple[float, float]]) -> float | None:
    pairs = list(pairs)
    pos = [(score, label) for score, label in pairs if label == 1.0]
    neg = [(score, label) for score, label in pairs if label == 0.0]
    if not pos or not neg:
        return None
    wins = 0.0
    for pos_score, _ in pos:
        for neg_score, _ in neg:
            if pos_score > neg_score:
                wins += 1.0
            elif pos_score == neg_score:
                wins += 0.5
    return wins / (len(pos) * len(neg))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _pseudo_choice(row: MajorGroupRow) -> VolunteerChoice:
    return VolunteerChoice(
        choice_index=1,
        school_code=row.school_code,
        school_name=row.school_name,
        major_group_code=row.major_group_code,
        major_choices=row.suggested_major_choices or row.major_options[:6],
        obey_adjustment=row.obey_adjustment,
        group_admission_prob=row.admission_prob,
    )


def audit_market_evidence(
    *,
    frozen_records: list[dict],
    actual_outcomes_path: Path,
    encoding: str = "utf-8-sig",
) -> dict:
    actuals = load_actual_outcomes_csv(actual_outcomes_path, encoding=encoding)
    outcome_index = _index_outcomes(actuals)

    candidate_rows: list[dict] = []
    first_hit_rows: list[dict] = []
    signal_counts: Counter[str] = Counter()
    missing_candidate_outcomes = 0

    for record in frozen_records:
        user_rank = int(record["user_rank"])
        plan = VolunteerPlan(**(record.get("plan") or record.get("volunteer_plan")))
        result = evaluate_volunteer_plan(
            plan=plan,
            actual_outcomes=actuals,
            user_rank=user_rank,
            preferred_majors=record.get("preferred_majors") or [],
            blacklist_majors=record.get("blacklist_majors") or [],
            case_id=record.get("case_id", ""),
        )
        if result.success and result.first_hit_index:
            choice = plan.choices[result.first_hit_index - 1]
            first_hit_rows.append(
                {
                    "market_evidence_strength": choice.market_evidence_strength,
                    "publicity_heat_score": choice.publicity_heat_score,
                    "publicity_rebound_risk": choice.publicity_rebound_risk,
                    "arbitrage_score": choice.arbitrage_score,
                    "front_major_arbitrage_score": choice.front_major_arbitrage_score,
                    "selected_major_hit": 1.0 if result.selected_major_hit else 0.0,
                    "preferred_major_hit": 1.0 if result.preferred_major_hit else 0.0,
                    "tail_assignment_hit": 1.0 if result.tail_assignment_hit else 0.0,
                    "assigned_major_utility": result.assigned_major_utility,
                }
            )

        for row_payload in record.get("candidate_rows") or []:
            row = MajorGroupRow(**row_payload)
            for card in row.market_evidence_cards:
                signal_counts[str(card.get("signal_type") or "unknown")] += 1
            actual = _lookup_outcome(_pseudo_choice(row), outcome_index)
            if not actual:
                missing_candidate_outcomes += 1
                continue
            group_admitted = 1.0 if user_rank <= actual.actual_group_min_rank else 0.0
            candidate_rows.append(
                {
                    "admission_prob": row.admission_prob,
                    "market_evidence_strength": row.market_evidence_strength,
                    "publicity_heat_score": row.publicity_heat_score,
                    "publicity_rebound_risk": row.publicity_rebound_risk,
                    "market_discount_score": row.market_discount_score,
                    "arbitrage_score": row.arbitrage_score,
                    "front_major_arbitrage_score": row.front_major_arbitrage_score,
                    "group_admitted": group_admitted,
                }
            )

    candidate_metrics = {
        "count": len(candidate_rows),
        "missing_outcomes": missing_candidate_outcomes,
        "signal_counts": dict(signal_counts.most_common()),
        "auc_group_admitted": {
            "admission_prob": _auc((row["admission_prob"], row["group_admitted"]) for row in candidate_rows),
            "market_discount_score": _auc((row["market_discount_score"], row["group_admitted"]) for row in candidate_rows),
            "arbitrage_score": _auc((row["arbitrage_score"], row["group_admitted"]) for row in candidate_rows),
            "front_major_arbitrage_score": _auc((row["front_major_arbitrage_score"], row["group_admitted"]) for row in candidate_rows),
            "publicity_rebound_risk": _auc((row["publicity_rebound_risk"], row["group_admitted"]) for row in candidate_rows),
        },
        "averages": {
            "market_evidence_strength": _mean([row["market_evidence_strength"] for row in candidate_rows]),
            "publicity_heat_score": _mean([row["publicity_heat_score"] for row in candidate_rows]),
            "publicity_rebound_risk": _mean([row["publicity_rebound_risk"] for row in candidate_rows]),
            "market_discount_score": _mean([row["market_discount_score"] for row in candidate_rows]),
        },
    }

    first_hit_metrics = {
        "count": len(first_hit_rows),
        "selected_major_hit_rate": _mean([row["selected_major_hit"] for row in first_hit_rows]),
        "preferred_major_hit_rate": _mean([row["preferred_major_hit"] for row in first_hit_rows]),
        "tail_assignment_hit_rate": _mean([row["tail_assignment_hit"] for row in first_hit_rows]),
        "avg_assigned_major_utility": _mean([row["assigned_major_utility"] for row in first_hit_rows]),
        "auc_preferred_major_hit": {
            "arbitrage_score": _auc((row["arbitrage_score"], row["preferred_major_hit"]) for row in first_hit_rows),
            "front_major_arbitrage_score": _auc((row["front_major_arbitrage_score"], row["preferred_major_hit"]) for row in first_hit_rows),
            "market_evidence_strength": _auc((row["market_evidence_strength"], row["preferred_major_hit"]) for row in first_hit_rows),
            "publicity_rebound_risk": _auc((row["publicity_rebound_risk"], row["preferred_major_hit"]) for row in first_hit_rows),
        },
    }

    return {
        "records": len(frozen_records),
        "actual_outcomes": len(actuals),
        "candidate_level": candidate_metrics,
        "first_hit_level": first_hit_metrics,
        "data_boundary": {
            "actual_outcomes_used_only_for_posthoc_audit": True,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit market evidence signals against 2025 outcomes.")
    parser.add_argument("--plans-jsonl", required=True)
    parser.add_argument("--actual-outcomes", required=True)
    parser.add_argument("--output", default="logs/market_evidence_2025_audit.json")
    parser.add_argument("--encoding", default="utf-8-sig")
    args = parser.parse_args()

    records = _load_jsonl(Path(args.plans_jsonl))
    result = audit_market_evidence(
        frozen_records=records,
        actual_outcomes_path=Path(args.actual_outcomes),
        encoding=args.encoding,
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved market evidence audit -> {output_path}")


if __name__ == "__main__":
    main()
