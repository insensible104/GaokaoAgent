"""审计结果数据模型"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class AuditStatus(str, Enum):
    """审计状态"""
    PASS = "pass"                              # 通过
    REJECT_LOGIC = "reject_logic"             # 逻辑不自洽
    REJECT_POLICY = "reject_policy"           # 政策违规
    REJECT_ADJUSTMENT = "reject_adjustment"   # 调剂风险未确认


class AuditResult(BaseModel):
    """审计结果"""
    status: AuditStatus = AuditStatus.PASS
    issues: List[str] = Field(default_factory=list, description="发现的问题清单")

    # 如果驳回，指定回退目标
    reroute_to: Optional[str] = Field(None, description="回退到哪个 Agent")
    fix_suggestions: List[str] = Field(default_factory=list, description="修正建议")

    @property
    def is_approved(self) -> bool:
        """是否通过审计"""
        return self.status == AuditStatus.PASS

    def add_issue(self, issue: str, suggestion: str = ""):
        """添加问题"""
        self.issues.append(issue)
        if suggestion:
            self.fix_suggestions.append(suggestion)
