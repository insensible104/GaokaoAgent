"""博弈矩阵数据模型（专业组级别）"""
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional
from enum import Enum


class StrategyTag(str, Enum):
    """志愿策略标签"""
    RUSH = "rush"      # 冲：录取概率 < 60%
    TARGET = "target"  # 稳：录取概率 60%-90%
    SAFE = "safe"      # 保：录取概率 >= 90%


class VolatilityLevel(str, Enum):
    """波动率等级"""
    LOW = "low"        # 低波动（历史稳定）
    MEDIUM = "medium"  # 中波动
    HIGH = "high"      # 高波动（大小年明显）


class QuotaBucket(str, Enum):
    """招生计划规模分桶"""
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    UNKNOWN = "unknown"


class BundleType(str, Enum):
    """院校专业组内部专业组合类型"""
    CLEAN_FIT = "clean_fit"
    MILD_MIXED = "mild_mixed"
    HIGHLY_MIXED = "highly_mixed"
    BAIT_RISK = "bait_risk"
    BLACKLIST_BLOCKED = "blacklist_blocked"
    UNKNOWN = "unknown"


class AdjustmentAdvice(str, Enum):
    """是否服从专业调剂的建议"""
    RECOMMEND = "recommend"
    CAUTIOUS = "cautious"
    AVOID = "avoid"


class MajorOption(BaseModel):
    """广东志愿表中某个院校专业组内的一个专业选项。"""
    school_code: str = ""
    school_name: str = ""
    major_group_code: str = ""
    major_code: str = ""
    major_name: str
    subject_requirement: Optional[str] = None
    plan_quota: Optional[int] = None
    tuition: Optional[float] = None
    remarks: Optional[str] = None

    historical_min_scores: Dict[int, Optional[float]] = Field(default_factory=dict)
    historical_min_ranks: Dict[int, Optional[int]] = Field(default_factory=dict)

    category: Optional[str] = None
    user_utility: float = Field(default=0.5, ge=0, le=1)
    is_preferred: bool = False
    is_acceptable: bool = True
    is_blacklisted: bool = False
    major_rank_risk: float = Field(default=0.5, ge=0, le=1)
    risk_reasons: List[str] = Field(default_factory=list)


class VolunteerChoice(BaseModel):
    """一行可落到广东志愿填报表的院校专业组志愿。"""
    choice_index: int
    school_code: str
    school_name: str
    major_group_code: str
    major_choices: List[MajorOption] = Field(default_factory=list)
    obey_adjustment: bool = True
    adjustment_advice: AdjustmentAdvice = AdjustmentAdvice.CAUTIOUS

    group_admission_prob: float = Field(default=0.0, ge=0, le=1)
    survival_before_prob: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Probability that all previous choices fail before this row is reached.",
    )
    first_hit_prob: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Probability that this row becomes the first admitted major group.",
    )
    cumulative_hit_prob: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Probability that at least one row has admitted the user through this row.",
    )
    consequence_score: float = Field(
        default=0.0,
        description="First-hit-weighted utility after tail-risk penalty.",
    )
    prefix_role: str = Field(
        default="unclassified",
        description="Role in the ordered volunteer-plan prefix.",
    )
    is_key_prefix: bool = Field(
        default=False,
        description="Whether this row is likely to affect the final admission outcome.",
    )
    expected_major_utility: float = Field(default=0.0, ge=0, le=1)
    worst_case_major: Optional[str] = None
    tail_assignment_risk: float = Field(default=0.0, ge=0, le=1)
    strategy_tag: StrategyTag = StrategyTag.TARGET
    recommendation_role: str = "target"
    explanation: str = ""
    audit_flags: List[str] = Field(default_factory=list)
    score_band: str = ""
    tradeoff_breakdown: Dict[str, float] = Field(default_factory=dict)
    pain_point_flags: List[str] = Field(default_factory=list)
    market_behavior_notes: List[str] = Field(default_factory=list)
    tradeoff_summary: str = ""
    arbitrage_score: float = Field(default=0.0, ge=0, le=1)
    front_major_arbitrage_score: float = Field(default=0.0, ge=0, le=1)
    relative_lift: float = Field(default=0.0, ge=0, le=1)
    market_discount_score: float = Field(default=0.0, ge=0, le=1)
    personal_acceptability: float = Field(default=0.0, ge=0, le=1)
    sacrifice_cost: float = Field(default=0.0, ge=0, le=1)
    assignment_opportunity: float = Field(default=0.0, ge=0, le=1)
    front_major_hit_prob: float = Field(default=0.0, ge=0, le=1)
    rebound_risk: float = Field(default=0.0, ge=0, le=1)
    opportunity_types: List[str] = Field(default_factory=list)
    opportunity_pools: List[str] = Field(default_factory=list)
    arbitrage_breakdown: Dict[str, float] = Field(default_factory=dict)
    market_evidence_cards: List[Dict[str, Any]] = Field(default_factory=list)
    market_evidence_strength: float = Field(default=0.0, ge=0, le=1)
    publicity_heat_score: float = Field(default=0.0, ge=0, le=1)
    publicity_rebound_risk: float = Field(default=0.0, ge=0, le=1)
    segment_demand_score: float = Field(default=0.0, ge=0, le=1)
    low_attention_signal: float = Field(default=0.0, ge=0, le=1)
    segment_rebound_risk: float = Field(default=0.0, ge=0, le=1)
    best_fit_archetypes: List[str] = Field(default_factory=list)
    segment_demand_breakdown: Dict[str, float] = Field(default_factory=dict)
    plan_change_score: float = Field(default=0.0, ge=0, le=1)
    plan_change_types: List[str] = Field(default_factory=list)
    plan_change_evidence: List[str] = Field(default_factory=list)


