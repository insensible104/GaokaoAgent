"""报告草案数据模型"""
from pydantic import BaseModel, Field
from typing import List


class ReportDraft(BaseModel):
    """报告草案"""
    title: str = Field(default="GaokaoAgent 志愿填报战略建议书")

    # 分段内容
    executive_summary: str = Field(default="", description="执行摘要")
    strategy_analysis: str = Field(default="", description="策略分析（冲稳保比例）")
    school_recommendations: List[str] = Field(
        default_factory=list,
        description="院校推荐（带因果解释）"
    )
    risk_warnings: List[str] = Field(default_factory=list, description="风险警示")
    regret_value: float = Field(default=0.0, description="遗憾值（滑档代价）")

    # Markdown 全文
    full_markdown: str = Field(default="", description="完整的 Markdown 报告")

    def generate_markdown(self):
        """生成完整的 Markdown 报告"""
        sections = [
            f"# {self.title}\n",
            f"## 执行摘要\n{self.executive_summary}\n",
            f"## 策略分析\n{self.strategy_analysis}\n",
            "## 院校推荐\n",
        ]

        for idx, rec in enumerate(self.school_recommendations, 1):
            sections.append(f"{idx}. {rec}\n")

        if self.risk_warnings:
            sections.append("\n## [WARN] 风险警示\n")
            for warning in self.risk_warnings:
                sections.append(f"- {warning}\n")

        sections.append(f"\n## 遗憾值分析\n如果滑档，您的位次分差成本约为：**{self.regret_value:.0f}位**\n")

        self.full_markdown = "\n".join(sections)
        return self.full_markdown

