"""Agent 2: 博弈推荐智能体（专业组级别）"""
import os
import pandas as pd
from datetime import date
from pathlib import Path
from typing import Any, Sequence
from langchain_core.messages import AIMessage

from models.state import SupervisorState
from models.game_matrix import GameMatrix, MajorGroupRow, StrategyTag, VolatilityLevel
from engines.enrollment_loader import EnrollmentPlanLoader
from engines.quant_engine import GaokaoQuantEngine
from engines.monte_carlo_sim import monte_carlo_admission_probability
from engines.probability import classify_strategy_tag, calculate_admission_probability
from recommendation.policy_config import TAIL_RISK_SCORE_PENALTY_WEIGHT
from recommendation.bundle_risk import (
    analyze_bundle_risk,
    quota_bucket,
    quota_stability_score,
    variance_opportunity_score,
)
from recommendation.major_choice_planner import (
    build_major_options_from_records,
    build_volunteer_plan,
    choose_six_majors,
    format_plan_probability_range,
)
from recommendation.major_utility import score_major_options
from recommendation.school_signal import score_school_major_signal
from recommendation.tradeoff_policy import score_tradeoff
from recommendation.arbitrage_adapter import score_major_group_arbitrage
from recommendation.quant_scorecard import build_quant_scorecard
from recommendation.data_vintage import inspect_recommendation_data_vintage
from recommendation.decision_trace import build_decision_trace
from recommendation.plan_change_explanation import build_plan_change_explanation
from recommendation.plan_change_signals import attach_plan_change_signals, load_online_plan_change_events
from recommendation.probability_calibration import (
    calibrate_probability,
    load_probability_calibration,
)
from recommendation.strategy_coverage import (
    build_coverage_report,
    count_strategy_rows,
    fill_plan_capacity,
    retain_strategy_candidates,
)
from evaluation.plan_audit import build_plan_audit_summary
from utils.agent_bus import publish_agent_message, remember
from utils.city_mapping import get_school_city, calculate_city_preference_score
from rl.rank_gradient_strategy import RankGradientStrategy
from rl.runtime_policy import RLRuntimePolicy


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def _normalize_percent_score(value: float) -> float:
    return _clamp01(value / 100.0)


def _prepare_strategy_candidate_pool(
    rows: Sequence[MajorGroupRow],
    *,
    desired: dict[str, int],
    reserve: int = 3,
) -> list[MajorGroupRow]:
    """Pareto-rank within each strategy while preserving mix capacity."""
    return retain_strategy_candidates(rows, desired=desired, reserve=reserve)


def _resolve_plan_change_diff_path() -> Path | None:
    configured = os.getenv("GAOKAO_PLAN_CHANGE_DIFF")
    candidates = [
        Path(configured) if configured else None,
        Path(__file__).resolve().parents[3] / "logs" / "enrollment_diff_2025.json",
    ]
    return next((path for path in candidates if path and path.exists()), None)


def _resolve_probability_calibration_path() -> Path | None:
    configured = os.getenv("GAOKAO_PROBABILITY_CALIBRATION")
    candidates = [
        Path(configured) if configured else None,
        Path(__file__).resolve().parents[2] / "data" / "probability_calibration_2025.json",
    ]
    return next((path for path in candidates if path and path.exists()), None)


def _calibrate_online_probability(
    raw_probability: float,
    calibration_path: str | Path | None,
    *,
    subject_group: str | None = None,
) -> tuple[float, dict[str, Any]]:
    raw = _clamp01(raw_probability)
    artifact = load_probability_calibration(str(Path(calibration_path).resolve())) if calibration_path else None
    if artifact is None:
        return raw, {
            "raw_admission_prob": raw,
            "probability_is_calibrated": False,
            "probability_method": "historical_rank_monte_carlo_uncalibrated",
            "probability_calibration_year": None,
            "probability_hazard_scale": 1.0,
            "probability_calibration_source": "",
        }
    probability_method = (
        "historical_beta_subject"
        if artifact.method == "beta_subject"
        else "historical_isotonic"
    )
    return calibrate_probability(raw, artifact, subject_group=subject_group), {
        "raw_admission_prob": raw,
        "probability_is_calibrated": True,
        "probability_method": probability_method,
        "probability_calibration_year": artifact.calibration_year,
        "probability_hazard_scale": artifact.subsequent_choice_hazard_scale,
        "probability_calibration_source": artifact.source,
    }


def _attach_online_plan_changes(
    rows: Sequence[MajorGroupRow],
    *,
    subject_group: str,
    diff_path: str | Path | None,
) -> int:
    if diff_path:
        attach_plan_change_signals(
            rows,
            load_online_plan_change_events(diff_path),
            subject_group=subject_group,
        )
    attached = 0
    for row in rows:
        row.plan_change_explanation = build_plan_change_explanation(row)
        if row.plan_change_details:
            attached += 1
    return attached


def _extract_research_evidence_cards(state: dict) -> list[dict[str, Any]]:
    """Read source-aware research cards from supervisor state."""
    cards = state.get("research_evidence_cards") or []
    return [dict(card) for card in cards if isinstance(card, dict)]


