"""Offline tuning for quant calibration blends.

The tuner searches transparent feature-weight blends on choice-level
calibration rows. It does not update runtime weights automatically; it produces
candidate parameters that should be validated on a separate frozen-plan split.
"""

from __future__ import annotations

from itertools import product
from typing import Any, Sequence


FEATURES = [
    "predicted_prob",
    "quant_score",
    "rank_buffer_score",
    "history_stability_score",
    "data_confidence_score",
    "trend_score",
]
DEFAULT_STEP = 0.20
MIN_PROB_WEIGHT = 0.40
DEFAULT_HOLDOUT_FRACTION = 0.25


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _float(row: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(row.get(key, default) or default)
    except (TypeError, ValueError):
        return default


def _label(row: dict[str, Any]) -> float:
    return 1.0 if row.get("group_admitted") else 0.0


def _mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _bucket(value: float) -> str:
    if value < 0.2:
        return "00-20%"
    if value < 0.4:
        return "20-40%"
    if value < 0.6:
        return "40-60%"
    if value < 0.8:
        return "60-80%"
    return "80-100%"


def _predict(row: dict[str, Any], weights: dict[str, float]) -> float:
    return _clamp(sum(_float(row, feature) * weight for feature, weight in weights.items()))


def _bucket_error(rows: Sequence[dict[str, Any]], predictions: Sequence[float]) -> float:
    grouped: dict[str, list[tuple[float, float]]] = {}
    for row, pred in zip(rows, predictions):
        grouped.setdefault(_bucket(pred), []).append((pred, _label(row)))
    errors = [
        abs(_mean([pred for pred, _ in values]) - _mean([label for _, label in values]))
        for values in grouped.values()
        if len(values) >= 2
    ]
    return _mean(errors)


def _score_candidate(rows: Sequence[dict[str, Any]], weights: dict[str, float], name: str = "") -> dict[str, Any]:
    predictions = [_predict(row, weights) for row in rows]
    labels = [_label(row) for row in rows]
    brier = _mean([(pred - label) ** 2 for pred, label in zip(predictions, labels)])
    mae = _mean([abs(pred - label) for pred, label in zip(predictions, labels)])
    expected = _mean(predictions)
    observed = _mean(labels)
    abs_calibration = abs(expected - observed)
    bucket_abs_calibration = _bucket_error(rows, predictions)
    objective = brier + 0.35 * abs_calibration + 0.20 * bucket_abs_calibration
    return {
        "name": name,
        "weights": {key: round(value, 6) for key, value in weights.items() if value > 0},
        "choice_count": len(rows),
        "brier_score": round(brier, 6),
        "mean_absolute_error": round(mae, 6),
        "expected_admit_rate": round(expected, 6),
        "observed_admit_rate": round(observed, 6),
        "absolute_calibration_error": round(abs_calibration, 6),
        "bucket_absolute_calibration_error": round(bucket_abs_calibration, 6),
        "objective": round(objective, 6),
    }


def _candidate_key(weights: dict[str, float]) -> tuple[tuple[str, float], ...]:
    return tuple(sorted((key, round(value, 6)) for key, value in weights.items() if value > 0))


def _split_train_holdout(
    rows: Sequence[dict[str, Any]],
    *,
    holdout_fraction: float,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str]:
    if holdout_fraction <= 0.0:
        return list(rows), [], "disabled"

    case_ids = sorted({str(row.get("case_id") or "") for row in rows if row.get("case_id")})
    if len(case_ids) >= 4:
        holdout_count = max(1, min(len(case_ids) - 1, round(len(case_ids) * holdout_fraction)))
        holdout_cases = set(case_ids[-holdout_count:])
        train = [row for row in rows if str(row.get("case_id") or "") not in holdout_cases]
        holdout = [row for row in rows if str(row.get("case_id") or "") in holdout_cases]
        return train, holdout, "case_id"

    if len(rows) >= 8:
        holdout_count = max(1, min(len(rows) - 1, round(len(rows) * holdout_fraction)))
        return list(rows[:-holdout_count]), list(rows[-holdout_count:]), "row_order"

    return list(rows), [], "insufficient_rows"


def _weight_grid(*, step: float, min_prob_weight: float) -> list[dict[str, float]]:
    units = int(round(1.0 / step))
    if units <= 0:
        raise ValueError("step must be positive and no larger than 1.0")
    candidates: list[dict[str, float]] = []
    for raw in product(range(units + 1), repeat=len(FEATURES)):
        if sum(raw) != units:
            continue
        weights = {
            feature: count / units
            for feature, count in zip(FEATURES, raw)
            if count > 0
        }
        if weights.get("predicted_prob", 0.0) < min_prob_weight:
            continue
        candidates.append(weights)
    return candidates


def _named_baselines() -> list[tuple[str, dict[str, float]]]:
    return [
        ("current_probability_only", {"predicted_prob": 1.0}),
        ("runtime_quant_blend", {"predicted_prob": 0.85, "quant_score": 0.15}),
        (
            "balanced_scorecard",
            {
                "predicted_prob": 0.55,
                "quant_score": 0.15,
                "rank_buffer_score": 0.12,
                "history_stability_score": 0.08,
                "data_confidence_score": 0.07,
                "trend_score": 0.03,
            },
        ),
    ]


def tune_quant_probability_blends(
    *,
    choice_rows: Sequence[dict[str, Any]],
    step: float = DEFAULT_STEP,
    min_prob_weight: float = MIN_PROB_WEIGHT,
    holdout_fraction: float = DEFAULT_HOLDOUT_FRACTION,
    top_k: int = 10,
) -> dict[str, Any]:
    """Search transparent probability/scorecard blends on calibration rows."""
    rows = [
        row
        for row in choice_rows
        if "group_admitted" in row and any(feature in row for feature in FEATURES)
    ]
    if not rows:
        return {
            "choice_count": 0,
            "best": None,
            "baseline": None,
            "top_candidates": [],
            "warning": "No usable choice rows were provided.",
        }

    train_rows, holdout_rows, split_method = _split_train_holdout(
        rows,
        holdout_fraction=holdout_fraction,
    )
    baseline = _score_candidate(train_rows, {"predicted_prob": 1.0}, name="current_probability_only")
    scored_by_key: dict[tuple[tuple[str, float], ...], dict[str, Any]] = {}
    for name, weights in _named_baselines():
        scored = _score_candidate(train_rows, weights, name=name)
        scored_by_key[_candidate_key(scored["weights"])] = scored
    for weights in _weight_grid(step=step, min_prob_weight=min_prob_weight):
        scored = _score_candidate(train_rows, weights)
        scored_by_key[_candidate_key(scored["weights"])] = scored

    scored = sorted(scored_by_key.values(), key=lambda item: (item["objective"], item["brier_score"]))
    holdout_baseline = (
        _score_candidate(holdout_rows, {"predicted_prob": 1.0}, name="current_probability_only")
        if holdout_rows
        else None
    )
    if holdout_baseline:
        baseline["holdout"] = holdout_baseline
    for index, candidate in enumerate(scored, 1):
        if not candidate.get("name"):
            candidate["name"] = f"grid_candidate_{index:03d}"
        candidate["brier_delta_vs_current"] = round(
            float(candidate["brier_score"]) - float(baseline["brier_score"]),
            6,
        )
        candidate["objective_delta_vs_current"] = round(
            float(candidate["objective"]) - float(baseline["objective"]),
            6,
        )
        if holdout_rows:
            holdout_score = _score_candidate(
                holdout_rows,
                candidate["weights"],
                name=str(candidate.get("name") or ""),
            )
            holdout_score["brier_delta_vs_current"] = round(
                float(holdout_score["brier_score"]) - float(holdout_baseline["brier_score"]),
                6,
            )
            holdout_score["objective_delta_vs_current"] = round(
                float(holdout_score["objective"]) - float(holdout_baseline["objective"]),
                6,
            )
            candidate["holdout"] = holdout_score

    best = scored[0]
    return {
        "choice_count": len(rows),
        "train_choice_count": len(train_rows),
        "holdout_choice_count": len(holdout_rows),
        "feature_names": FEATURES,
        "search": {
            "step": step,
            "min_prob_weight": min_prob_weight,
            "holdout_fraction": holdout_fraction,
            "split_method": split_method,
            "candidate_count": len(scored),
            "objective": "brier + 0.35 * abs_calibration + 0.20 * bucket_abs_calibration",
        },
        "baseline": baseline,
        "holdout_baseline": holdout_baseline,
        "best": best,
        "top_candidates": scored[:top_k],
        "deployment_note": (
            "Use these weights as candidates only. Prefer candidates that improve holdout metrics; "
            "validate again on a later frozen-plan split before changing runtime scoring."
        ),
    }


def build_markdown_quant_tuning_report(result: dict[str, Any]) -> str:
    """Build a compact Markdown report for tuning results."""
    lines = [
        "# Quant Probability Tuning Report",
        "",
        f"Choices: {result.get('choice_count', 0)}",
        f"Train choices: {result.get('train_choice_count', 0)}",
        f"Holdout choices: {result.get('holdout_choice_count', 0)}",
        "",
        result.get("deployment_note", ""),
        "",
    ]
    baseline = result.get("baseline") or {}
    best = result.get("best") or {}
    lines.extend(
        [
            "## Summary",
            "",
            "| Model | Split | Objective | Brier | Abs Calib Err | Bucket Calib Err | Weights |",
            "| --- | --- | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for label, row in [("baseline", baseline), ("best", best)]:
        if not row:
            continue
        for split, split_row in [("train", row), ("holdout", row.get("holdout"))]:
            if not split_row:
                continue
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{label}:{row.get('name', '')}`",
                        split,
                        f"{float(split_row.get('objective', 0.0)):.3f}",
                        f"{float(split_row.get('brier_score', 0.0)):.3f}",
                        f"{float(split_row.get('absolute_calibration_error', 0.0)):.1%}",
                        f"{float(split_row.get('bucket_absolute_calibration_error', 0.0)):.1%}",
                        "`" + str(row.get("weights", {})) + "`",
                    ]
                )
                + " |"
            )

    lines.extend(
        [
            "",
            "## Top Candidates",
            "",
            "| Rank | Name | Train Objective | Holdout Objective | Holdout Brier Delta | Weights |",
            "| ---: | --- | ---: | ---: | ---: | --- |",
        ]
    )
    for index, row in enumerate(result.get("top_candidates", []) or [], 1):
        holdout = row.get("holdout") or {}
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    f"`{row.get('name', '')}`",
                    f"{float(row.get('objective', 0.0)):.3f}",
                    f"{float(holdout.get('objective', 0.0)):.3f}" if holdout else "",
                    f"{float(holdout.get('brier_delta_vs_current', 0.0)):.3f}" if holdout else "",
                    "`" + str(row.get("weights", {})) + "`",
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"
