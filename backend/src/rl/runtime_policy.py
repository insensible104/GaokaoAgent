"""Runtime helpers for bringing RL artifacts into the online recommendation flow."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from models.game_matrix import MajorGroupRow, StrategyTag
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from rl.learnable_prompt import LearnablePrompt, PromptParameters
from rl.volunteer_combination_optimizer import (
    VolunteerCandidate,
    VolunteerCombination,
    VolunteerCombinationOptimizer,
)
from utils.city_mapping import get_school_city


class RLRuntimePolicy:
    """Load RL checkpoints and apply them to online recommendation selection."""

    def __init__(self, checkpoint_path: Optional[str] = None):
        backend_root = Path(__file__).resolve().parents[2]
        default_checkpoint = backend_root / "rl_checkpoints" / "final_checkpoint.json"

        self.checkpoint_path = Path(checkpoint_path) if checkpoint_path else default_checkpoint
        self.learnable_prompt = LearnablePrompt()
        self.is_loaded = False
        self.policy_source = "default"

        if self.checkpoint_path.exists():
            try:
                self.learnable_prompt.load(str(self.checkpoint_path))
                self.is_loaded = True
                self.policy_source = str(self.checkpoint_path)
            except Exception as exc:
                print(f"[WARN] RL runtime policy load failed: {exc}")

    def get_effective_params(self, profile: UserProfile) -> PromptParameters:
        """Blend learned policy params with current user preferences."""
        base_params = self.learnable_prompt.best_params or self.learnable_prompt.params
        params = PromptParameters(**base_params.model_dump())

        user_risk = {
            RiskTolerance.CONSERVATIVE: 0.2,
            RiskTolerance.BALANCED: 0.5,
            RiskTolerance.AGGRESSIVE: 0.8,
        }.get(profile.risk_tolerance, 0.5)
        params.risk_tolerance = (params.risk_tolerance * 0.6) + (user_risk * 0.4)

        if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
            params.prestige_weight = min(1.0, params.prestige_weight + 0.15)
        elif profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
            params.prestige_weight = max(0.2, params.prestige_weight - 0.15)

        return params

    def get_recommendation_mix(
        self,
        total_count: int,
        profile: UserProfile,
    ) -> Dict[str, int]:
        """Return an RL-adjusted rush/target/safe mix."""
        params = self.get_effective_params(profile)
        rush_ratio = params.rush_ratio
        target_ratio = params.target_ratio
        safe_ratio = params.safe_ratio

        if profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
            rush_ratio = min(0.45, rush_ratio + 0.05)
            safe_ratio = max(0.15, safe_ratio - 0.05)
        elif profile.risk_tolerance == RiskTolerance.CONSERVATIVE:
            rush_ratio = max(0.15, rush_ratio - 0.05)
            safe_ratio = min(0.35, safe_ratio + 0.05)

        total_ratio = rush_ratio + target_ratio + safe_ratio
        rush_ratio /= total_ratio
        target_ratio /= total_ratio
        safe_ratio /= total_ratio

        rush_count = int(total_count * rush_ratio)
        target_count = int(total_count * target_ratio)
        safe_count = max(0, total_count - rush_count - target_count)

        return {
            "rush": rush_count,
            "target": target_count,
            "safe": safe_count,
            "total": total_count,
        }

    def select_candidates(
        self,
        rows: List[MajorGroupRow],
        profile: UserProfile,
        total_count: int,
    ) -> Tuple[List[MajorGroupRow], Dict[str, Any]]:
        """Greedily select candidates with learned ratios and diversity-aware reranking."""
        if not rows:
            return [], self._empty_summary()

        mix = self.get_recommendation_mix(total_count, profile)
        by_strategy = {
            StrategyTag.RUSH: [r for r in rows if r.strategy_tag == StrategyTag.RUSH],
            StrategyTag.TARGET: [r for r in rows if r.strategy_tag == StrategyTag.TARGET],
            StrategyTag.SAFE: [r for r in rows if r.strategy_tag == StrategyTag.SAFE],
        }

        effective_params = self.get_effective_params(profile)
        city_counts: Dict[str, int] = defaultdict(int)
        selected: List[MajorGroupRow] = []

        for strategy, needed in (
            (StrategyTag.RUSH, mix["rush"]),
            (StrategyTag.TARGET, mix["target"]),
            (StrategyTag.SAFE, mix["safe"]),
        ):
            ranked = self._greedy_rank(by_strategy[strategy], effective_params, city_counts)
            picked = ranked[:needed]
            selected.extend(picked)
            for row in picked:
                city_counts[get_school_city(row.school_name)] += 1

        if len(selected) < total_count:
            remaining = [row for row in rows if row not in selected]
            ranked_remaining = self._greedy_rank(remaining, effective_params, city_counts)
            for row in ranked_remaining[: total_count - len(selected)]:
                selected.append(row)
                city_counts[get_school_city(row.school_name)] += 1

        portfolio_summary = self.optimize_portfolio(selected, profile)

        return selected, {
            "policy_source": self.policy_source,
            "checkpoint_loaded": self.is_loaded,
            "mix": mix,
            "effective_params": {
                "risk_tolerance": round(effective_params.risk_tolerance, 3),
                "diversity_weight": round(effective_params.diversity_weight, 3),
                "prestige_weight": round(effective_params.prestige_weight, 3),
                "rush_ratio": round(effective_params.rush_ratio, 3),
                "target_ratio": round(effective_params.target_ratio, 3),
                "safe_ratio": round(effective_params.safe_ratio, 3),
            },
            "selected_count": len(selected),
            "portfolio": portfolio_summary,
        }

    def optimize_portfolio(
        self,
        rows: List[MajorGroupRow],
        profile: UserProfile,
    ) -> Dict[str, Any]:
        """Use the ILP optimizer to build a final 10-volunteer portfolio summary."""
        if len(rows) < 10:
            return {
                "generated": False,
                "reason": "not_enough_candidates",
                "available_candidates": len(rows),
            }

        candidates = [
            VolunteerCandidate(
                index=i,
                school_name=row.school_name,
                major_group=row.major_group_code,
                major_list=row.major_list,
                admission_prob=row.admission_prob,
                major_satisfaction=row.comprehensive_score,
                school_tier_score=row.comprehensive_score,
                comprehensive_score=row.comprehensive_score,
                adjustment_risk=row.adjustment_risk,
                strategy_type=row.strategy_tag.value,
                city=get_school_city(row.school_name),
            )
            for i, row in enumerate(rows[: min(len(rows), 30)])
        ]

        user_preferences = {
            "major_satisfaction": 0.45,
            "school_tier": 0.25,
            "admission_prob": 0.30,
        }
        if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
            user_preferences = {
                "major_satisfaction": 0.20,
                "school_tier": 0.50,
                "admission_prob": 0.30,
            }
        elif profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
            user_preferences = {
                "major_satisfaction": 0.50,
                "school_tier": 0.15,
                "admission_prob": 0.35,
            }

        optimizer = VolunteerCombinationOptimizer()
        combinations = optimizer.optimize_combinations(
            candidates=candidates,
            user_preferences=user_preferences,
            num_combinations=4,
        )
        if not combinations:
            return {
                "generated": False,
                "reason": "optimizer_failed",
            }

        chosen = self._choose_combination(combinations, profile)
        selected_keys = [
            f"{v.school_name}::{v.major_group}"
            for v in chosen.volunteers
        ]
        return {
            "generated": True,
            "style_name": chosen.style_name,
            "style_description": chosen.style_description,
            "avg_admission_prob": round(chosen.avg_admission_prob, 4),
            "avg_major_satisfaction": round(chosen.avg_major_satisfaction, 4),
            "rush_count": chosen.rush_count,
            "target_count": chosen.target_count,
            "safe_count": chosen.safe_count,
            "admission_guarantee": round(chosen.admission_guarantee, 4),
            "major_guarantee": round(chosen.major_guarantee, 4),
            "selected_keys": selected_keys,
            "candidate_styles": [
                {
                    "style_name": combo.style_name,
                    "rush_count": combo.rush_count,
                    "target_count": combo.target_count,
                    "safe_count": combo.safe_count,
                    "avg_admission_prob": round(combo.avg_admission_prob, 4),
                }
                for combo in combinations
            ],
        }

    def _empty_summary(self) -> Dict[str, Any]:
        return {
            "policy_source": self.policy_source,
            "checkpoint_loaded": self.is_loaded,
            "mix": {"rush": 0, "target": 0, "safe": 0, "total": 0},
            "effective_params": {},
            "selected_count": 0,
            "portfolio": {"generated": False, "reason": "no_candidates"},
        }

    def _greedy_rank(
        self,
        rows: List[MajorGroupRow],
        params: PromptParameters,
        city_counts: Dict[str, int],
    ) -> List[MajorGroupRow]:
        working_city_counts = defaultdict(int, city_counts)
        ranked: List[MajorGroupRow] = []
        remaining = rows[:]

        while remaining:
            best_row = max(
                remaining,
                key=lambda row: self._policy_score(row, params, working_city_counts),
            )
            ranked.append(best_row)
            working_city_counts[get_school_city(best_row.school_name)] += 1
            remaining.remove(best_row)

        return ranked

    def _policy_score(
        self,
        row: MajorGroupRow,
        params: PromptParameters,
        city_counts: Dict[str, int],
    ) -> float:
        if row.strategy_tag == StrategyTag.RUSH:
            prob_fit = 1.0 - min(
                1.0,
                abs(row.admission_prob - (params.rush_prob_threshold * 0.85))
                / max(params.rush_prob_threshold, 0.1),
            )
        elif row.strategy_tag == StrategyTag.TARGET:
            target_center = (params.target_prob_min + params.target_prob_max) / 2
            prob_fit = 1.0 - min(1.0, abs(row.admission_prob - target_center) / 0.25)
        else:
            prob_fit = row.admission_prob

        city = get_school_city(row.school_name)
        diversity_penalty = city_counts[city] * params.diversity_weight * 0.08
        safety_component = (1.0 - params.risk_tolerance) * row.admission_prob
        prestige_component = params.prestige_weight * row.comprehensive_score
        quality_component = (1.0 - params.prestige_weight) * prob_fit
        arbitrage_component = (
            0.14 * row.arbitrage_score
            + 0.16 * row.front_major_arbitrage_score
            + 0.06 * row.front_major_hit_prob
            + 0.06 * row.segment_demand_score
            + 0.03 * row.low_attention_signal
            + (0.06 if "front_major_arbitrage_pool" in row.opportunity_pools else 0.0)
            + (0.04 if "relative_tier_lift_pool" in row.opportunity_pools else 0.0)
        )
        rebound_penalty = max(row.rebound_risk, row.segment_rebound_risk) * 0.07
        risk_penalty = row.adjustment_risk * (0.15 + (1.0 - params.risk_tolerance) * 0.1)
        tail_penalty = row.tail_assignment_risk * (0.10 + (1.0 - params.risk_tolerance) * 0.08)
        guard_penalty = 0.0
        if row.tail_assignment_risk > 0.55:
            guard_penalty += 0.12
        if max(row.rebound_risk, row.segment_rebound_risk) > 0.55:
            guard_penalty += 0.08
        if row.major_utility_mean < 0.45:
            guard_penalty += 0.06
        blacklist_penalty = 0.12 if row.is_blacklist_risk else 0.0

        return (
            prestige_component
            + quality_component
            + safety_component
            + arbitrage_component
            + (0.10 * (1.0 - row.adjustment_risk))
            - risk_penalty
            - tail_penalty
            - rebound_penalty
            - guard_penalty
            - blacklist_penalty
            - diversity_penalty
        )

    def _choose_combination(
        self,
        combinations: List[VolunteerCombination],
        profile: UserProfile,
    ) -> VolunteerCombination:
        if profile.risk_tolerance == RiskTolerance.AGGRESSIVE:
            return max(
                combinations,
                key=lambda combo: (combo.rush_count, combo.total_utility),
            )
        if profile.risk_tolerance == RiskTolerance.CONSERVATIVE:
            return max(
                combinations,
                key=lambda combo: (combo.safe_count, combo.avg_admission_prob, combo.total_utility),
            )
        if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_SCHOOL:
            return max(
                combinations,
                key=lambda combo: (combo.total_utility, combo.avg_major_satisfaction),
            )
        if profile.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR:
            return max(
                combinations,
                key=lambda combo: (combo.avg_major_satisfaction, combo.total_utility),
            )
        return max(
            combinations,
            key=lambda combo: (
                combo.total_utility,
                combo.avg_admission_prob,
                combo.avg_major_satisfaction,
            ),
        )