def _dedupe_strings(values: Sequence[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value)
        if text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def _dedupe_evidence_cards(cards: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for card in cards:
        key = (
            str(card.get("signal_type") or ""),
            str(card.get("source") or ""),
            str(card.get("claim") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(dict(card))
    return deduped


def _city_preference_from_tradeoff(row: MajorGroupRow) -> float:
    """Approximate the original city-preference score from saved tradeoff features."""
    city_value = (row.tradeoff_breakdown or {}).get("city_value")
    if city_value is None:
        return 1.0
    city_value = _clamp01(float(city_value))
    if city_value <= 0.10:
        return 0.50
    if city_value >= 1.0:
        return 1.30
    return max(0.50, min(1.30, city_value + 0.50))


def _score_row_arbitrage(
    *,
    row: MajorGroupRow,
    profile,
    school_major_score: float,
    city_preference_score: float,
    research_evidence_cards: Sequence[dict[str, Any]] | None = None,
) -> object:
    """Attach arbitrage signals, optionally using deep-research evidence cards."""
    return score_major_group_arbitrage(
        row=row,
        profile=profile,
        school_major_score=school_major_score,
        city_preference_score=city_preference_score,
        research_evidence_cards=research_evidence_cards,
    )


def refresh_game_matrix_research_evidence(state: dict) -> dict:
    """Refresh an existing game matrix after slow-loop research produces evidence.

    This is intentionally not a candidate-regeneration step. It preserves the
    selected candidate set and reapplies the deterministic prefix optimizer after
    updating market evidence so a late refresh cannot destroy volunteer ordering.
    """
    matrix = state.get("game_matrix")
    profile = state.get("user_profile")
    cards = _extract_research_evidence_cards(state)
    rows = list(getattr(matrix, "major_group_rows", []) or []) if matrix else []
    if not matrix or not profile or not cards or not rows:
        return {
            "current_agent": "research_evidence_refresh",
            "debug_logs": ["[ResearchEvidenceRefresh] skipped: missing matrix, profile, evidence, or rows."],
        }

    refreshed = 0
    for row in rows:
        before_score = float(getattr(row, "plan_change_score", 0.0) or 0.0)
        _score_row_arbitrage(
            row=row,
            profile=profile,
            school_major_score=float((row.tradeoff_breakdown or {}).get("school_value", row.comprehensive_score)),
            city_preference_score=_city_preference_from_tradeoff(row),
            research_evidence_cards=cards,
        )
        row.plan_change_types = _dedupe_strings(row.plan_change_types)
        row.plan_change_evidence = _dedupe_strings(row.plan_change_evidence)
        row.audit_flags = _dedupe_strings(row.audit_flags)
        row.market_behavior_notes = _dedupe_strings(row.market_behavior_notes)
        row.market_evidence_cards = _dedupe_evidence_cards(row.market_evidence_cards)
        row.plan_change_explanation = build_plan_change_explanation(row)
        row.decision_trace = build_decision_trace(row)
        if float(getattr(row, "plan_change_score", 0.0) or 0.0) > before_score:
            refreshed += 1

    existing_plan = getattr(matrix, "volunteer_plan", None)
    max_choices = len(existing_plan.choices) if existing_plan else len(rows)
    matrix.volunteer_plan = build_volunteer_plan(
        rows,
        profile,
        max_choices=max_choices,
        optimize_prefix=True,
    )
    matrix.calculate_statistics()
    return {
        "game_matrix": matrix,
        "current_agent": "research_evidence_refresh",
        "debug_logs": [
            (
                f"[ResearchEvidenceRefresh] refreshed {len(rows)} rows with "
                f"{len(cards)} research cards; plan_change_score improved on {refreshed} rows."
            )
        ],
    }


def _major_keyword_score(majors, preferred_majors) -> float:
    if not preferred_majors:
        return 0.0
    major_text = " ".join(str(major) for major in (majors or []))
    if not major_text:
        return 0.0
    hits = sum(1 for keyword in preferred_majors if keyword and keyword in major_text)
    return min(1.0, hits / max(len(preferred_majors), 1))


def _cheap_candidate_priority(group, profile) -> float:
    """Rank candidates before expensive probability simulation."""
    min_rank = float(group.get("min_rank", profile.rank) or profile.rank)
    rank_distance = abs(min_rank - profile.rank)
    rank_closeness = 1.0 - min(rank_distance / max(float(profile.rank), 5000.0), 2.0) / 2.0
    city_score = calculate_city_preference_score(
        city=get_school_city(str(group.get("school", ""))),
        preferred_cities=profile.preferred_cities,
        excluded_cities=profile.excluded_cities,
    )
    major_score = _major_keyword_score(group.get("major", []), profile.preferred_majors)
    quota = float(group.get("quota", 0) or 0)
    quota_signal = min(0.4, quota / 500.0)
    return major_score * 2.0 + city_score * 1.1 + rank_closeness * 1.2 + quota_signal


def _take_priority_rows(df: pd.DataFrame, count: int, profile) -> pd.DataFrame:
    if count <= 0 or df.empty:
        return df.head(0)
    ranked = df.copy()
    ranked["_precision_priority"] = ranked.apply(
        lambda row: _cheap_candidate_priority(row, profile),
        axis=1,
    )
    ranked = ranked.sort_values(
        ["_precision_priority", "min_rank"],
        ascending=[False, True],
    )
    return ranked.head(count).drop(columns=["_precision_priority"], errors="ignore")


def _limit_precision_candidates(
    major_groups: pd.DataFrame,
    profile,
    *,
    total_recommend: int,
    max_candidates: int | None = None,
) -> pd.DataFrame:
    """Limit expensive Monte Carlo work with stratified, preference-aware sampling."""
    if major_groups.empty:
        return major_groups

    if max_candidates is None:
        max_candidates = int(os.getenv(
            "GAOKAO_MAX_PRECISION_CANDIDATES",
            str(max(180, total_recommend * 12)),
        ))

    max_candidates = max(total_recommend * 4, max_candidates)
    if len(major_groups) <= max_candidates:
        return major_groups

    ranked = major_groups.copy()
    ranked["_rank_diff"] = ranked["min_rank"].astype(float) - float(profile.rank)
    near_window = max(3000, int(profile.rank * 0.25))

    rush_rows = ranked[ranked["_rank_diff"] < -near_window]
    target_rows = ranked[
        (ranked["_rank_diff"] >= -near_window)
        & (ranked["_rank_diff"] <= near_window * 2)
    ]
    safe_rows = ranked[ranked["_rank_diff"] > near_window * 2]

    rush_quota = int(max_candidates * 0.30)
    target_quota = int(max_candidates * 0.35)
    safe_quota = max_candidates - rush_quota - target_quota

    selected_parts = [
        _take_priority_rows(rush_rows, rush_quota, profile),
        _take_priority_rows(target_rows, target_quota, profile),
        _take_priority_rows(safe_rows, safe_quota, profile),
    ]
    selected = pd.concat(selected_parts, ignore_index=False)
    selected_indexes = set(selected.index.tolist())

    if len(selected) < max_candidates:
        remainder = ranked[~ranked.index.isin(selected_indexes)]
        selected = pd.concat(
            [
                selected,
                _take_priority_rows(remainder, max_candidates - len(selected), profile),
            ],
            ignore_index=False,
        )

    selected = selected.drop(columns=["_rank_diff"], errors="ignore")
    return selected.sort_values("min_rank").head(max_candidates)


def _resolve_runtime_data_dir() -> str:
    """Find prediction-time admissions data without reading post-hoc outcome labels."""
    candidate_dirs = [
        Path.cwd() / "data",
        Path.cwd() / "backend" / "data",
        Path.cwd().parent / "data",
    ]
    for path in candidate_dirs:
        if (
            (path / "2025_enrollment_full.csv").exists()
            and any(path.glob("2024_*.csv"))
        ):
            return str(path)

    for path in candidate_dirs:
        if any(path.glob("2024_*.csv")):
            return str(path)

    return "data"


def game_agent_node(state: SupervisorState) -> dict:
    """
    Game Agent 节点：推荐30个专业组（冲10/稳10/保10）

    广东省新高考规则：
    - 本科批次可填45个专业组
    - 每个专业组可选6个专业
    - 这里先推荐30个专业组供用户选择
    """
    print("[Agent 2] Game Agent 启动（专业组级别）...")
    print("[进度] 正在初始化量化引擎...")

    profile = state["user_profile"]
    if not profile:
        return {
            "current_agent": "game_agent",
            "debug_logs": ["[ERROR] Game Agent: 缺少用户画像"],
            "messages": [AIMessage(content="错误：缺少用户画像")]
        }

    # 修复新问题6：检查rank是否为None
    if not profile.rank or profile.rank <= 0:
        return {
            "current_agent": "game_agent",
            "debug_logs": ["[ERROR] Game Agent: 缺少有效的位次信息"],
            "messages": [AIMessage(content="错误：需要提供您的高考位次才能进行推荐。请告诉我您的全省位次。")]
        }
    research_evidence_cards = _extract_research_evidence_cards(state)
    if research_evidence_cards:
        print(f"[INFO] Game Agent: loaded {len(research_evidence_cards)} research evidence cards for market features")

    # 初始化量化引擎 - 智能检测数据目录
    try:
        from pathlib import Path
        import os

        data_dir = _resolve_runtime_data_dir()
        print(f"[DEBUG] 使用预测阶段数据目录: {data_dir}")

        engine = GaokaoQuantEngine(data_dir=data_dir)
        enrollment_loader = EnrollmentPlanLoader(data_dir=data_dir)
        target_year = int(os.getenv("GAOKAO_TARGET_YEAR", str(date.today().year)))
        data_vintage = inspect_recommendation_data_vintage(
            data_dir,
            target_year=target_year,
        )
    except Exception as e:
        return {
            "current_agent": "game_agent",
            "debug_logs": [f"[ERROR] Game Agent: 引擎初始化失败 - {e}"],
            "messages": [AIMessage(content=f"数据加载失败：{e}")]
        }

    # 搜索专业组候选（基于2021-2023历史数据）
    # 动态搜索范围：根据用户位次自动调整候选池大小
    gradient_strategy = RankGradientStrategy()
    config = gradient_strategy.get_config(profile.rank)
    candidate_pool_size = config.candidate_pool_size

    print(f"[进度] 搜索专业组（基于历史数据预测，用户位次={profile.rank}）...")
    print(f"[INFO] 排位梯度策略：{config.description}")
    print(f"[INFO] 候选池大小：{candidate_pool_size}个（根据排位{profile.rank}动态调整）")
    print(f"[INFO] 搜索专业组（基于历史数据预测）...")
    major_groups = engine.search_major_groups(
        user_rank=profile.rank,
        subject_group=profile.subject_group,
        target_count=candidate_pool_size   # 动态候选池大小
    )

    if major_groups.empty:
        return {
            "current_agent": "game_agent",
            "debug_logs": ["[WARN] Game Agent: 未找到匹配的专业组"],
            "messages": [AIMessage(content="抱歉，未找到符合您位次的专业组")]
        }

    recommend_config = gradient_strategy.get_recommended_volunteer_count(profile.rank)
    total_recommend = recommend_config["total"]
    original_candidate_count = len(major_groups)
    major_groups = _limit_precision_candidates(
        major_groups,
        profile,
        total_recommend=total_recommend,
    )
    if len(major_groups) < original_candidate_count:
        print(
            f"[INFO] 精算候选限流: {original_candidate_count} → {len(major_groups)} "
            f"(偏好/位次分层保留)"
        )

    print(f"[OK] 找到 {len(major_groups)} 个候选专业组")
    print(f"[进度] 正在计算录取概率（蒙特卡洛模拟，10K次采样）...")
    print(f"[INFO] 使用蒙特卡洛模拟处理大小年效应、招生计划变化等不确定因素")

    # 为每个专业组计算录取概率和策略标签
    major_group_rows = []
    probability_calibration_path = _resolve_probability_calibration_path()
    for _, group in major_groups.iterrows():
        school = group['school']
        school_code = group.get('school_code', school)
        # Handle NaN values from CSV
        if pd.isna(school_code):
            school_code = school  # Use school name as fallback
        school_code = EnrollmentPlanLoader._normalize_code(school_code) or str(school_code)
        major_group_code = group['major_group']
        major_list = group['major']  # List[str]
        min_rank_pred_simple = int(group['min_rank'])  # 简单平均（作为后备）
        historical_quota = int(group.get('quota', 0))  # 历史录取人数聚合，仅作兜底

        plan_records = enrollment_loader.get_major_group_options(
            school_name=school,
            school_code=school_code,
            major_group_code=major_group_code,
            category=profile.subject_group,
        )
        major_options = build_major_options_from_records(
            records=plan_records,
            fallback_majors=major_list,
        )
        major_options = score_major_options(major_options, profile)
        bundle_risk = analyze_bundle_risk(major_options)
        suggested_major_choices = choose_six_majors(major_options)
        suggested_major_names = [option.major_name for option in suggested_major_choices]
        full_major_names = [option.major_name for option in major_options] or list(major_list)
        quota = sum(option.plan_quota or 0 for option in major_options) or historical_quota

        # 【核心修复】使用蒙特卡洛模拟（真实概率计算）
        # 原因：一分一段表不是完美正态分布，存在偏态和多峰现象
        # 获取该专业组的历史数据
        hist_data = engine.get_major_group_history(
            school=school,
            major_group=major_group_code
        )

        # === 问题8修复：舆情修正（可选）===
        # 注意：舆情分析需要调用Tavily API，较慢且有成本
        # 只在用户明确要求时启用（通过环境变量或参数控制）
        sentiment_modifier = 0.0  # 默认不使用舆情修正

        # 如果启用舆情分析（环境变量 ENABLE_SENTIMENT_ANALYSIS=true）
        # 且是高概率候选（0.4 < prob < 0.8），才进行舆情分析
        # 这样可以避免对所有200个候选都调用API
        enable_sentiment = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "false").lower() == "true"
        if enable_sentiment:
            # 舆情分析功能（可选，需要Tavily API）
            # 取消下面的注释并配置ENABLE_SENTIMENT_ANALYSIS=true启用
            # from engines.sentiment_analyzer import get_sentiment_modifier
            # sentiment_result = get_sentiment_modifier(school, major_list[0] if major_list else None)
            # sentiment_modifier = sentiment_result.rank_modifier
            pass

        # 初始化：用于存储从fallback计算得到的正确Z-score
        z_score_from_calc = None
        skewness = 0.0

        try:
            # 蒙特卡洛模拟（3,000次采样，平衡速度和准确性）
            mc_result = monte_carlo_admission_probability(
                user_rank=profile.rank,
                hist_data=hist_data,
                n_simulations=3000,  # 修复：从5K降到3K，确保180秒内完成
                quota_change_rate=0.0,  # NOTE: 暂不使用2025招生计划变化率（需要额外数据处理）
                sentiment_modifier=sentiment_modifier,  # 问题8修复：使用舆情修正
                penalty_factor=2.0  # 小样本惩罚
            )
            # 从蒙特卡洛结果中提取关键指标
            admission_prob = mc_result.admission_prob
            min_rank_pred = mc_result.min_rank_pred  # 中位数预测
            rank_ci_lower = mc_result.ci_lower  # 95%置信区间下界
            rank_ci_upper = mc_result.ci_upper  # 95%置信区间上界
            volatility_std = mc_result.volatility_std  # 波动率
            z_score_from_calc = mc_result.z_score  # Z-score（基于raw_std）
            skewness = mc_result.skewness
        except ValueError as e:
            # 修复：首先捕获预期的ValueError
            print(f"[WARN] 数据验证失败 {school}-{major_group_code}: {e}")
            try:
                # 使用自适应分层惩罚（不传入penalty_factor参数）
                fallback_result = calculate_admission_probability(
                    user_rank=profile.rank,
                    hist_data=hist_data
                )
                if not fallback_result:
                    print(f"[WARN] Fallback也失败，跳过 {school}-{major_group_code}")
                    continue

                # 使用fallback结果
                admission_prob = fallback_result['prob']
                min_rank_pred = fallback_result['min_rank_pred']
                rank_ci_lower = fallback_result['ci_lower']
                rank_ci_upper = fallback_result['ci_upper']
                volatility_std = fallback_result['volatility_std']
                z_score_from_calc = fallback_result.get('z_score', 0)  # 获取基于raw_std的正确Z-score
                print(f"[OK] Fallback成功: {school}-{major_group_code} (概率={admission_prob:.1%})")
            except Exception as fallback_error:
                print(f"[ERROR] Fallback也失败: {fallback_error}")
                continue
        except Exception as e:
            # 修复：其他未预期的异常（应该记录并重新抛出或跳过）
            print(f"[ERROR] 蒙特卡洛模拟遇到未预期错误 {school}-{major_group_code}: {e}")
            import traceback
            traceback.print_exc()
            # 尝试fallback（使用自适应分层惩罚）
            try:
                fallback_result = calculate_admission_probability(
                    user_rank=profile.rank,
                    hist_data=hist_data
                )
                if not fallback_result:
                    print(f"[WARN] Fallback也失败，跳过 {school}-{major_group_code}")
                    continue

                # 使用fallback结果
                admission_prob = fallback_result['prob']
                min_rank_pred = fallback_result['min_rank_pred']
                rank_ci_lower = fallback_result['ci_lower']
                rank_ci_upper = fallback_result['ci_upper']
                volatility_std = fallback_result['volatility_std']
                z_score_from_calc = fallback_result.get('z_score', 0)  # 获取基于raw_std的正确Z-score
                print(f"[OK] Fallback成功: {school}-{major_group_code} (概率={admission_prob:.1%})")
            except Exception as fallback_error:
                print(f"[ERROR] Fallback失败，跳过 {school}-{major_group_code}: {fallback_error}")
                continue

        raw_admission_prob = admission_prob

        # 过滤仍基于原始历史模拟，避免经验校准映射改变候选搜索边界。
        if raw_admission_prob < 0.20:
            continue  # 录取概率太低，放弃

        # 计算rank_diff（用于后续分析）
        rank_diff = min_rank_pred - profile.rank

        # 使用正确的Z-score（基于raw_std）
        # 如果是fallback路径，z_score_from_calc已经包含正确的基于raw_std的Z-score
        # 如果是MC路径，z_score_from_calc应该从mc_result中提取
        if z_score_from_calc is not None:
            z_score = z_score_from_calc  # 使用计算的正确Z-score
            print(f"[DEBUG] {school}-{major_group_code}: Using calculated Z-score = {z_score:.3f}, rank_diff = {rank_diff}")
        else:
            # 不应该到这里，如果到了说明MC或fallback没正确返回z_score
            z_score = rank_diff / volatility_std if volatility_std > 0 else 0
            print(f"[WARN] {school}-{major_group_code}: z_score_from_calc is None! Using fallback Z = {z_score:.3f} (rank_diff={rank_diff}, volatility_std={volatility_std})")

        # 分类策略标签（基于Z-score的AI智能分类）
        strategy = classify_strategy_tag(raw_admission_prob, z_score=z_score)
        strategy_value = strategy.value if hasattr(strategy, "value") else str(strategy)
        admission_prob, probability_metadata = _calibrate_online_probability(
            raw_admission_prob,
            probability_calibration_path,
            subject_group=profile.subject_group,
        )
        print(
            f"[DEBUG] {school}-{major_group_code}: Z-score={z_score:.3f}, "
            f"Raw={raw_admission_prob:.1%}, Calibrated={admission_prob:.1%}, Strategy={strategy}"
        )

        scoring_major_names = suggested_major_names or major_list[:6]
        school_signal = score_school_major_signal(
            school_name=school,
            major_names=scoring_major_names,
            profile=profile,
        )

        # 修复问题7：如果所有专业评分都失败，跳过该专业组
        if school_signal.average_score <= 0:
            print(f"[SKIP] {school}-{major_group_code}: 无法计算综合评分（所有专业评分失败）")
            continue

        # 该专业组的平均综合评分
        avg_comprehensive_score = school_signal.average_score

        # 计算最终评分（综合评分60% + 录取概率40%）
        # 录取概率需要乘100，使其与综合评分（0-100）在同一量级
        final_score = avg_comprehensive_score * 0.6 + admission_prob * 100 * 0.4

        # === 问题5修复：专业黑名单检查 ===
        is_blacklist_risk = False
        blacklist_majors_in_group = []

        if profile.blacklist_majors:
            # 检查专业组中是否包含黑名单专业
            for major in full_major_names:
                for blacklist_keyword in profile.blacklist_majors:
                    if blacklist_keyword in major:
                        is_blacklist_risk = True
                        blacklist_majors_in_group.append(major)
                        break

        # 如果专业组全部是黑名单专业，直接跳过
        if full_major_names and is_blacklist_risk and len(blacklist_majors_in_group) == len(full_major_names):
            print(f"[SKIP] {school}-{major_group_code}: 全部为黑名单专业 {blacklist_majors_in_group}")
            continue

        # 如果部分是黑名单，降低综合评分（惩罚20%）
        if is_blacklist_risk:
            blacklist_ratio = len(blacklist_majors_in_group) / max(len(full_major_names), 1)
            final_score *= (1 - blacklist_ratio * 0.2)  # 最多降低20%
            print(f"[WARN] {school}-{major_group_code}: 包含黑名单专业 {blacklist_majors_in_group}，评分降低{blacklist_ratio*20:.0f}%")

        # 组内混搭和尾部调剂风险会影响专业组整体推荐价值
        final_score *= (1 - bundle_risk.tail_assignment_risk * TAIL_RISK_SCORE_PENALTY_WEIGHT)

        # === 问题6修复：城市偏好过滤 ===
        school_city = get_school_city(school)
        city_preference_score = calculate_city_preference_score(
            city=school_city,
            preferred_cities=profile.preferred_cities,
            excluded_cities=profile.excluded_cities
        )

        # 应用城市偏好调整
        final_score *= city_preference_score

        if city_preference_score < 1.0:
            print(f"[INFO] {school}({school_city}): 非偏好城市，评分调整为{city_preference_score:.0%}")
        elif city_preference_score > 1.0:
            print(f"[INFO] {school}({school_city}): 偏好城市，评分提升为{city_preference_score:.0%}")

        # 利用蒙特卡洛结果判断波动性（大小年效应）
        if abs(skewness) > 0.5 or volatility_std > min_rank_pred * 0.1:
            # 偏度大或标准差大 → 高波动（明显大小年）
            volatility_level = VolatilityLevel.HIGH
        elif volatility_std < min_rank_pred * 0.05:
            # 标准差小 → 低波动（稳定）
            volatility_level = VolatilityLevel.LOW
        else:
            # 中等波动
            volatility_level = VolatilityLevel.MEDIUM

        quota_stability = quota_stability_score(quota)
        variance_opportunity = variance_opportunity_score(
            quota,
            bundle_risk.major_utility_dispersion,
        )
        quant_scorecard = build_quant_scorecard(
            hist_data=hist_data,
            user_rank=profile.rank,
            min_rank_pred=min_rank_pred,
            rank_ci_lower=rank_ci_lower,
            rank_ci_upper=rank_ci_upper,
            quota_stability=quota_stability,
        )

        # 创建专业组推荐行（增强版：包含更多元数据）
        row = MajorGroupRow(
            school_name=school,
            school_code=school_code,  # 修复：添加院校代码字段
            major_group_code=str(major_group_code),
            major_list=suggested_major_names or (major_list[:6] if len(major_list) >= 6 else major_list),
            major_count=len(full_major_names),
            major_options=major_options,
            suggested_major_choices=suggested_major_choices,
            admission_prob=admission_prob,
            **probability_metadata,
            min_rank_pred=min_rank_pred,
            rank_diff=rank_diff,  # 修复新问题1：存储rank_diff
            rank_ci_lower=rank_ci_lower,
            rank_ci_upper=rank_ci_upper,
            strategy_tag=strategy,
            volatility=volatility_level,  # 基于蒙特卡洛结果的波动性判断
            quota=quota if quota > 0 else None,
            quota_bucket=quota_bucket(quota),
            quota_stability_score=quota_stability,
            variance_opportunity_score=variance_opportunity,
            adjustment_risk=bundle_risk.tail_assignment_risk,
            worst_case_major=bundle_risk.worst_case_major,
            is_blacklist_risk=is_blacklist_risk,  # 修复：实际检查黑名单
            acceptable_major_ratio=bundle_risk.acceptable_major_ratio,
            blacklist_major_ratio=bundle_risk.blacklist_major_ratio,
            major_utility_mean=bundle_risk.major_utility_mean,
            major_utility_min=bundle_risk.major_utility_min,
            major_utility_dispersion=bundle_risk.major_utility_dispersion,
            tail_assignment_risk=bundle_risk.tail_assignment_risk,
            bundle_type=bundle_risk.bundle_type,
            obey_adjustment=bundle_risk.obey_adjustment,
            adjustment_advice=bundle_risk.adjustment_advice,
            recommendation_role=f"{strategy_value}:{school_signal.tradeoff_label}",
            risk_reasons=bundle_risk.risk_reasons,
            audit_flags=bundle_risk.audit_flags,
            quant_score=quant_scorecard.quant_score,
            rank_buffer_score=quant_scorecard.rank_buffer_score,
            history_stability_score=quant_scorecard.history_stability_score,
            data_confidence_score=quant_scorecard.data_confidence_score,
            trend_score=quant_scorecard.trend_score,
            deterministic_risk_band=quant_scorecard.deterministic_risk_band,
            quant_evidence=quant_scorecard.evidence,
            # 修复问题1：使用comprehensive_score字段存储综合评分
            comprehensive_score=_normalize_percent_score(final_score),  # 归一化到0-1范围
            sentiment_score=0.0  # 保留舆情字段，暂未使用
        )

        tradeoff_result = score_tradeoff(
            row=row,
            profile=profile,
            school_major_score=_normalize_percent_score(avg_comprehensive_score),
            city_preference_score=city_preference_score,
        )
        row.comprehensive_score = _clamp01(
            tradeoff_result.final_score * 0.85
            + quant_scorecard.quant_score * 0.15
        )
        row.score_band = tradeoff_result.score_band
        row.tradeoff_breakdown = {
            **tradeoff_result.breakdown,
            "quant_score": quant_scorecard.quant_score,
            "rank_buffer_score": quant_scorecard.rank_buffer_score,
            "history_stability_score": quant_scorecard.history_stability_score,
            "data_confidence_score": quant_scorecard.data_confidence_score,
            "trend_score": quant_scorecard.trend_score,
        }
        row.pain_point_flags = tradeoff_result.pain_point_flags
        row.market_behavior_notes = tradeoff_result.market_behavior_notes
        row.tradeoff_summary = tradeoff_result.summary
        _score_row_arbitrage(
            row=row,
            profile=profile,
            school_major_score=_normalize_percent_score(avg_comprehensive_score),
            city_preference_score=city_preference_score,
            research_evidence_cards=research_evidence_cards,
        )
        row.recommendation_role = (
            f"{row.recommendation_role}:{tradeoff_result.score_band}"
            if row.recommendation_role
            else tradeoff_result.score_band
        )
        row.decision_trace = build_decision_trace(row)

        major_group_rows.append(row)

    plan_change_count = _attach_online_plan_changes(
        major_group_rows,
        subject_group=profile.subject_group,
        diff_path=_resolve_plan_change_diff_path(),
    )
    if plan_change_count:
        print(f"[INFO] 已为 {plan_change_count} 个候选附加高置信招生计划变化证据")

    runtime_rl = RLRuntimePolicy()
    desired_mix = runtime_rl.get_recommendation_mix(total_recommend, profile)
    classified_counts = count_strategy_rows(major_group_rows)
    print(
        "[进度] 按冲稳保分桶执行帕累托保留："
        f"原始冲{classified_counts['rush']}/稳{classified_counts['target']}/保{classified_counts['safe']}，"
        f"目标冲{desired_mix['rush']}/稳{desired_mix['target']}/保{desired_mix['safe']}..."
    )
    candidate_pool = _prepare_strategy_candidate_pool(
        major_group_rows,
        desired=desired_mix,
        reserve=3,
    )
    retained_counts = count_strategy_rows(candidate_pool)
    print(
        "[OK] 分桶保留后："
        f"冲{retained_counts['rush']}/稳{retained_counts['target']}/保{retained_counts['safe']}"
    )

    print("[进度] 正在应用运行时RL策略与志愿组合优化...")
    final_groups, optimization_summary = runtime_rl.select_candidates(
        rows=candidate_pool,
        profile=profile,
        total_count=total_recommend,
    )

    if not final_groups:
        print("[WARN] 运行时RL未返回候选，回退到综合评分排序")
        final_groups = sorted(
            candidate_pool,
            key=lambda row: row.comprehensive_score,
            reverse=True,
        )[:total_recommend]
        optimization_summary = {
            "policy_source": runtime_rl.policy_source,
            "checkpoint_loaded": runtime_rl.is_loaded,
            "mix": recommend_config,
            "effective_params": {},
            "selected_count": len(final_groups),
            "portfolio": {"generated": False, "reason": "fallback"},
            "fallback": "comprehensive_score",
        }

    final_groups, capacity_fill = fill_plan_capacity(
        selected_rows=final_groups,
        all_rows=major_group_rows,
        total_count=total_recommend,
    )
    optimization_summary["capacity_fill"] = capacity_fill
    optimization_summary["selected_count"] = len(final_groups)
    if capacity_fill["filled_count"]:
        optimization_summary["portfolio"] = runtime_rl.optimize_portfolio(final_groups, profile)

    optimization_summary["coverage_report"] = build_coverage_report(
        desired=desired_mix,
        classified_rows=major_group_rows,
        post_pareto_rows=candidate_pool,
        selected_rows=final_groups,
    )

    portfolio_summary = optimization_summary.get("portfolio", {})
    if portfolio_summary.get("generated"):
        selected_order = {
            key: idx
            for idx, key in enumerate(portfolio_summary.get("selected_keys", []))
        }
        final_groups = sorted(
            final_groups,
            key=lambda row: (
                selected_order.get(
                    f"{row.school_name}::{row.major_group_code}",
                    len(selected_order) + 1,
                ),
                -row.comprehensive_score,
            ),
        )

    mix = optimization_summary.get("mix", recommend_config)
    rush_needed = mix.get("rush", recommend_config["rush"])
    target_needed = mix.get("target", recommend_config["target"])
    safe_needed = mix.get("safe", recommend_config["safe"])

    selected_rush = [r for r in final_groups if r.strategy_tag == StrategyTag.RUSH]
    selected_target = [r for r in final_groups if r.strategy_tag == StrategyTag.TARGET]
    selected_safe = [r for r in final_groups if r.strategy_tag == StrategyTag.SAFE]

    print(f"[OK] 最终推荐 {len(final_groups)} 个专业组（目标：{total_recommend}个）")
    print(f"    - 冲刺: {len(selected_rush)} 个（目标：{rush_needed}个）")
    print(f"    - 稳妥: {len(selected_target)} 个（目标：{target_needed}个）")
    print(f"    - 保底: {len(selected_safe)} 个（目标：{safe_needed}个）")
    print(
        f"[INFO] 推荐策略：Pareto筛选 + 运行时RL配比 + 组合优化 "
        f"(checkpoint_loaded={optimization_summary.get('checkpoint_loaded', False)})"
    )

    # === 新增：Agent自主思考与自我评估 ===
    reasoning_insights = []
    if optimization_summary.get("checkpoint_loaded"):
        reasoning_insights.append(
            f"[RL Policy] 已加载checkpoint；运行时配比为 "
            f"冲{rush_needed}/稳{target_needed}/保{safe_needed}。"
        )
    if portfolio_summary.get("generated"):
        portfolio_probability_label = (
            "最高单组历史校准命中率"
            if final_groups and all(row.probability_is_calibrated for row in final_groups)
            else "最高单组模拟概率"
        )
        reasoning_insights.append(
            f"[Portfolio] 组合优化选择了“{portfolio_summary.get('style_name', '默认风格')}”，"
            f"{portfolio_probability_label}约为{portfolio_summary.get('admission_guarantee', 0.0):.1%}。"
        )

    # 评估1：检查保底数量是否充足（基于Z-score智能判断）
    if len(selected_safe) == 0:
        reasoning_insights.append(
            f"[🤔 AI推理] 未找到保底院校（Z-score≥2.0σ）。分析原因："
            f"用户位次{profile.rank}处于竞争激烈区间，"
            f"候选院校中位次优势未达到2倍标准差（统计学保底标准）。"
            f"建议：关注Z-score≥1.0的稳妥档院校，或扩大搜索范围到更低位次段。"
        )
    elif len(selected_safe) < safe_needed:
        reasoning_insights.append(
            f"[🤔 AI推理] 保底院校数量不足（{len(selected_safe)}/{safe_needed}）。"
            f"系统基于Z-score（相对位次优势）智能分类："
            f"Z≥2.0σ为保底（95%+置信度），Z=1.0-2.0σ为稳妥，Z<1.0σ为冲刺。"
            f"已自动从稳妥档中选择位次优势最大的院校补充。"
        )

    # 评估2：检查冲刺数量
    if len(selected_rush) < rush_needed / 2:
        reasoning_insights.append(
            f"[🤔 AI推理] 冲刺院校数量较少（{len(selected_rush)}/{rush_needed}）。"
            f"用户位次{profile.rank}可能已处于较高水平，向上冲刺空间有限。"
            f"建议关注稳妥档和保底档院校，确保录取安全。"
        )

    # 评估3：检查招生规模分布
    small_quota_count = len([r for r in final_groups if r.quota_bucket.value == "small"])
    if small_quota_count > len(final_groups) * 0.6:
        reasoning_insights.append(
            f"[🤔 AI推理] 检测到{small_quota_count}个小招生规模专业组。"
            f"系统现在基于2025招生计划quota判断招生规模，而不是用专业数量代替。"
            f"小计划专业组会同时标记高波动风险和潜在捡漏机会。"
        )

    # 评估4：检查是否需要触发深度研究
    should_trigger_deep_research = False
    deep_research_reason = ""

    if len(selected_safe) == 0 and len(selected_target) < target_needed / 2:
        should_trigger_deep_research = True
        deep_research_reason = "推荐结果严重不平衡，建议启动深度研究循环分析边界情况"

    if should_trigger_deep_research:
        reasoning_insights.append(
            f"[⚠️ AI判断] {deep_research_reason}。"
            f"系统建议切换到慢思考循环（Deep Research），进行更深入的分析。"
        )
        # 在debug_logs中添加特殊标记，供路由函数检测
        reasoning_insights.append("[TRIGGER_DEEP_RESEARCH]")

    # 将推理过程记录到debug_logs
    for insight in reasoning_insights:
        try:
            print(insight)
        except UnicodeEncodeError:
            # Windows控制台GBK编码无法显示emoji，仅记录简化信息
            # 推理内容仍会通过debug_logs发送到前端
            try:
                # 尝试移除emoji后打印
                ascii_msg = insight.encode('ascii', errors='ignore').decode('ascii')
                print(f"[AI Reasoning] {ascii_msg}")
            except:
                # 如果还是失败，就完全跳过控制台输出
                pass

    volunteer_plan = build_volunteer_plan(final_groups, profile, optimize_prefix=True)

    # 创建博弈矩阵
    plan_audit_summary = (
        build_plan_audit_summary(
            volunteer_plan,
            profile,
            coverage_report=optimization_summary.get("coverage_report"),
            data_vintage=data_vintage.model_dump(),
        )
        if volunteer_plan
        else None
    )

    game_matrix = GameMatrix(
        major_group_rows=final_groups,
        agentic_rl_used=optimization_summary.get("checkpoint_loaded", False),
        selection_method="pareto+runtime_rl+portfolio_optimization+prefix_optimizer",
        optimization_summary=optimization_summary,
        data_vintage=data_vintage.model_dump(),
        volunteer_plan=volunteer_plan,
        plan_audit_summary=plan_audit_summary,
    )
    game_matrix.calculate_statistics()

    debug_msg = f"[OK] Game Agent: 推荐 {len(final_groups)} 个专业组（冲{game_matrix.total_rush} + 稳{game_matrix.total_target} + 保{game_matrix.total_safe}）"
    if volunteer_plan:
        probability_range_label = (
            "历史校准命中区间"
            if volunteer_plan.probability_is_calibrated
            else "未校准启发式命中区间"
        )
        debug_msg += (
            f"，{probability_range_label}{format_plan_probability_range(volunteer_plan)}，"
            f"关键前缀{volunteer_plan.key_prefix_count}行"
        )

    # 合并推理过程到debug_logs（不包含触发标记，那个只用于内部检测）
    all_debug_logs = [debug_msg] + [
        f"[REASONING] {msg}"
        for msg in reasoning_insights
        if not msg.startswith("[TRIGGER_DEEP_RESEARCH]")
    ]

    return {
        "game_matrix": game_matrix,
        "agent_messages": publish_agent_message(
            sender="game_agent",
            stage="post_game_deliberation",
            message_type="proposal",
            content=(
                f"Generated {len(final_groups)} candidates with rush={game_matrix.total_rush}, "
                f"target={game_matrix.total_target}, safe={game_matrix.total_safe}."
            ),
            recipients=[
                "risk_guardian_agent",
                "opportunity_advocate_agent",
                "evidence_guardian_agent",
                "deliberation_coordinator",
            ],
            thread_id="post_game_deliberation",
            priority="high",
            requires_ack=True,
            action_preference="report_agent",
            confidence=0.75,
            metadata={
                "candidate_count": len(final_groups),
                "rush_count": game_matrix.total_rush,
                "target_count": game_matrix.total_target,
                "safe_count": game_matrix.total_safe,
                "portfolio_risk": game_matrix.portfolio_risk,
                "expected_admission_prob": volunteer_plan.expected_admission_prob if volunteer_plan else None,
                "key_prefix_count": volunteer_plan.key_prefix_count if volunteer_plan else None,
                "shadowed_choice_count": volunteer_plan.shadowed_choice_count if volunteer_plan else None,
            },
        )["agent_messages"],
        "agent_memories": remember(
            agent_name="game_agent",
            stage="post_game_deliberation",
            note_type="proposal_summary",
            content=(
                f"Prepared candidate slate count={len(final_groups)}, "
                f"risk={game_matrix.portfolio_risk:.3f}, method={game_matrix.selection_method}"
            ),
            importance=0.8,
        )["agent_memories"],
        "current_agent": "game_agent",
        "debug_logs": all_debug_logs,
        "messages": [AIMessage(content=f"已生成{len(final_groups)}个专业组推荐")]
    }