class VolunteerPlan(BaseModel):
    """完整志愿表草案。"""
    province: str = "广东"
    year: int = 2025
    subject_group: str = ""
    user_score: Optional[int] = None
    user_rank: Optional[int] = None
    choices: List[VolunteerChoice] = Field(default_factory=list)

    total_rush: int = 0
    total_target: int = 0
    total_safe: int = 0
    safe_anchor_coverage: float = Field(default=0.0, ge=0, le=1)
    average_tail_risk: float = Field(default=0.0, ge=0, le=1)
    expected_admission_prob: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Probability that at least one ordered volunteer choice admits the user.",
    )
    expected_first_hit_utility: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Expected major utility weighted by first-hit probabilities.",
    )
    expected_tail_risk: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Expected tail-assignment risk weighted by first-hit probabilities.",
    )
    expected_plan_value: float = Field(
        default=0.0,
        description="Plan-level value: first-hit utility minus realized tail/sliding risk.",
    )
    key_prefix_count: int = Field(default=0, description="Number of active rows before the plan is mostly decided.")
    key_choice_indexes: List[int] = Field(
        default_factory=list,
        description="Choice indexes that materially affect the final first-hit outcome.",
    )
    shadowed_choice_count: int = Field(
        default=0,
        description="Rows whose first-hit probability is low because earlier rows dominate.",
    )
    blacklist_violation_count: int = 0
    adjustment_warning_count: int = 0
    plan_summary: str = ""
    human_review_items: List[str] = Field(default_factory=list)

    def calculate_statistics(self):
        """计算志愿表层面的统计指标。"""
        if not self.choices:
            return

        total_count = len(self.choices)
        self.total_rush = sum(1 for c in self.choices if c.strategy_tag == StrategyTag.RUSH)
        self.total_target = sum(1 for c in self.choices if c.strategy_tag == StrategyTag.TARGET)
        self.total_safe = sum(1 for c in self.choices if c.strategy_tag == StrategyTag.SAFE)
        self.safe_anchor_coverage = self.total_safe / total_count
        self.average_tail_risk = sum(c.tail_assignment_risk for c in self.choices) / total_count
        self.blacklist_violation_count = sum(
            1
            for c in self.choices
            if any(m.is_blacklisted for m in c.major_choices)
        )
        self.adjustment_warning_count = sum(
            1
            for c in self.choices
            if c.adjustment_advice in {AdjustmentAdvice.CAUTIOUS, AdjustmentAdvice.AVOID}
        )

        survival = 1.0
        expected_utility = 0.0
        expected_tail_risk = 0.0
        key_indexes: List[int] = []
        shadowed_count = 0

        for choice in self.choices:
            admission_prob = max(0.0, min(1.0, choice.group_admission_prob))
            choice.survival_before_prob = survival
            choice.first_hit_prob = survival * admission_prob
            survival *= 1 - admission_prob
            choice.cumulative_hit_prob = 1 - survival
            choice.consequence_score = choice.first_hit_prob * max(
                0.0,
                choice.expected_major_utility * (1 - choice.tail_assignment_risk),
            )

            if choice.first_hit_prob >= 0.10:
                choice.prefix_role = "key_result"
                choice.is_key_prefix = True
            elif choice.survival_before_prob + 1e-9 >= 0.10 and choice.first_hit_prob >= 0.03:
                choice.prefix_role = "active_backup"
                choice.is_key_prefix = True
            elif choice.survival_before_prob < 0.10 and choice.group_admission_prob >= 0.85:
                choice.prefix_role = "safety_anchor"
                choice.is_key_prefix = False
                shadowed_count += 1
            else:
                choice.prefix_role = "shadowed"
                choice.is_key_prefix = False
                shadowed_count += 1

            if choice.is_key_prefix:
                key_indexes.append(choice.choice_index)

            expected_utility += choice.first_hit_prob * choice.expected_major_utility
            expected_tail_risk += choice.first_hit_prob * choice.tail_assignment_risk

        self.expected_admission_prob = 1 - survival
        self.expected_first_hit_utility = min(1.0, expected_utility)
        self.expected_tail_risk = min(1.0, expected_tail_risk)
        self.expected_plan_value = (
            self.expected_first_hit_utility
            - self.expected_tail_risk
            - (1 - self.expected_admission_prob)
        )
        self.key_choice_indexes = key_indexes
        self.key_prefix_count = len(key_indexes)
        self.shadowed_choice_count = shadowed_count


