"""用户画像数据模型"""
from pydantic import BaseModel, Field, model_validator
from typing import Any, List, Dict, Optional
from enum import Enum


class RiskTolerance(str, Enum):
    """风险偏好类型"""
    CONSERVATIVE = "conservative"  # 保守型（稳>70%）
    BALANCED = "balanced"         # 平衡型（冲30% 稳50% 保20%）
    AGGRESSIVE = "aggressive"     # 激进型（冲>50%）


class SchoolMajorPreference(str, Enum):
    """学校-专业权衡偏好"""
    PRIORITIZE_SCHOOL = "prioritize_school"   # 优先选择好学校（可接受冷门专业）
    BALANCED = "balanced"                     # 学校和专业兼顾
    PRIORITIZE_MAJOR = "prioritize_major"     # 优先选择好专业（可接受学校降档）
    UNKNOWN = "unknown"                       # 用户未明确（需要询问）


class HollandCode(BaseModel):
    """霍兰德职业兴趣代码（简化版）"""
    realistic: float = Field(default=0.5, ge=0, le=1, description="R: 实用型")
    investigative: float = Field(default=0.5, ge=0, le=1, description="I: 研究型")
    artistic: float = Field(default=0.5, ge=0, le=1, description="A: 艺术型")
    social: float = Field(default=0.5, ge=0, le=1, description="S: 社会型")
    enterprising: float = Field(default=0.5, ge=0, le=1, description="E: 企业型")
    conventional: float = Field(default=0.5, ge=0, le=1, description="C: 常规型")


class UserProfile(BaseModel):
    """用户完整画像"""
    # 硬性指标
    score: int = Field(description="高考总分")
    rank: Optional[int] = Field(None, description="全省位次")  # 修复新问题6：允许为None
    subject_group: str = Field(description="选科组合，如 '物理' 或 '历史'")

    # 地理偏好
    preferred_cities: List[str] = Field(default_factory=list, description="偏好城市")
    excluded_cities: List[str] = Field(default_factory=list, description="排除城市")

    # 专业偏好（核心创新）
    preferred_majors: List[str] = Field(default_factory=list, description="意向专业关键词")
    blacklist_majors: List[str] = Field(
        default_factory=list,
        description="🚨 负面清单：绝对不学的专业关键词"
    )

    # 隐性权重（简化版：后期可用 LLM 推断）
    holland_code: Optional[HollandCode] = Field(default_factory=HollandCode)
    mbti_type: Optional[str] = Field(None, description="MBTI 类型，如 INTJ（暂不实现）")

    # 风险定价
    risk_tolerance: RiskTolerance = RiskTolerance.BALANCED

    # 学校-专业权衡偏好（新增）
    school_major_preference: SchoolMajorPreference = SchoolMajorPreference.UNKNOWN

    # LLM-extracted behavioral signals. These fields should not directly decide
    # admission probability; they explain user-side assumptions and regret risk.
    stated_misconceptions: List[str] = Field(
        default_factory=list,
        description="Possible misconceptions explicitly or implicitly present in the user request",
    )
    emotional_concerns: List[str] = Field(
        default_factory=list,
        description="User anxieties such as sliding, wasting score, being exploited, or family conflict",
    )
    family_pressure_points: List[str] = Field(
        default_factory=list,
        description="Family or peer pressure signals that may distort stated preference",
    )
    preference_assumptions: List[str] = Field(
        default_factory=list,
        description="Unverified assumptions behind the user's school, major, city, or career preference",
    )
    preference_confidence: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="How reliable the stated preference appears after parsing",
    )
    major_cognition_risk: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Risk that the user misunderstands major content, career path, or major-group composition",
    )
    regret_sensitivity: float = Field(
        default=0.5,
        ge=0,
        le=1,
        description="How sensitive the user appears to ex-post regret, justified envy, and tail assignment",
    )

    # 体检限制（简化版）
    medical_restrictions: Dict[str, bool] = Field(
        default_factory=dict,
        description="如 {'color_blind': False, 'myopia': False}"
    )

    # 单科成绩（可选）
    subject_scores: Optional[Dict[str, int]] = Field(
        None,
        description="如 {'数学': 145, '英语': 138}"
    )

    @model_validator(mode="before")
    @classmethod
    def coerce_null_defaults(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        data = dict(data)

        for key in (
            "preferred_cities",
            "excluded_cities",
            "preferred_majors",
            "blacklist_majors",
            "stated_misconceptions",
            "emotional_concerns",
            "family_pressure_points",
            "preference_assumptions",
        ):
            if data.get(key) is None:
                data[key] = []

        if data.get("medical_restrictions") is None:
            data["medical_restrictions"] = {}

        return data

    class Config:
        json_schema_extra = {
            "example": {
                "score": 620,
                "rank": 12000,
                "subject_group": "物理",
                "preferred_cities": ["北京", "上海"],
                "preferred_majors": ["计算机", "人工智能"],
                "blacklist_majors": ["土木", "化工"],
                "risk_tolerance": "balanced",
                "emotional_concerns": ["fear of sliding to unwanted majors"],
                "preference_assumptions": ["computer science is assumed to be the only high-employment major"],
                "preference_confidence": 0.55,
                "major_cognition_risk": 0.4,
                "regret_sensitivity": 0.7,
            }
        }
