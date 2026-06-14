"""Smoke checks for backend API normalization and runtime status helpers."""

import asyncio
import json
from pathlib import Path
from tempfile import TemporaryDirectory

import main
from main import QueryRequest, build_user_message, get_runtime_status, get_stats


def test_subject_group_variants_are_normalized_to_chinese_labels():
    cases = {
        "物理类": "物理",
        "物": "物理",
        "physics": "物理",
        "Physics": "物理",
        "历史类": "历史",
        "历": "历史",
        "history": "历史",
        "History": "历史",
    }

    for raw_value, expected in cases.items():
        request = QueryRequest(
            message="请帮我规划志愿",
            score=620,
            rank=12000,
            subject_group=raw_value,
        )

        assert request.subject_group == expected


def test_build_user_message_uses_normalized_structured_context():
    request = QueryRequest(
        message="想学计算机，最好在广州。",
        score=620,
        rank=12000,
        subject_group="Physics",
    )

    message = build_user_message(request)

    assert "我的高考信息如下" in message
    assert "- 总分：620" in message
    assert "- 全省位次：12000" in message
    assert "- 选科组合：物理" in message
    assert "想学计算机，最好在广州。" in message


def test_query_request_builds_authoritative_structured_profile_payload():
    assert hasattr(main, "build_explicit_profile_payload")

    request = QueryRequest(
        message="正文里写的是激进，但应以表单结构化选择为准。",
        score=620,
        rank=12000,
        subject_group="physics",
        delivery_profile={
            "preferred_cities": ["广州"],
            "excluded_cities": ["北京"],
            "preferred_majors": ["计算机"],
            "blacklist_majors": ["土木"],
            "risk_tolerance": "conservative",
            "school_major_preference": "prioritize_major",
        },
    )

    payload = main.build_explicit_profile_payload(request)

    assert payload["score"] == 620
    assert payload["rank"] == 12000
    assert payload["subject_group"] == "物理"
    assert payload["risk_tolerance"] == "conservative"
    assert payload["preferred_cities"] == ["广州"]
    assert payload["blacklist_majors"] == ["土木"]


def test_query_request_scores_raw_career_assessment_into_profile_payload():
    answers = {
        f"{dimension}{index}": 5 if dimension == "I" else 2
        for dimension in "RIASEC"
        for index in range(1, 3)
    }
    request = QueryRequest(
        message="使用职业兴趣测评结果生成方案。",
        score=620,
        rank=12000,
        subject_group="physics",
        delivery_profile={
            "career_assessment": {
                "mode": "quick",
                "answers": answers,
                "mbti_type": "intj",
                "career_values": ["growth", "autonomy"],
            }
        },
    )

    payload = main.build_explicit_profile_payload(request)

    assert payload["career_assessment_status"] == "completed"
    assert payload["career_assessment_mode"] == "quick"
    assert payload["holland_code"]["investigative"] == 1.0
    assert payload["riasec_top_codes"][0] == "I"
    assert payload["mbti_type"] == "INTJ"
    assert payload["career_values"] == ["growth", "autonomy"]
    assert payload["_field_provenance"]["holland_code"] == "measured_assessment"
    assert payload["_field_provenance"]["mbti_type"] == "user_explicit"


def test_runtime_status_exposes_backend_and_agent_capabilities():
    status = get_runtime_status()

    assert status["service"] == "GaokaoAgent"
    assert status["status"] == "running"
    assert status["runtime"]["environment"] in {"development", "production"}
    assert status["capabilities"]["structured_recommendation"] is True
    assert status["capabilities"]["multi_agent_deliberation"] is True
    assert status["capabilities"]["critic_audit"] is True
    assert "/api/delivery/preview" in status["entrypoints"]["api"]
    assert "smoke" in status["entrypoints"]["cli_commands"]


def test_delivery_preview_endpoint_builds_internal_preflight_bundle():
    from main import DeliveryPreviewRequest, preview_delivery_bundle

    request = DeliveryPreviewRequest(
        profile={
            "score": 620,
            "rank": 12000,
            "subject_group": "physics",
            "preferred_cities": ["广州"],
            "preferred_majors": ["计算机"],
            "blacklist_majors": ["土木"],
            "risk_tolerance": "balanced",
        },
        report="""
# 志愿填报建议

学生位次 12000，620 分，选科物理，城市偏好广州。限制条件包括专业偏好和黑名单专业。
推荐 A 大学。概率不是保证，存在滑档、调剂、尾部专业、黑名单和浪费分风险。
第1志愿：A 大学 201 专业组，专业1-6：计算机类、软件工程，调剂建议谨慎。量化校验：位次缓冲和历史数据置信。
最终以官方招生章程、考试院数据和政策更新为准，仅供参考，请家长复核。
""",
        case_id="api-smoke-delivery",
    )

    response = asyncio.run(preview_delivery_bundle(request))

    assert response.case_id == "api-smoke-delivery"
    assert response.manifest["status"] in {"pending_signoff", "needs_revision"}
    assert response.manifest["intake_status"] in {
        "ready_for_recommendation",
        "needs_clarification",
    }
    assert "expectation_packet" in response.artifacts
    assert "report_quality_audit" in response.artifacts


def test_agency_command_center_reads_delivery_bundle_logs():
    from main import build_agency_command_center_from_logs

    with TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        for case_id, status, gates in [
            (
                "case-ready",
                "ready_to_deliver",
                [
                    {"gate": "intake_audit", "status": "ready_for_recommendation"},
                    {"gate": "plan_quality", "status": "pass"},
                    {"gate": "report_quality", "status": "pass"},
                ],
            ),
            (
                "case-blocked",
                "blocked",
                [
                    {"gate": "intake_audit", "status": "blocked_missing_core"},
                    {"gate": "plan_quality", "status": "not_provided"},
                    {"gate": "report_quality", "status": "pass"},
                ],
            ),
        ]:
            case_dir = root / case_id
            case_dir.mkdir(parents=True)
            (case_dir / "delivery_bundle.json").write_text(
                json.dumps(
                    {
                        "case_id": case_id,
                        "status": status,
                        "intake_readiness_score": 0.4 if status == "blocked" else 0.9,
                        "plan_quality_score": 0.0 if status == "blocked" else 0.9,
                        "report_quality_score": 0.7,
                        "delivery_gates": gates,
                        "next_actions": ["Repair intake."] if status == "blocked" else [],
                    }
                ),
                encoding="utf-8",
            )

        response = build_agency_command_center_from_logs(root)

    assert response["success"] is True
    assert response["audit"]["agency_positioning"] == "head_advisor_command_center"
    assert response["audit"]["portfolio"]["case_count"] == 2
    assert response["audit"]["escalation_queue"][0]["case_id"] == "case-blocked"
    assert "Agency Command Center" in response["markdown"]


def test_stats_endpoint_uses_prediction_history_data():
    stats = asyncio.run(get_stats())

    assert stats["total_records"] > 0
    assert 2024 in stats["years"]
    assert stats["latest_year"] == 2024
