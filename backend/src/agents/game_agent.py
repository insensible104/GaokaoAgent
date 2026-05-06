"""Agent 2: 博弈推荐智能体（专业组级别）"""
import os
import pandas as pd
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
)
from recommendation.major_utility import score_major_options
from recommendation.school_signal import score_school_major_signal
from recommendation.tradeoff_policy import score_tradeoff
from utils.agent_bus import publish_agent_message, remember
from utils.city_mapping import get_school_city, calculate_city_preference_score
from rl.rank_gradient_strategy import RankGradientStrategy
from rl.runtime_policy import RLRuntimePolicy
from engines.pareto_optimizer import compute_pareto_frontier, Objective


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

    # 初始化量化引擎 - 智能检测数据目录
    try:
        from pathlib import Path
        import os

        # 优先检查相对于backend/的data目录（修复路径bug）
        if Path("data").exists():
            data_dir = "data"
            print(f"[DEBUG] 使用相对路径: data/")
        elif Path("../data").exists():
            data_dir = "../data"
            print(f"[DEBUG] 使用相对路径: ../data/")
        elif Path("backend/data").exists():
            data_dir = "backend/data"
            print(f"[DEBUG] 使用相对路径: backend/data/")
        else:
            # 使用绝对路径作为最后的备选
            cwd = Path.cwd()
            abs_data_dir = cwd / "data"
            if not abs_data_dir.exists():
                abs_data_dir = cwd.parent / "data"
            data_dir = str(abs_data_dir)
            print(f"[DEBUG] 使用绝对路径: {data_dir}")

        engine = GaokaoQuantEngine(data_dir=data_dir)
        enrollment_loader = EnrollmentPlanLoader(data_dir=data_dir)
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

    print(f"[OK] 找到 {len(major_groups)} 个候选专业组")
    print(f"[进度] 正在计算录取概率（蒙特卡洛模拟，10K次采样）...")
    print(f"[INFO] 使用蒙特卡洛模拟处理大小年效应、招生计划变化等不确定因素")

    # 为每个专业组计算录取概率和策略标签
    major_group_rows = []
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

        # 过滤掉概率过低的（冲刺概率 < 20%）
        if admission_prob < 0.20:
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
        strategy = classify_strategy_tag(admission_prob, z_score=z_score)
        print(f"[DEBUG] {school}-{major_group_code}: Z-score = {z_score:.3f}, Probability = {admission_prob:.1%}, Strategy = {strategy}")

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
            min_rank_pred=min_rank_pred,
            rank_diff=rank_diff,  # 修复新问题1：存储rank_diff
            rank_ci_lower=rank_ci_lower,
            rank_ci_upper=rank_ci_upper,
            strategy_tag=strategy,
            volatility=volatility_level,  # 基于蒙特卡洛结果的波动性判断
            quota=quota if quota > 0 else None,
            quota_bucket=quota_bucket(quota),
            quota_stability_score=quota_stability_score(quota),
            variance_opportunity_score=variance_opportunity_score(
                quota,
                bundle_risk.major_utility_dispersion,
            ),
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
            recommendation_role=f"{strategy.value}:{school_signal.tradeoff_label}",
            risk_reasons=bundle_risk.risk_reasons,
            audit_flags=bundle_risk.audit_flags,
            # 修复问题1：使用comprehensive_score字段存储综合评分
            comprehensive_score=final_score / 100.0,  # 归一化到0-1范围
            sentiment_score=0.0  # 保留舆情字段，暂未使用
        )

        tradeoff_result = score_tradeoff(
            row=row,
            profile=profile,
            school_major_score=avg_comprehensive_score / 100.0,
            city_preference_score=city_preference_score,
        )
        row.comprehensive_score = tradeoff_result.final_score
        row.score_band = tradeoff_result.score_band
        row.tradeoff_breakdown = tradeoff_result.breakdown
        row.pain_point_flags = tradeoff_result.pain_point_flags
        row.market_behavior_notes = tradeoff_result.market_behavior_notes
        row.tradeoff_summary = tradeoff_result.summary
        row.recommendation_role = (
            f"{row.recommendation_role}:{tradeoff_result.score_band}"
            if row.recommendation_role
            else tradeoff_result.score_band
        )

        major_group_rows.append(row)

    # === 帕累托最优筛选（降低搜索空间）===
    print(f"[进度] 帕累托前沿筛选（从{len(major_group_rows)}个候选中找出非支配解）...")

    # 修复：先分离保底院校（Z-score≥2.0），保底院校不参与Pareto筛选，直接保留
    safe_schools_preserved = [r for r in major_group_rows if r.strategy_tag == StrategyTag.SAFE]
    non_safe_schools = [r for r in major_group_rows if r.strategy_tag != StrategyTag.SAFE]

    print(f"[INFO] 保底院校：{len(safe_schools_preserved)}个（不参与Pareto筛选，全部保留）")
    print(f"[INFO] 非保底院校：{len(non_safe_schools)}个（将进行Pareto筛选）")

    # 定义多目标优化目标
    objectives = [
        Objective(name='录取概率', key='admission_prob', maximize=True, weight=1.0),
        Objective(name='综合评分', key='comprehensive_score', maximize=True, weight=2.0),
        Objective(name='调剂风险', key='adjustment_risk', maximize=False, weight=0.5)
    ]

    # 转换为字典格式（pareto_optimizer需要）- 只对非保底院校进行优化
    candidates_dict = []
    for i, row in enumerate(non_safe_schools):
        candidates_dict.append({
            'volunteer_index': i,
            'school_name': row.school_name,
            'major_name': ','.join(row.major_list[:3]),  # 前3个专业
            'admission_prob': row.admission_prob,
            'comprehensive_score': row.comprehensive_score,
            'adjustment_risk': row.adjustment_risk,
            'original_row': row  # 保留原始对象
        })

    # 计算帕累托前沿（只对非保底院校）
    pareto_result = compute_pareto_frontier(
        candidates=candidates_dict,
        objectives=objectives,
        max_rank=5  # 修复：从2增加到5，保留更多层次的候选
    )

    print(f"[OK] 帕累托前沿: {pareto_result.frontier_size}个非支配解")
    print(f"     被支配解: {pareto_result.dominated_size}个（已过滤）")

    # 从帕累托前沿中提取原始row对象
    pareto_indices = [sol.volunteer_index for sol in pareto_result.pareto_frontier]
    if pareto_result.dominated_solutions:
        # 修复：保留前5层的所有解，而不是只保留第2层的一半
        pareto_indices.extend([
            sol.volunteer_index
            for sol in pareto_result.dominated_solutions
            if sol.pareto_rank <= 5
        ])

    pareto_non_safe_rows = [non_safe_schools[i] for i in pareto_indices]
    candidate_pool = pareto_non_safe_rows + safe_schools_preserved

    print("[进度] 正在应用运行时RL策略与志愿组合优化...")
    recommend_config = gradient_strategy.get_recommended_volunteer_count(profile.rank)
    total_recommend = recommend_config["total"]

    runtime_rl = RLRuntimePolicy()
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
        reasoning_insights.append(
            f"[Portfolio] 组合优化选择了“{portfolio_summary.get('style_name', '默认风格')}”，"
            f"保底成功率约为{portfolio_summary.get('admission_guarantee', 0.0):.1%}。"
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

    volunteer_plan = build_volunteer_plan(final_groups, profile)

    # 创建博弈矩阵
    game_matrix = GameMatrix(
        major_group_rows=final_groups,
        agentic_rl_used=optimization_summary.get("checkpoint_loaded", False),
        selection_method="pareto+runtime_rl+portfolio_optimization",
        optimization_summary=optimization_summary,
        volunteer_plan=volunteer_plan,
    )
    game_matrix.calculate_statistics()

    debug_msg = f"[OK] Game Agent: 推荐 {len(final_groups)} 个专业组（冲{game_matrix.total_rush} + 稳{game_matrix.total_target} + 保{game_matrix.total_safe}）"
    if volunteer_plan:
        debug_msg += (
            f"，首命中累计概率{volunteer_plan.expected_admission_prob:.1%}，"
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
