"""用户意图分类模型"""
from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional


class IntentType(str, Enum):
    """用户意图类型（对应双循环路由）"""
    QUANT = "quant"           # 定量分析：录取概率、位次预测、冲稳保策略
    RESEARCH = "research"     # 深度研究：院校评价、专业前景、就业去向
    MULTIMODAL = "multimodal" # 多模态：招生章程、体检限制、政策解读
    MIXED = "mixed"           # 混合型：需要多个循环协作


class IntentClassification(BaseModel):
    """意图分类结果"""
    primary_intent: IntentType = Field(
        description="主要意图类型"
    )

    secondary_intents: List[IntentType] = Field(
        default_factory=list,
        description="次要意图（用于混合型任务）"
    )

    reasoning: str = Field(
        description="分类推理过程（用于 SFT 训练数据生成）"
    )

    requires_quant: bool = Field(
        default=False,
        description="是否需要量化引擎（访问 CSV 数据）"
    )

    requires_search: bool = Field(
        default=False,
        description="是否需要网络搜索（Tavily）"
    )

    requires_vision: bool = Field(
        default=False,
        description="是否需要多模态模型（PDF/图像）"
    )

    confidence: float = Field(
        ge=0.0, le=1.0,
        description="分类置信度（0-1）"
    )

    @property
    def should_use_fast_loop(self) -> bool:
        """是否使用快思考循环（Quant）"""
        return self.requires_quant

    @property
    def should_use_slow_loop(self) -> bool:
        """是否使用慢思考循环（Research）"""
        return self.requires_search

    @property
    def should_use_multimodal(self) -> bool:
        """是否使用多模态能力"""
        return self.requires_vision


class LoopType(str, Enum):
    """执行循环类型"""
    FAST = "fast"       # 快思考：结构化数据分析（Quant Engine）
    SLOW = "slow"       # 慢思考：非结构化研究（Deep Research）
    MULTIMODAL = "multimodal"  # 多模态：PDF/图像处理
    HYBRID = "hybrid"   # 混合：需要多个循环协作
