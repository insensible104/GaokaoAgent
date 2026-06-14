"""Smoke tests for the agency-facing delivery command center."""

from __future__ import annotations

from evaluation.agency_command_center import (
    build_agency_command_center,
    build_markdown_agency_command_center,
)


def test_agency_command_center_surfaces_portfolio_pain_points() -> None:
    manifests = [
        {
            "case_id": "ready-001",
            "status": "ready_to_deliver",
            "intake_readiness_score": 0.92,
            "plan_quality_score": 0.90,
            "report_quality_score": 0.88,
            "delivery_gates": [
                {"gate": "intake_audit", "status": "ready_for_recommendation"},
                {"gate": "plan_quality", "status": "pass"},
                {"gate": "report_quality", "status": "pass"},
            ],
            "next_actions": [],
        },
        {
            "case_id": "revision-001",
            "status": "needs_revision",
            "intake_readiness_score": 0.72,
            "plan_quality_score": 0.46,
            "report_quality_score": 0.64,
            "delivery_gates": [
                {"gate": "intake_audit", "status": "ready_for_recommendation"},
                {"gate": "plan_quality", "status": "needs_revision"},
                {"gate": "report_quality", "status": "needs_revision"},
            ],
            "next_actions": ["Repair plan quality before client delivery."],
        },
        {
            "case_id": "blocked-001",
            "status": "blocked",
            "intake_readiness_score": 0.24,
            "plan_quality_score": 0.0,
            "report_quality_score": 0.70,
            "delivery_gates": [
                {"gate": "intake_audit", "status": "blocked_missing_core"},
                {"gate": "plan_quality", "status": "not_provided"},
                {"gate": "report_quality", "status": "pass"},
            ],
            "next_actions": ["Collect missing score, rank, subject group, and preferences."],
        },
    ]

    result = build_agency_command_center(manifests)

    assert result["status"] == "blocked_for_scale"
    assert result["agency_positioning"] == "head_advisor_command_center"
    assert result["portfolio"]["case_count"] == 3
    assert result["north_star"]["ready_to_deliver_rate"] == result["portfolio"]["ready_to_deliver_rate"]
    assert result["north_star"]["blocked_rate"] == result["portfolio"]["blocked_rate"]
    assert result["pain_points"][0]["gate"] == "plan_quality"
    assert result["pain_points"][0]["affected_case_count"] == 2
    assert result["escalation_queue"][0]["case_id"] == "blocked-001"
    assert result["advisor_lead_brief"][0]["priority"] == "P0"
    assert result["advisor_playbook"][0]["gate"] == "plan_quality"
    assert result["advisor_playbook"][0]["handoff_stage"] == "pre_delivery_qa"
    assert len(result["advisor_playbook"][0]["intake_questions"]) >= 2
    assert any("plan" in item.lower() for item in result["advisor_playbook"][0]["acceptance_evidence"])
    assert result["advisor_playbook"][0]["manager_sop"][0]["owner"] == "advisor_lead"
    assert result["advisor_training_plan"]["status"] == "training_required"
    assert result["advisor_training_plan"]["modules"][0]["source_gate"] == "plan_quality"
    assert result["advisor_training_plan"]["modules"][0]["practice_drill"]
    assert result["advisor_training_plan"]["modules"][0]["qa_rubric"][0]["criterion"]
    assert result["advisor_training_plan"]["operating_cadence"][0]["cadence"] == "daily"
    assert "ready-to-deliver" in result["advisor_training_plan"]["pass_condition"]
    assert result["action_register"]["status"] == "active"
    assert result["action_register"]["items"][0]["owner"] == "advisor_lead"
    assert result["action_register"]["items"][0]["cadence"] == "daily"
    assert result["action_register"]["items"][0]["success_metric"]
    assert result["action_register"]["items"][0]["source"] in {"advisor_lead_brief", "advisor_training_plan"}
    assert result["executive_decision"]["decision"] == "hold_scale"
    assert result["executive_decision"]["priority"] == "P0"
    assert any("public quality claims" in item for item in result["executive_decision"]["blocked_claims"])
    assert result["executive_decision"]["review_cadence"] == "daily"
    assert result["executive_decision"]["required_evidence"]
    assert result["client_pain_radar"][0]["gate"] == "plan_quality"
    assert "滑档" in result["client_pain_radar"][0]["user_pain"]
    assert result["client_pain_radar"][0]["advisor_opening"]
    assert result["client_pain_radar"][0]["proof_to_show"][0]
    assert result["client_pain_radar"][0]["success_signal"]
    assert result["proof_gap_ledger"]["status"] == "evidence_required"
    assert result["proof_gap_ledger"]["items"][0]["gate"] == "plan_quality"
    assert result["proof_gap_ledger"]["items"][0]["owner"] == "qa_reviewer"
    assert "冲稳保分层表" in result["proof_gap_ledger"]["items"][0]["missing_proof"]
    assert result["proof_gap_ledger"]["items"][0]["client_risk"]
    assert result["proof_gap_ledger"]["items"][0]["evidence_standard"]
    assert result["proof_gap_ledger"]["items"][0]["unblocks_claims"]
    assert result["communication_guardrails"]["status"] == "restricted"
    assert result["communication_guardrails"]["cards"][0]["gate"] == "plan_quality"
    assert result["communication_guardrails"]["cards"][0]["approved_opening"]
    assert any("保证" in item for item in result["communication_guardrails"]["cards"][0]["must_disclose"])
    assert result["communication_guardrails"]["cards"][0]["forbidden_language"]
    assert result["communication_guardrails"]["cards"][0]["escalate_when"]
    assert result["communication_guardrails"]["cards"][0]["proof_before_claim"][0] == "冲稳保分层表"
    assert result["case_rescue_queue"]["status"] == "active"
    assert result["case_rescue_queue"]["items"][0]["case_id"] == "blocked-001"
    assert result["case_rescue_queue"]["items"][0]["priority"] == "P0"
    assert result["case_rescue_queue"]["items"][0]["owner"] == "advisor_lead"
    assert "plan_quality" in result["case_rescue_queue"]["items"][0]["failed_gates"]
    assert result["case_rescue_queue"]["items"][0]["rescue_steps"]
    assert result["case_rescue_queue"]["items"][0]["client_update_script"]
    assert result["case_rescue_queue"]["items"][0]["do_not_release_until"]
    assert result["institution_health_scorecard"]["overall_status"] == "critical_attention"
    assert result["institution_health_scorecard"]["dimensions"][0]["dimension"] == "delivery_reliability"
    assert result["institution_health_scorecard"]["dimensions"][0]["status"] == "red"
    assert result["institution_health_scorecard"]["dimensions"][0]["management_question"]
    assert any(
        item["dimension"] == "rescue_pressure" and item["status"] == "red"
        for item in result["institution_health_scorecard"]["dimensions"]
    )
    assert result["institution_health_scorecard"]["next_management_decision"]

    markdown = build_markdown_agency_command_center(result)
    assert "Agency Command Center" in markdown
    assert "Institution Health Scorecard" in markdown
    assert "Executive Decision Gate" in markdown
    assert "Client Pain Radar" in markdown
    assert "Proof Gap Ledger" in markdown
    assert "Advisor Communication Guardrails" in markdown
    assert "Case Rescue Queue" in markdown
    assert "User Pain Points" in markdown
    assert "Advisor Playbook" in markdown
    assert "Advisor Training Plan" in markdown
    assert "Action Register" in markdown
    assert "blocked-001" in markdown


def test_agency_command_center_keeps_empty_portfolio_neutral() -> None:
    result = build_agency_command_center([])

    assert result["status"] == "no_cases"
    assert result["north_star"]["case_count"] == 0
    assert result["advisor_lead_brief"][0]["priority"] == "P2"
    assert result["executive_decision"]["decision"] == "collect_evidence_before_scaling"
    assert result["executive_decision"]["priority"] == "P2"
    assert result["client_pain_radar"] == []
    assert result["proof_gap_ledger"]["status"] == "waiting_for_cases"
    assert result["communication_guardrails"]["status"] == "waiting_for_cases"
    assert result["case_rescue_queue"]["status"] == "waiting_for_cases"
    assert result["institution_health_scorecard"]["overall_status"] == "collect_cases_first"


if __name__ == "__main__":
    test_agency_command_center_surfaces_portfolio_pain_points()
    test_agency_command_center_keeps_empty_portfolio_neutral()
    print("agency command center smoke tests passed")
