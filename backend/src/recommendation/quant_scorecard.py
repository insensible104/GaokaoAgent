"""Deterministic quant scorecard for major-group recommendations.

The scorecard keeps the primary admissions model explainable: rank buffer,
historical stability, trend, and data confidence are separated instead of
collapsed into a pseudo-precise probability.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class QuantScorecard:
    quant_score: float
    rank_buffer_score: float
    history_stability_score: float
    data_confidence_score: float
    trend_score: float
    deterministic_risk_band: str
    rank_buffer: int
    uncertainty_width: float
    evidence: list[str] = field(default_factory=list)


def _risk_band(rank_buffer: int, uncertainty_width: float) -> str:
    z = rank_buffer / max(uncertainty_width, 1.0)
    if z < -1.0:
        return "far_rush"
    if z < 0.0:
        return "boundary_rush"
    if z < 1.0:
        return "thin_target"
    if z < 2.0:
        return "solid_target"
    return "safe_anchor"


def _trend_score(hist_data: pd.DataFrame, user_rank: int) -> tuple[float, float]:
    if hist_data.empty or len(hist_data) < 2 or "year" not in hist_data.columns:
        return 0.5, 0.0

    ordered = hist_data.sort_values("year")
    years = [float(value) for value in ordered["year"].tolist()]
    ranks = [float(value) for value in ordered["min_rank"].tolist()]
    year_mean = sum(years) / len(years)
    rank_mean = sum(ranks) / len(ranks)
    denominator = sum((year - year_mean) ** 2 for year in years)
    if denominator <= 0:
        return 0.5, 0.0
    slope = sum(
        (year - year_mean) * (rank - rank_mean)
        for year, rank in zip(years, ranks)
    ) / denominator
    trend_ratio = slope / max(float(user_rank), 1.0)
    return _clamp(0.5 + trend_ratio * 8.0), trend_ratio


def build_quant_scorecard(
    *,
    hist_data: pd.DataFrame,
    user_rank: int,
    min_rank_pred: int,
    rank_ci_lower: int,
    rank_ci_upper: int,
    quota_stability: float,
) -> QuantScorecard:
    ranks = [
        float(value)
        for value in hist_data.get("min_rank", pd.Series(dtype=float)).dropna().tolist()
    ]
    year_count = len(ranks)
    rank_buffer = int(min_rank_pred - user_rank)

    if ranks:
        history_span = max(ranks) - min(ranks)
    else:
        history_span = float(max(rank_ci_upper - rank_ci_lower, user_rank * 0.10))

    ci_width = max(0.0, float(rank_ci_upper - rank_ci_lower))
    uncertainty_width = max(
        history_span / 2.0,
        ci_width / 3.92 if ci_width else 0.0,
        user_rank * 0.03,
        1.0,
    )
    buffer_z = rank_buffer / uncertainty_width
    rank_buffer_score = _clamp(0.5 + buffer_z / 4.0)

    volatility_ratio = history_span / max(float(user_rank), 1.0)
    history_stability_score = 1.0 - _clamp(volatility_ratio / 1.25)

    trend_score, trend_ratio = _trend_score(hist_data, user_rank)
    volatility_penalty = _clamp(volatility_ratio * 0.45)
    data_confidence_score = _clamp(
        0.18
        + min(year_count, 4) * 0.13
        + _clamp(quota_stability) * 0.25
        + history_stability_score * 0.20
        - volatility_penalty
    )

    quant_score = _clamp(
        rank_buffer_score * 0.40
        + history_stability_score * 0.22
        + data_confidence_score * 0.18
        + _clamp(quota_stability) * 0.12
        + trend_score * 0.08
    )
    band = _risk_band(rank_buffer, uncertainty_width)

    trend_label = "趋于放宽" if trend_ratio > 0.015 else ("趋于收紧" if trend_ratio < -0.015 else "基本稳定")
    evidence = [
        f"位次缓冲 {rank_buffer:+d} 名，约 {buffer_z:.2f} 个不确定性宽度",
        f"历史跨度约 {int(history_span)} 名，稳定性评分 {history_stability_score:.2f}",
        f"近年趋势{trend_label}，趋势评分 {trend_score:.2f}",
        f"数据年数 {year_count}，数据置信度 {data_confidence_score:.2f}",
    ]

    return QuantScorecard(
        quant_score=round(quant_score, 4),
        rank_buffer_score=round(rank_buffer_score, 4),
        history_stability_score=round(history_stability_score, 4),
        data_confidence_score=round(data_confidence_score, 4),
        trend_score=round(trend_score, 4),
        deterministic_risk_band=band,
        rank_buffer=rank_buffer,
        uncertainty_width=round(uncertainty_width, 2),
        evidence=evidence,
    )
