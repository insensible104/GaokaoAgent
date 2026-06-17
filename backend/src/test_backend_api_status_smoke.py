"""Smoke checks for backend API normalization and runtime status helpers."""

import asyncio

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


def test_runtime_status_exposes_backend_and_agent_capabilities():
    status = get_runtime_status()

    assert status["service"] == "GaokaoAgent"
    assert status["status"] == "running"
    assert status["runtime"]["environment"] in {"development", "production"}
    assert status["capabilities"]["structured_recommendation"] is True
    assert status["capabilities"]["multi_agent_deliberation"] is True
    assert status["capabilities"]["critic_audit"] is True
    assert "/api/delivery/preview" in status["entrypoints"]["api"]
    assert "/api/delivery/portfolio" in status["entrypoints"]["api"]
    assert "smoke" in status["entrypoints"]["cli_commands"]


def test_delivery_preview_endpoint_builds_internal_preflight_bundle():
    from main import DeliveryPreviewRequest, preview_delivery_bundle

    plan = {
        "province": "广东",
        "year": 2025,
        "subject_group": "物理",
        "user_score": 620,
        "user_rank": 12000,
        "choices": [
            {
                "choice_index": 1,
                "school_code": "A001",
                "school_name": "A大学",
                "major_group_code": "201",
                "major_choices": [
                    {
                        "school_code": "A001",
                        "school_name": "A大学",
                        "major_group_code": "201",
                        "major_name": "计算机类",
                        "is_preferred": True,
                        "user_utility": 0.86,
                        "major_rank_risk": 0.12,
                    }
                ],
                "obey_adjustment": True,
                "adjustment_advice": "recommend",
                "group_admission_prob": 0.38,
                "expected_major_utility": 0.86,
                "tail_assignment_risk": 0.10,
                "strategy_tag": "rush",
                "explanation": "位次缓冲、概率和专业组结构均已解释。",
                "quant_evidence": ["rank_buffer=rush", "data_confidence=0.80"],
            },
            {
                "choice_index": 2,
                "school_code": "B001",
                "school_name": "B大学",
                "major_group_code": "202",
                "major_choices": [
                    {
                        "school_code": "B001",
                        "school_name": "B大学",
                        "major_group_code": "202",
                        "major_name": "软件工程",
                        "is_preferred": True,
                        "user_utility": 0.82,
                        "major_rank_risk": 0.10,
                    }
                ],
                "obey_adjustment": True,
                "adjustment_advice": "recommend",
                "group_admission_prob": 0.72,
                "expected_major_utility": 0.82,
                "tail_assignment_risk": 0.08,
                "strategy_tag": "target",
                "explanation": "稳妥区关键志愿，位次缓冲和专业可接受度均已解释。",
                "quant_evidence": ["rank_buffer=stable", "data_confidence=0.82"],
            },
            {
                "choice_index": 3,
                "school_code": "C001",
                "school_name": "C大学",
                "major_group_code": "203",
                "major_choices": [
                    {
                        "school_code": "C001",
                        "school_name": "C大学",
                        "major_group_code": "203",
                        "major_name": "信息管理",
                        "is_acceptable": True,
                        "user_utility": 0.72,
                        "major_rank_risk": 0.08,
                    }
                ],
                "obey_adjustment": True,
                "adjustment_advice": "recommend",
                "group_admission_prob": 0.98,
                "expected_major_utility": 0.72,
                "tail_assignment_risk": 0.06,
                "strategy_tag": "safe",
                "explanation": "保底安全垫，专业组尾部风险可承受。",
                "quant_evidence": ["rank_buffer=safe", "data_confidence=0.86"],
            },
        ],
    }
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
        plan=plan,
        case_id="api-smoke-delivery",
    )

    response = asyncio.run(preview_delivery_bundle(request))

    assert response.case_id == "api-smoke-delivery"
    assert response.manifest["status"] in {"pending_signoff", "needs_revision"}
    assert response.manifest["intake_status"] in {
        "ready_for_recommendation",
        "needs_clarification",
    }
    assert response.manifest["plan_quality_status"] != "not_provided"
    assert "VolunteerPlan JSON" not in response.artifacts["plan_quality_audit"]
    assert "delivery_bundle" in response.artifacts
    assert "服务交付包" in response.artifacts["delivery_bundle"]
    assert "expectation_packet" in response.artifacts
    assert "report_quality_audit" in response.artifacts


def test_delivery_portfolio_endpoint_aggregates_client_delivery_gates():
    from main import DeliveryPortfolioAuditRequest, audit_delivery_portfolio_api

    request = DeliveryPortfolioAuditRequest(
        manifests=[
            {
                "case_id": "portfolio-ready",
                "status": "ready_to_deliver",
                "intake_readiness_score": 0.90,
                "plan_quality_score": 0.86,
                "report_quality_score": 0.84,
                "client_delivery": {
                    "allowed": True,
                    "status": "allowed",
                    "blocked_reason": "",
                },
                "delivery_gates": [
                    {"gate": "intake_audit", "status": "ready_for_recommendation"},
                    {"gate": "plan_quality", "status": "pass"},
                    {"gate": "report_quality", "status": "pass"},
                ],
            },
            {
                "case_id": "portfolio-blocked",
                "status": "needs_revision",
                "intake_readiness_score": 0.72,
                "plan_quality_score": 0.55,
                "report_quality_score": 0.63,
                "client_delivery": {
                    "allowed": False,
                    "status": "blocked",
                    "blocked_reason": "客户确认包仅在内部质检通过后开放。",
                },
                "delivery_gates": [
                    {"gate": "intake_audit", "status": "ready_for_recommendation"},
                    {"gate": "plan_quality", "status": "needs_revision"},
                    {"gate": "report_quality", "status": "needs_revision"},
                ],
            },
        ]
    )

    response = asyncio.run(audit_delivery_portfolio_api(request))

    assert response.success is True
    assert response.audit["case_count"] == 2
    assert response.audit["client_delivery_allowed_rate"] == 0.5
    assert response.audit["client_delivery_status_counts"]["blocked"] == 1
    assert "Client Delivery Gate" in response.markdown


def test_stats_endpoint_uses_prediction_history_data():
    stats = asyncio.run(get_stats())

    assert stats["total_records"] > 0
    assert 2024 in stats["years"]
    assert stats["latest_year"] == 2024