class MajorGroupRow(BaseModel):
    """博弈矩阵的单行（一个专业组）

    广东省新高考规则：
    - 本科批次可填45个专业组
    - 每个专业组可选6个专业
    - 这里先推荐专业组，用户选择后再展开专业
    """
    # 基础信息
    school_name: str
    school_code: str = Field(description="院校代码")  # 修复：添加缺失字段
    major_group_code: str = Field(description="专业组代码")
    major_list: List[str] = Field(default_factory=list, description="该专业组包含的所有专业")
    major_count: int = Field(default=0, description="专业数量")
    major_options: List[MajorOption] = Field(default_factory=list, description="该专业组内的结构化专业选项")
    suggested_major_choices: List[MajorOption] = Field(default_factory=list, description="建议填入志愿表的1-6个专业")

    # 核心指标
    admission_prob: float = Field(ge=0, le=1, description="录取概率")
    choice_index: Optional[int] = Field(default=None, description="Ordered volunteer-form row index.")
    survival_before_prob: float = Field(
        default=1.0,
        ge=0,
        le=1,
        description="Probability that all previous ordered rows fail before this row.",
    )
    first_hit_prob: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Probability that this row becomes the first admitted major group.",
    )
    cumulative_hit_prob: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Probability that at least one ordered row has admitted through this row.",
    )
    consequence_score: float = Field(default=0.0, description="First-hit-weighted utility score.")
    prefix_role: str = Field(default="unclassified", description="Role in the ordered volunteer prefix.")
    is_key_prefix: bool = Field(default=False, description="Whether this row materially affects final outcome.")
    min_rank_pred: int = Field(description="预测最低位次（基于2021-2023历史数据）")
    rank_diff: int = Field(default=0, description="位次差（预测最低位次 - 用户位次）")  # 修复新问题1：添加rank_diff字段
    rank_ci_lower: int = Field(description="位次置信区间下界（布林带）")
    rank_ci_upper: int = Field(description="位次置信区间上界")

    # 量化信号
    fear_index: float = Field(default=0.0, description="恐惧指数（-3到3，负值表示超卖）")
    volatility: VolatilityLevel = Field(default=VolatilityLevel.MEDIUM, description="波动率等级")
    quota: Optional[int] = Field(default=None, description="该院校专业组2025招生计划总数")
    quota_bucket: QuotaBucket = Field(default=QuotaBucket.UNKNOWN, description="招生计划规模分桶")
    quota_stability_score: float = Field(default=0.0, ge=0, le=1, description="招生计划带来的稳定性信号")
    variance_opportunity_score: float = Field(default=0.0, ge=0, le=1, description="高波动捡漏机会信号")

    # 调剂风险
    adjustment_risk: float = Field(default=0.0, ge=0, le=1, description="调剂概率")
    worst_case_major: Optional[str] = Field(None, description="最差调剂专业")
    is_blacklist_risk: bool = Field(default=False, description="是否可能调剂到黑名单专业")
    acceptable_major_ratio: float = Field(default=1.0, ge=0, le=1, description="组内用户可接受专业占比")
    blacklist_major_ratio: float = Field(default=0.0, ge=0, le=1, description="组内黑名单专业占比")
    major_utility_mean: float = Field(default=0.5, ge=0, le=1, description="组内专业平均用户效用")
    major_utility_min: float = Field(default=0.5, ge=0, le=1, description="组内专业最低用户效用")
    major_utility_dispersion: float = Field(default=0.0, ge=0, le=1, description="组内专业效用差异")
    tail_assignment_risk: float = Field(default=0.0, ge=0, le=1, description="服从调剂后的尾部专业风险")
    bundle_type: BundleType = Field(default=BundleType.UNKNOWN, description="专业组混搭风险类型")
    obey_adjustment: bool = Field(default=True, description="是否建议服从专业调剂")
    adjustment_advice: AdjustmentAdvice = Field(default=AdjustmentAdvice.CAUTIOUS, description="服从调剂建议")
    recommendation_role: str = Field(default="", description="该专业组在组合中的角色")
    risk_reasons: List[str] = Field(default_factory=list, description="风险原因解释")
    audit_flags: List[str] = Field(default_factory=list, description="需要审计或人工复核的标记")
    score_band: str = Field(default="", description="Rank-band tradeoff policy used for this row")
    tradeoff_breakdown: Dict[str, float] = Field(default_factory=dict, description="Auditable tradeoff score terms")
    pain_point_flags: List[str] = Field(default_factory=list, description="User pain points triggered by this row")
    market_behavior_notes: List[str] = Field(default_factory=list, description="Parallel-volunteer market behavior notes")
    tradeoff_summary: str = Field(default="", description="One-line tradeoff explanation")
    arbitrage_score: float = Field(default=0.0, ge=0, le=1, description="Personalized arbitrage score")
    front_major_arbitrage_score: float = Field(default=0.0, ge=0, le=1, description="Front-major arbitrage score")
    relative_lift: float = Field(default=0.0, ge=0, le=1, description="Lift versus same-rank baseline")
    market_discount_score: float = Field(default=0.0, ge=0, le=1, description="Market discount score")
    personal_acceptability: float = Field(default=0.0, ge=0, le=1, description="Student-specific acceptability")
    sacrifice_cost: float = Field(default=0.0, ge=0, le=1, description="Student-specific sacrifice cost")
    assignment_opportunity: float = Field(default=0.0, ge=0, le=1, description="Within-group assignment opportunity")
    front_major_hit_prob: float = Field(default=0.0, ge=0, le=1, description="Estimated front-major hit probability")
    rebound_risk: float = Field(default=0.0, ge=0, le=1, description="Risk that a known leak rebounds")
    opportunity_types: List[str] = Field(default_factory=list, description="Detected arbitrage mechanisms")
    opportunity_pools: List[str] = Field(default_factory=list, description="Portfolio pools this row can enter")
    arbitrage_breakdown: Dict[str, float] = Field(default_factory=dict, description="Auditable arbitrage score terms")
    market_evidence_cards: List[Dict[str, Any]] = Field(default_factory=list, description="Auditable market evidence cards")
    market_evidence_strength: float = Field(default=0.0, ge=0, le=1, description="Confidence of available public evidence")
    publicity_heat_score: float = Field(default=0.0, ge=0, le=1, description="Publicity or counselor-promotion heat signal")
    publicity_rebound_risk: float = Field(default=0.0, ge=0, le=1, description="Risk that a known opportunity rebounds after publicity")
    segment_demand_score: float = Field(default=0.0, ge=0, le=1, description="Demand predicted by student/family archetype simulation")
    low_attention_signal: float = Field(default=0.0, ge=0, le=1, description="How hidden the opportunity remains after publicity effects")
    segment_rebound_risk: float = Field(default=0.0, ge=0, le=1, description="Rebound risk estimated from segment demand and publicity")
    best_fit_archetypes: List[str] = Field(default_factory=list, description="Student/family archetypes most able to absorb sacrifices")
    segment_demand_breakdown: Dict[str, float] = Field(default_factory=dict, description="Per-archetype demand-fit scores")
    plan_change_score: float = Field(default=0.0, ge=0, le=1, description="Opportunity signal from enrollment-plan changes")
    plan_change_types: List[str] = Field(default_factory=list, description="Enrollment-plan change mechanisms")
    plan_change_evidence: List[str] = Field(default_factory=list, description="Auditable enrollment-plan change evidence")

    # 策略标签
    strategy_tag: StrategyTag

    # 综合评分（用于排序）
    comprehensive_score: float = Field(default=0.0, ge=0, le=1, description="综合评分（0-1），用于排序")

    # 舆情修正（简化版）
    sentiment_score: float = Field(default=0.0, ge=-1, le=1, description="舆情修正系数")
    news_summary: Optional[str] = Field(None, description="舆情摘要")

    # 用户选择状态（前端交互用）
    is_selected: bool = Field(default=False, description="用户是否选择此专业组")

    def apply_arbitrage_result(self, result: Any) -> None:
        """Attach a quantitative arbitrage result to this major-group row."""
        self.arbitrage_score = result.arbitrage_score
        self.front_major_arbitrage_score = result.front_major_arbitrage_score
        self.relative_lift = result.relative_lift
        self.market_discount_score = result.market_discount_score
        self.personal_acceptability = result.personal_acceptability
        self.sacrifice_cost = result.sacrifice_cost
        self.assignment_opportunity = result.assignment_opportunity
        self.front_major_hit_prob = result.front_major_hit_prob
        self.rebound_risk = result.rebound_risk
        self.opportunity_types = list(result.opportunity_types)
        self.arbitrage_breakdown = dict(result.breakdown)
        self.opportunity_pools = self._infer_opportunity_pools()

    def _infer_opportunity_pools(self) -> List[str]:
        """Route this row into coarse opportunity pools for portfolio planning."""
        pools: List[str] = []
        if self.front_major_arbitrage_score >= 0.10 and self.front_major_hit_prob >= 0.40:
            pools.append("front_major_arbitrage_pool")
        if self.arbitrage_score >= 0.55 and self.relative_lift >= 0.20:
            pools.append("relative_tier_lift_pool")
        if self.market_discount_score >= 0.35 and self.personal_acceptability >= 0.65:
            pools.append("market_discount_pool")
        if self.strategy_tag == StrategyTag.SAFE or self.admission_prob >= 0.85:
            pools.append("safe_anchor_pool")
        elif self.strategy_tag == StrategyTag.TARGET:
            pools.append("target_core_pool")
        elif not pools:
            pools.append("rush_opportunity_pool")
        return pools


