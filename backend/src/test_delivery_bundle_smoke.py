"""Smoke tests for client delivery bundle generation."""

from __future__ import annotations

from pathlib import Path
import tempfile

from evaluation.delivery_bundle import build_delivery_bundle
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def test_delivery_bundle_writes_client_artifacts() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州", "深圳"],
        preferred_majors=["计算机"],
        blacklist_majors=["土木"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )
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
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "bundle"
        manifest = build_delivery_bundle(
            profile=profile,
            report_payload=report,
            output_dir=output_dir,
            case_id="case-smoke",
        )

        assert manifest["case_id"] == "case-smoke"
        assert manifest["status"] == "pending_signoff"
        assert (output_dir / "expectation_packet.md").exists()
        assert (output_dir / "final_report.md").exists()
        assert (output_dir / "report_quality_audit.md").exists()
        assert (output_dir / "delivery_bundle.md").exists()
        assert "服务交付包" in (output_dir / "delivery_bundle.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    test_delivery_bundle_writes_client_artifacts()
    print("delivery bundle smoke tests passed")
