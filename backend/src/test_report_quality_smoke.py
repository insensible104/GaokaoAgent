"""Smoke tests for report delivery-quality audits."""

from __future__ import annotations

from evaluation.report_quality import (
    audit_report_quality,
    build_markdown_report_quality_audit,
)


def test_report_quality_audit_passes_complete_delivery() -> None:
    report = """
# GaokaoAgent 志愿填报战略建议书

## 执行摘要
学生当前位次 12000，620 分，选科物理，省内城市偏好广州深圳。限制条件包括城市偏好、专业偏好、预算边界和黑名单专业确认。

## 策略分析
本方案按冲稳保组合处理，所有概率不是保证，存在不确定性，最终以官方招生章程和考试院数据为准，需要家长复核。

## 院校推荐
1. 第1志愿 A大学 201专业组 (单点投档概率 70.0%, 首命中概率 20.0%, 专业1-6：计算机类、软件工程, 调剂建议 cautious, 尾部风险 18%)；量化校验: 位次缓冲 +1000 名；数据置信=0.80；关键志愿解释：机会逻辑充分。

## [WARN] 风险警示
- 滑档风险、调剂风险、尾部专业风险、黑名单风险和浪费分风险均需复核。

## 免责与复核
本报告仅供参考，不保证录取；最终以官方政策、招生章程和数据更新为准。
"""
    result = audit_report_quality(report)

    assert result["status"] == "pass"
    assert result["total_score"] >= 0.78
    assert result["finding_count"] == 0
    markdown = build_markdown_report_quality_audit(result)
    assert "Report Quality Audit" in markdown
    assert "student_context" in markdown


def test_report_quality_audit_flags_missing_boundaries() -> None:
    report = "推荐 A大学、B大学，概率较高。"
    result = audit_report_quality(report)

    assert result["status"] == "needs_revision"
    assert result["finding_count"] > 0
    assert any(item["area"] == "risk_explanation" for item in result["findings"])
    assert any(item["area"] == "disclaimer_boundary" for item in result["findings"])


if __name__ == "__main__":
    test_report_quality_audit_passes_complete_delivery()
    test_report_quality_audit_flags_missing_boundaries()
    print("report quality smoke tests passed")
