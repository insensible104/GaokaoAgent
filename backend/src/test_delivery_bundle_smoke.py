"""Smoke tests for client delivery bundle generation."""

from __future__ import annotations

from pathlib import Path
import tempfile

from evaluation.delivery_bundle import build_delivery_bundle
from models.game_matrix import AdjustmentAdvice, MajorOption, StrategyTag, VolunteerChoice, VolunteerPlan
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile


def _valid_plan() -> VolunteerPlan:
    def choice(index: int, prob: float, strategy: StrategyTag) -> VolunteerChoice:
        return VolunteerChoice(
            choice_index=index,
            school_code=f"S{index}",
            school_name=f"测试大学{index}",
            major_group_code=f"20{index}",
            major_choices=[
                MajorOption(
                    school_code=f"S{index}",
                    school_name=f"测试大学{index}",
                    major_group_code=f"20{index}",
                    major_name="计算机类",
                    is_preferred=True,
                    user_utility=0.85,
                    major_rank_risk=0.10,
                )
            ],
            obey_adjustment=True,
            adjustment_advice=AdjustmentAdvice.RECOMMEND,
            group_admission_prob=prob,
            expected_major_utility=0.85,
            tail_assignment_risk=0.08,
            strategy_tag=strategy,
            explanation="位次缓冲、概率和专业组结构均已解释。",
            quant_evidence=["rank_buffer=stable", "data_confidence=0.80"],
        )

    return VolunteerPlan(
        province="广东",
        year=2025,
        subject_group="物理",
        user_score=620,
        user_rank=12000,
        choices=[
            choice(1, 0.35, StrategyTag.RUSH),
            choice(2, 0.55, StrategyTag.TARGET),
            choice(3, 0.98, StrategyTag.SAFE),
        ],
    )


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
            plan=_valid_plan(),
            case_id="case-smoke",
        )

        assert manifest["case_id"] == "case-smoke"
        assert manifest["status"] == "pending_signoff"
        assert manifest["client_delivery"]["allowed"] is True
        assert manifest["client_delivery"]["status"] == "allowed"
        signoff_ids = {item["id"] for item in manifest["client_signoff_checklist"]}
        assert "constraint_freeze" in signoff_ids
        assert "non_guarantee" in signoff_ids
        assert manifest["intake_status"] == "ready_for_recommendation"
        assert manifest["plan_quality_status"] == "pass"
        audiences = {item["id"]: item["audience"] for item in manifest["artifacts"]}
        assert audiences["expectation_packet"] == "client_confirmation"
        assert audiences["final_report"] == "client_confirmation"
        assert audiences["intake_audit"] == "internal_review"
        assert audiences["plan_quality_audit"] == "internal_review"
        assert audiences["report_quality_audit"] == "internal_review"
        assert (output_dir / "intake_audit.md").exists()
        assert (output_dir / "plan_quality_audit.md").exists()
        assert (output_dir / "expectation_packet.md").exists()
        assert (output_dir / "final_report.md").exists()
        assert (output_dir / "report_quality_audit.md").exists()
        assert (output_dir / "delivery_bundle.md").exists()
        assert "服务交付包" in (output_dir / "delivery_bundle.md").read_text(encoding="utf-8")
        assert "客户签收清单" in (output_dir / "delivery_bundle.md").read_text(encoding="utf-8")


def test_delivery_bundle_requires_plan_quality_artifact() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=["广州"],
        preferred_majors=["计算机"],
        risk_tolerance=RiskTolerance.BALANCED,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_MAJOR,
    )
    report = "位次 12000，620 分，选科物理。推荐 A 大学。概率不是保证，风险需复核，最终以官方招生章程为准。"
    with tempfile.TemporaryDirectory() as temp_dir:
        output_dir = Path(temp_dir) / "bundle"
        manifest = build_delivery_bundle(
            profile=profile,
            report_payload=report,
            output_dir=output_dir,
            case_id="case-missing-plan",
        )

        assert manifest["status"] == "needs_revision"
        assert manifest["client_delivery"]["allowed"] is False
        assert manifest["client_delivery"]["status"] == "blocked"
        assert "客户确认包" in manifest["client_delivery"]["blocked_reason"]
        assert manifest["plan_quality_status"] == "not_provided"
        assert (output_dir / "plan_quality_audit.md").exists()
        assert "VolunteerPlan JSON" in (output_dir / "plan_quality_audit.md").read_text(encoding="utf-8")


if __name__ == "__main__":
    test_delivery_bundle_writes_client_artifacts()
    test_delivery_bundle_requires_plan_quality_artifact()
    print("delivery bundle smoke tests passed")