class GameRow(BaseModel):
    """博弈矩阵的单行（单个专业，旧模型，保留兼容性）"""
    # 基础信息
    school_name: str
    major_name: str
    major_group: str = Field(default="", description="专业组代码（调剂范围）")

    # 核心指标
    admission_prob: float = Field(ge=0, le=1, description="录取概率")
    min_rank_pred: int = Field(description="预测最低位次")
    rank_ci_lower: int = Field(description="位次置信区间下界（布林带）")
    rank_ci_upper: int = Field(description="位次置信区间上界")

    # 量化信号
    fear_index: float = Field(default=0.0, description="恐惧指数（-3到3，负值表示超卖）")
    volatility: VolatilityLevel = Field(default=VolatilityLevel.MEDIUM, description="波动率等级")

    # 调剂风险
    adjustment_risk: float = Field(default=0.0, ge=0, le=1, description="调剂概率")
    worst_case_major: Optional[str] = Field(None, description="最差调剂专业")
    is_blacklist_risk: bool = Field(default=False, description="是否可能调剂到黑名单专业")

    # 策略标签
    strategy_tag: StrategyTag

    # 舆情修正（简化版）
    sentiment_score: float = Field(default=0.0, ge=-1, le=1, description="舆情修正系数")
    news_summary: Optional[str] = Field(None, description="舆情摘要")


class GameMatrix(BaseModel):
    """完整的博弈矩阵（专业组级别）

    推荐策略：
    - 冲刺10个专业组（录取概率 < 60%）
    - 稳妥10个专业组（录取概率 60-90%）
    - 保底10个专业组（录取概率 >= 90%）
    - 共30个专业组供用户选择
    """
    major_group_rows: List[MajorGroupRow] = Field(default_factory=list, description="专业组推荐列表")
    rows: List[GameRow] = Field(default_factory=list, description="单个专业列表（旧模型，保留兼容性）")

    # 全局统计
    total_rush: int = Field(default=0, description="冲刺类志愿数量")
    total_target: int = Field(default=0, description="稳妥类志愿数量")
    total_safe: int = Field(default=0, description="保底类志愿数量")

    # 风险指标
    expected_utility: float = Field(default=0.0, description="期望效用（加权平均录取概率）")
    portfolio_risk: float = Field(default=0.0, description="投资组合风险（方差）")

    # 是否符合纳什均衡
    is_balanced: bool = Field(default=False, description="是否符合均衡策略（冲稳保比例合理）")

    # Runtime RL metadata
    agentic_rl_used: bool = Field(default=False, description="是否使用 runtime RL 策略")
    selection_method: str = Field(default="heuristic", description="推荐生成方法")
    optimization_summary: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Runtime RL 和组合优化摘要",
    )
    volunteer_plan: Optional[VolunteerPlan] = Field(default=None, description="广东志愿表草案")

    def calculate_statistics(self):
        """计算全局统计（基于专业组）- 修复：添加除零检查"""
        if not self.major_group_rows or len(self.major_group_rows) == 0:
            return

        self.total_rush = sum(1 for r in self.major_group_rows if r.strategy_tag == StrategyTag.RUSH)
        self.total_target = sum(1 for r in self.major_group_rows if r.strategy_tag == StrategyTag.TARGET)
        self.total_safe = sum(1 for r in self.major_group_rows if r.strategy_tag == StrategyTag.SAFE)

        # 修复：期望效用（防止除零）
        total_count = len(self.major_group_rows)
        if total_count > 0:
            self.expected_utility = sum(r.admission_prob for r in self.major_group_rows) / total_count
        else:
            self.expected_utility = 0.0

        # 修复：投资组合风险（简化：标准差，防止除零）
        if total_count > 0:
            mean_prob = self.expected_utility
            variance = sum((r.admission_prob - mean_prob) ** 2 for r in self.major_group_rows) / total_count
            self.portfolio_risk = variance ** 0.5
        else:
            self.portfolio_risk = 0.0

        # 纳什均衡检验（冲稳保比例合理）
        total = len(self.major_group_rows)
        self.is_balanced = (
            self.total_rush >= 8 and self.total_rush <= 12 and  # 冲刺8-12个
            self.total_target >= 8 and self.total_target <= 12 and  # 稳妥8-12个
            self.total_safe >= 8 and self.total_safe <= 12  # 保底8-12个
        )

        if self.volunteer_plan:
            self.volunteer_plan.calculate_statistics()
