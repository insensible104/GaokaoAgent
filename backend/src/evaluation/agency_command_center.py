"""Agency-level command center for delivery portfolio operations."""

from __future__ import annotations

from typing import Any, Iterable

from evaluation.delivery_portfolio import audit_delivery_portfolio


PROTOCOL_VERSION = "gaokao-agency-command-center-v1"

GATE_PAIN_LABELS = {
    "intake_audit": "Intake is not decision-ready.",
    "plan_quality": "Volunteer plan quality blocks trusted delivery.",
    "expectation_packet": "Client expectation boundaries are not signed off.",
    "report_quality": "Final report evidence or wording is not delivery-safe.",
}

GATE_OPERATOR_RESPONSES = {
    "intake_audit": "Run a structured intake repair before any school list discussion.",
    "plan_quality": "Freeze the recommendation and repair plan structure before client handoff.",
    "expectation_packet": "Ask the family to confirm constraints, tradeoffs, and non-guarantee boundaries.",
    "report_quality": "Rewrite the report around evidence, uncertainty, and actionable tradeoffs.",
}

PLAYBOOK_TEMPLATES = {
    "intake_audit": {
        "handoff_stage": "pre_analysis_intake",
        "intake_questions": [
            "What score, rank, subject group, city constraints, and major boundaries are confirmed by the family?",
            "Which constraints are hard exclusions versus preferences that can be traded off?",
            "What medical, tuition, distance, or family-pressure constraints could invalidate a recommendation later?",
        ],
        "client_language": "We need to complete the decision facts before discussing schools; otherwise the list may optimize the wrong target.",
        "acceptance_evidence": [
            "Completed profile with score, rank, subject group, city preference, major preference, and exclusions.",
            "Documented hard constraints and soft preferences signed off before recommendation generation.",
        ],
    },
    "plan_quality": {
        "handoff_stage": "pre_delivery_qa",
        "intake_questions": [
            "Does the plan contain a clear rush/stable/safe structure with enough safe-tail capacity?",
            "Which rows are there because of evidence, and which rows are unresolved advisor judgment calls?",
            "What is the fallback if the top-choice major group slides or forces an unwanted adjustment?",
        ],
        "client_language": "We will not hand off a school list until the plan structure, safe-tail boundary, and adjustment risk are auditable.",
        "acceptance_evidence": [
            "Frozen volunteer plan JSON or table reviewed by the plan-quality gate.",
            "Plan-level evidence for rush/stable/safe balance, safe-tail coverage, and adjustment-risk handling.",
        ],
    },
    "expectation_packet": {
        "handoff_stage": "family_signoff",
        "intake_questions": [
            "Which risk boundaries must the family explicitly accept before delivery?",
            "What outcome would the family later regard as unacceptable even if admission succeeds?",
            "Which recommendation claims must be phrased as probabilities or tradeoffs rather than promises?",
        ],
        "client_language": "The recommendation is a decision aid, not an admission guarantee; the family needs to confirm the tradeoff boundary.",
        "acceptance_evidence": [
            "Expectation packet signed off with non-guarantee language.",
            "Confirmed risk boundaries and unacceptable outcomes recorded before final delivery.",
        ],
    },
    "report_quality": {
        "handoff_stage": "final_report_review",
        "intake_questions": [
            "Does every important recommendation explain the evidence and uncertainty behind it?",
            "Does the report state what the student should do next rather than only listing schools?",
            "Are policy, admission, and adjustment-risk caveats visible enough for family review?",
        ],
        "client_language": "The final report should make tradeoffs inspectable, so the family understands why each decision is being made.",
        "acceptance_evidence": [
            "Report-quality audit passes evidence, uncertainty, and actionability checks.",
            "Final report includes caveats, decision rationale, and next actions for the family.",
        ],
    },
}

CLIENT_PAIN_TEMPLATES = {
    "intake_audit": {
        "user_symptom": "家长反复补材料，感觉顾问迟迟不给明确学校名单。",
        "user_pain": "核心画像不完整会让推荐像猜测，后面任何新增限制都可能推翻方案。",
        "advisor_opening": "我们先把分数、位次、选科、城市、专业禁区和家庭硬约束定下来，再进入学校讨论。",
        "proof_to_show": [
            "学生画像确认单",
            "硬约束与可让步偏好分层表",
            "缺失信息补齐记录",
        ],
        "success_signal": "家长能确认哪些条件绝不妥协，顾问再生成方案。",
        "risk_if_ignored": "方案看似很快，但后续会被城市、专业、体检或家庭压力反复推翻。",
    },
    "plan_quality": {
        "user_symptom": "家长拿到学校名单，却看不懂冲稳保、兜底和调剂风险。",
        "user_pain": "用户真正怕的是滑档、浪费分数，或者被调剂到不能接受的专业。",
        "advisor_opening": "我们先把冲稳保结构、保底容量和专业调剂风险讲清楚，再讨论每一所学校是否值得放入。",
        "proof_to_show": [
            "冲稳保分层表",
            "安全尾部容量说明",
            "调剂风险与替代方案记录",
        ],
        "success_signal": "家长能说清楚为什么这些学校分别承担冲、稳、保角色。",
        "risk_if_ignored": "名单像堆学校，家长会在临近填报时重新质疑全部推荐。",
    },
    "expectation_packet": {
        "user_symptom": "家长把推荐理解成承诺，后续对风险边界没有心理准备。",
        "user_pain": "用户怕花了钱却没人说明失败概率、调剂后果和不可控因素。",
        "advisor_opening": "我们会把能判断的概率和不能承诺的边界写清楚，避免把决策辅助说成录取保证。",
        "proof_to_show": [
            "预期确认单",
            "非保证声明",
            "不可接受结果清单",
        ],
        "success_signal": "家长能复述推荐的收益、风险和不可承诺边界。",
        "risk_if_ignored": "交付时满意，结果波动后会变成信任和售后风险。",
    },
    "report_quality": {
        "user_symptom": "报告看起来完整，但家长不知道下一步该怎么决策。",
        "user_pain": "用户不只要学校列表，还要知道依据、取舍、风险和执行顺序。",
        "advisor_opening": "报告会把每个关键建议背后的依据、风险和下一步动作写出来，方便家庭一起决策。",
        "proof_to_show": [
            "建议依据与不确定性说明",
            "家庭决策清单",
            "最终报告质检记录",
        ],
        "success_signal": "家长能根据报告完成下一步确认，而不是只截图问哪所学校最好。",
        "risk_if_ignored": "报告像资料汇编，不能降低家长焦虑，也难以体现机构专业度。",
    },
}


def _priority_for_pain_point(failed_rate: float) -> str:
    if failed_rate >= 0.50:
        return "P0"
    if failed_rate >= 0.20:
        return "P1"
    return "P2"


def _status(portfolio: dict[str, Any]) -> str:
    status = str(portfolio.get("status") or "no_cases")
    if status == "no_cases":
        return status
    if status in {"blocked_for_scale", "needs_operational_iteration"}:
        return status
    if float(portfolio.get("ready_to_deliver_rate", 0.0) or 0.0) < 0.80:
        return "needs_targeted_iteration"
    return "on_track"


def _pain_points(portfolio: dict[str, Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    case_count = int(portfolio.get("case_count", 0) or 0)
    for item in portfolio.get("top_failed_gates", []) or []:
        gate = str(item.get("gate") or "unknown")
        failed_rate = float(item.get("failed_rate", 0.0) or 0.0)
        points.append(
            {
                "priority": _priority_for_pain_point(failed_rate),
                "gate": gate,
                "pain_point": GATE_PAIN_LABELS.get(gate, f"{gate} repeatedly fails delivery review."),
                "affected_case_count": int(item.get("failed_count", 0) or 0),
                "affected_rate": failed_rate,
                "operator_response": GATE_OPERATOR_RESPONSES.get(
                    gate,
                    "Turn this repeated failure into a standard repair checklist.",
                ),
            }
        )
    if not points and case_count > 0:
        points.append(
            {
                "priority": "P2",
                "gate": "none",
                "pain_point": "No repeated failed delivery gate is visible yet.",
                "affected_case_count": 0,
                "affected_rate": 0.0,
                "operator_response": "Keep collecting cases and monitor the next delivery portfolio audit.",
            }
        )
    return points


def _client_pain_radar(pain_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    radar: list[dict[str, Any]] = []
    for point in pain_points:
        gate = str(point.get("gate") or "unknown")
        if gate == "none":
            continue
        template = CLIENT_PAIN_TEMPLATES.get(
            gate,
            {
                "user_symptom": "用户能感受到交付反复，但说不清问题出在哪个环节。",
                "user_pain": "反复返工会消耗信任，让家庭担心机构只是在补救而不是掌控全局。",
                "advisor_opening": "我们先定位这个环节的证据缺口，再决定是否可以继续交付。",
                "proof_to_show": [
                    "失败门槛复盘记录",
                    "修复动作与负责人",
                    "复检通过证据",
                ],
                "success_signal": "家长能理解为什么需要暂停或补证据，并接受下一步安排。",
                "risk_if_ignored": "内部问题会在客户沟通中暴露，形成更高的解释成本。",
            },
        )
        radar.append(
            {
                "priority": point.get("priority", "P2"),
                "gate": gate,
                "affected_case_count": point.get("affected_case_count", 0),
                "affected_rate": point.get("affected_rate", 0.0),
                "user_symptom": template["user_symptom"],
                "user_pain": template["user_pain"],
                "advisor_opening": template["advisor_opening"],
                "proof_to_show": list(template["proof_to_show"]),
                "success_signal": template["success_signal"],
                "risk_if_ignored": template["risk_if_ignored"],
                "source_pain_point": point.get("pain_point", ""),
            }
        )
    return radar


def _proof_gap_owner(gate: str) -> str:
    return {
        "intake_audit": "case_advisor",
        "plan_quality": "qa_reviewer",
        "expectation_packet": "advisor_lead",
        "report_quality": "qa_reviewer",
    }.get(gate, "advisor_lead")


def _proof_gap_ledger(
    portfolio: dict[str, Any],
    client_pain_radar: list[dict[str, Any]],
    executive_decision: dict[str, Any],
) -> dict[str, Any]:
    if int(portfolio.get("case_count", 0) or 0) == 0:
        return {
            "status": "waiting_for_cases",
            "item_count": 0,
            "items": [],
            "ledger_standard": "只有 reviewed delivery cases 暴露出重复用户痛点后，才分配证据缺口。",
        }

    items: list[dict[str, Any]] = []
    review_cadence = str(executive_decision.get("review_cadence") or "weekly")
    blocked_claims = list(executive_decision.get("blocked_claims", []) or [])
    unblocks_claims = blocked_claims[:2] or ["Internal advisor quality claim can be considered after proof is complete."]
    for index, card in enumerate(client_pain_radar, 1):
        gate = str(card.get("gate") or "unknown")
        priority = str(card.get("priority") or "P2")
        missing_proof = list(card.get("proof_to_show", []) or [])
        if not missing_proof:
            missing_proof = ["Gate-specific repair evidence"]
        items.append(
            {
                "gap_id": f"proof-{index}-{gate}",
                "priority": priority,
                "gate": gate,
                "owner": _proof_gap_owner(gate),
                "review_cadence": review_cadence if priority in {"P0", "P1"} else "weekly",
                "missing_proof": missing_proof,
                "client_risk": card.get("user_pain", ""),
                "why_it_matters": card.get("risk_if_ignored", ""),
                "evidence_standard": (
                    "补齐证据物，复跑来源交付门槛，并确认顾问能用客户安全语言解释风险边界。"
                ),
                "success_signal": card.get("success_signal", ""),
                "unblocks_claims": unblocks_claims,
            }
        )

    return {
        "status": "evidence_required" if items else "monitor_only",
        "item_count": len(items),
        "items": sorted(
            items,
            key=lambda item: (
                _priority_rank(str(item.get("priority", ""))),
                str(item.get("gate", "")),
                str(item.get("gap_id", "")),
            ),
        ),
        "ledger_standard": (
            "每个高频用户痛点都必须绑定具体证据物、负责人和复盘节奏，才可以支撑机构级质量表达。"
        ),
    }


def _communication_guardrails(
    portfolio: dict[str, Any],
    client_pain_radar: list[dict[str, Any]],
    proof_gap_ledger: dict[str, Any],
    executive_decision: dict[str, Any],
) -> dict[str, Any]:
    if int(portfolio.get("case_count", 0) or 0) == 0:
        return {
            "status": "waiting_for_cases",
            "cards": [],
            "guardrail_standard": "先收集 reviewed delivery cases，再沉淀顾问沟通护栏。",
        }

    proof_by_gate = {
        str(item.get("gate") or "unknown"): item
        for item in proof_gap_ledger.get("items", []) or []
    }
    blocked_claims = list(executive_decision.get("blocked_claims", []) or [])
    cards: list[dict[str, Any]] = []
    for card in client_pain_radar:
        gate = str(card.get("gate") or "unknown")
        proof_item = proof_by_gate.get(gate, {})
        priority = str(card.get("priority") or "P2")
        cards.append(
            {
                "priority": priority,
                "gate": gate,
                "approved_opening": card.get("advisor_opening", ""),
                "must_disclose": [
                    "当前方案是决策辅助，不保证录取结果。",
                    "必须同步冲稳保结构、调剂风险和家庭不可接受结果。",
                    "证据未补齐前，只能说正在内部复核，不能包装成成熟质量结论。",
                ],
                "forbidden_language": [
                    "这个方案保证不滑档。",
                    "我们可以保证录取到理想专业。",
                    "不用看调剂风险，照着填就行。",
                    *blocked_claims[:2],
                ],
                "proof_before_claim": list(
                    proof_item.get("missing_proof")
                    or card.get("proof_to_show")
                    or []
                ),
                "escalate_when": [
                    "家长要求录取保证或结果承诺。",
                    "家庭拒绝确认风险边界或不可接受结果。",
                    "证据物缺失但顾问准备进入客户交付。",
                ],
                "safe_close": card.get(
                    "success_signal",
                    "家长能复述关键风险和下一步动作后，再进入下一阶段。",
                ),
            }
        )

    return {
        "status": (
            "restricted"
            if str(executive_decision.get("priority") or "P2") in {"P0", "P1"}
            else "active"
        ),
        "cards": sorted(
            cards,
            key=lambda item: (
                _priority_rank(str(item.get("priority", ""))),
                str(item.get("gate", "")),
            ),
        ),
        "guardrail_standard": (
            "顾问只能使用已批准开场、必须披露风险边界，并在证据补齐前禁止保证式表达。"
        ),
    }


def _rescue_owner(failed_gates: list[str]) -> str:
    if "intake_audit" in failed_gates:
        return "advisor_lead"
    if "plan_quality" in failed_gates:
        return "qa_reviewer"
    if "expectation_packet" in failed_gates:
        return "advisor_lead"
    if "report_quality" in failed_gates:
        return "qa_reviewer"
    return "advisor_lead"


def _case_rescue_queue(portfolio: dict[str, Any]) -> dict[str, Any]:
    if int(portfolio.get("case_count", 0) or 0) == 0:
        return {
            "status": "waiting_for_cases",
            "item_count": 0,
            "items": [],
            "queue_standard": "先收集 reviewed delivery cases，再建立个案救援队列。",
        }

    items: list[dict[str, Any]] = []
    for index, case in enumerate(portfolio.get("worst_cases", [])[:8], 1):
        failed_gates = [
            str(gate.get("gate") or "unknown")
            for gate in case.get("failed_gates", []) or []
        ]
        status = str(case.get("status") or "unknown")
        if status == "ready_to_deliver" and not failed_gates:
            continue
        priority = "P0" if status == "blocked" else "P1" if failed_gates else "P2"
        owner = _rescue_owner(failed_gates)
        gate_steps = [
            GATE_OPERATOR_RESPONSES.get(
                gate,
                "Turn the failed gate into a repair checklist and rerun review.",
            )
            for gate in failed_gates
        ]
        if not gate_steps:
            gate_steps = ["Review the case score, failed status, and missing delivery evidence before release."]
        items.append(
            {
                "rescue_id": f"rescue-{index}-{case.get('case_id', 'unknown')}",
                "priority": priority,
                "case_id": case.get("case_id", ""),
                "status": status,
                "portfolio_score": case.get("portfolio_score", 0.0),
                "failed_gates": failed_gates,
                "owner": owner,
                "cadence": "daily" if priority == "P0" else "twice_weekly",
                "rescue_steps": [
                    *gate_steps[:3],
                    "Attach repaired evidence and rerun delivery review before client handoff.",
                ],
                "client_update_script": (
                    "这份方案还在内部复核，我们会先补齐关键证据和风险边界，"
                    "再把可交付版本同步给您。"
                ),
                "do_not_release_until": [
                    "All failed gates have a repair owner and evidence.",
                    "The case no longer has blocked delivery status.",
                    "Advisor lead confirms client-safe language before handoff.",
                ],
                "escalation_reason": (
                    "Blocked case needs same-day owner review."
                    if priority == "P0"
                    else "Failed gate needs targeted repair before delivery."
                ),
            }
        )

    return {
        "status": "active" if items else "monitor_only",
        "item_count": len(items),
        "items": sorted(
            items,
            key=lambda item: (
                _priority_rank(str(item.get("priority", ""))),
                float(item.get("portfolio_score", 0.0) or 0.0),
                str(item.get("case_id", "")),
            ),
        ),
        "queue_standard": (
            "每个阻塞或低质交付个案都必须有负责人、救援步骤、客户同步话术和禁止交付条件。"
        ),
    }


def _dimension_status(score: int) -> str:
    if score < 50:
        return "red"
    if score < 80:
        return "yellow"
    return "green"


def _institution_health_scorecard(
    portfolio: dict[str, Any],
    proof_gap_ledger: dict[str, Any],
    communication_guardrails: dict[str, Any],
    advisor_training_plan: dict[str, Any],
    case_rescue_queue: dict[str, Any],
) -> dict[str, Any]:
    case_count = int(portfolio.get("case_count", 0) or 0)
    if case_count == 0:
        return {
            "overall_status": "collect_cases_first",
            "dimensions": [],
            "next_management_decision": "先收集 reviewed delivery bundles，再判断机构级经营健康度。",
            "scorecard_standard": "经营体检卡只基于已审阅交付案源生成，避免用空样本包装成熟度。",
        }

    ready_rate = float(portfolio.get("ready_to_deliver_rate", 0.0) or 0.0)
    blocked_rate = float(portfolio.get("blocked_rate", 0.0) or 0.0)
    proof_gap_count = int(proof_gap_ledger.get("item_count", 0) or 0)
    rescue_count = int(case_rescue_queue.get("item_count", 0) or 0)
    training_module_count = len(advisor_training_plan.get("modules", []) or [])
    restricted_comms = str(communication_guardrails.get("status") or "") == "restricted"

    reliability_score = max(0, min(100, round(ready_rate * 100 - blocked_rate * 80)))
    evidence_score = max(0, 100 - proof_gap_count * 25)
    trust_score = 45 if restricted_comms else 85
    team_score = max(30, 90 - training_module_count * 15)
    rescue_score = max(0, 100 - rescue_count * 35)

    dimensions = [
        {
            "dimension": "delivery_reliability",
            "label": "交付可靠性",
            "score": reliability_score,
            "status": _dimension_status(reliability_score),
            "signal": f"Ready-to-deliver {ready_rate:.1%}, blocked {blocked_rate:.1%}.",
            "management_question": "是否应该暂停放大，先降低阻塞率？",
            "next_action": "优先处理 P0 阻塞个案，并复跑交付门槛。",
        },
        {
            "dimension": "evidence_readiness",
            "label": "证据准备度",
            "score": evidence_score,
            "status": _dimension_status(evidence_score),
            "signal": f"{proof_gap_count} proof gaps remain.",
            "management_question": "哪些质量表达还缺证据物支撑？",
            "next_action": "按证据缺口台账补齐证明材料。",
        },
        {
            "dimension": "client_trust_risk",
            "label": "客户信任风险",
            "score": trust_score,
            "status": _dimension_status(trust_score),
            "signal": str(communication_guardrails.get("status") or "unknown"),
            "management_question": "顾问是否仍可能说出保证式承诺？",
            "next_action": "执行顾问沟通护栏，并抽查客户同步话术。",
        },
        {
            "dimension": "team_training_load",
            "label": "团队训练负荷",
            "score": team_score,
            "status": _dimension_status(team_score),
            "signal": f"{training_module_count} training modules required.",
            "management_question": "哪些失败门槛要进入本周训练？",
            "next_action": "把高频失败门槛转成顾问训练和 QA 抽检。",
        },
        {
            "dimension": "rescue_pressure",
            "label": "个案救援压力",
            "score": rescue_score,
            "status": _dimension_status(rescue_score),
            "signal": f"{rescue_count} cases need rescue.",
            "management_question": "哪些个案今天不能继续交付？",
            "next_action": "按个案救援队列分配负责人和客户同步。",
        },
    ]
    if any(item["status"] == "red" for item in dimensions):
        overall_status = "critical_attention"
    elif any(item["status"] == "yellow" for item in dimensions):
        overall_status = "needs_management_review"
    else:
        overall_status = "healthy_with_monitoring"

    weakest = min(dimensions, key=lambda item: int(item["score"]))
    return {
        "overall_status": overall_status,
        "dimensions": dimensions,
        "next_management_decision": f"先处理{weakest['label']}：{weakest['next_action']}",
        "scorecard_standard": "经营体检卡用于主管一屏判断，所有红色维度都必须绑定到行动台账或救援队列。",
    }


def _advisor_lead_brief(portfolio: dict[str, Any], pain_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    brief: list[dict[str, Any]] = []
    if int(portfolio.get("case_count", 0) or 0) == 0:
        return [
            {
                "priority": "P2",
                "focus": "Start collecting delivery bundles before drawing agency-level conclusions.",
                "why": "No reviewed delivery cases are available yet.",
            }
        ]
    blocked_rate = float(portfolio.get("blocked_rate", 0.0) or 0.0)
    ready_rate = float(portfolio.get("ready_to_deliver_rate", 0.0) or 0.0)
    if blocked_rate >= 0.10:
        brief.append(
            {
                "priority": "P0",
                "focus": "Stop scaling client delivery until blocked cases are triaged.",
                "why": f"Blocked delivery rate is {blocked_rate:.1%}.",
            }
        )
    if ready_rate < 0.80:
        brief.append(
            {
                "priority": "P1",
                "focus": "Raise ready-to-deliver share before making public quality claims.",
                "why": f"Ready-to-deliver rate is {ready_rate:.1%}.",
            }
        )
    for point in pain_points[:3]:
        if point["priority"] in {"P0", "P1"}:
            brief.append(
                {
                    "priority": point["priority"],
                    "focus": point["operator_response"],
                    "why": (
                        f"{point['pain_point']} "
                        f"Affected rate: {float(point['affected_rate']):.1%}."
                    ),
                }
            )
    if not brief:
        brief.append(
            {
                "priority": "P2",
                "focus": "Continue weekly portfolio review and expand benchmarked delivery cases.",
                "why": "No urgent scale blocker is visible in the current delivery portfolio.",
            }
        )
    return brief


def _advisor_playbook(pain_points: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for point in pain_points:
        gate = str(point.get("gate") or "unknown")
        if gate == "none":
            continue
        template = PLAYBOOK_TEMPLATES.get(
            gate,
            {
                "handoff_stage": "delivery_review",
                "intake_questions": [
                    "What repeated case pattern caused this gate to fail?",
                    "Which evidence must be collected before this case can advance?",
                ],
                "client_language": "This case needs one more internal review before client handoff.",
                "acceptance_evidence": [
                    "Gate-specific repair evidence attached to the delivery bundle.",
                ],
            },
        )
        cards.append(
            {
                "priority": point.get("priority", "P2"),
                "gate": gate,
                "handoff_stage": template["handoff_stage"],
                "trigger": point.get("pain_point", ""),
                "affected_case_count": point.get("affected_case_count", 0),
                "affected_rate": point.get("affected_rate", 0.0),
                "manager_sop": [
                    {
                        "owner": "advisor_lead",
                        "step": point.get("operator_response", ""),
                    },
                    {
                        "owner": "case_advisor",
                        "step": "Apply the intake questions and attach acceptance evidence before release.",
                    },
                    {
                        "owner": "qa_reviewer",
                        "step": "Confirm the repaired bundle passes the relevant delivery gate.",
                    },
                ],
                "intake_questions": list(template["intake_questions"]),
                "client_language": template["client_language"],
                "acceptance_evidence": list(template["acceptance_evidence"]),
            }
        )
    return cards


def _advisor_training_plan(
    portfolio: dict[str, Any],
    advisor_playbook: list[dict[str, Any]],
) -> dict[str, Any]:
    case_count = int(portfolio.get("case_count", 0) or 0)
    if case_count == 0:
        return {
            "status": "collect_cases_first",
            "modules": [],
            "operating_cadence": [
                {
                    "cadence": "weekly",
                    "owner": "advisor_lead",
                    "action": "Review whether enough delivery bundles exist to start team-level training.",
                }
            ],
            "pass_condition": "Collect at least one reviewed delivery bundle before judging advisor training needs.",
        }

    modules: list[dict[str, Any]] = []
    for card in advisor_playbook:
        modules.append(
            {
                "module_id": f"{card.get('gate', 'unknown')}-repair",
                "priority": card.get("priority", "P2"),
                "source_gate": card.get("gate", "unknown"),
                "title": f"Repair {card.get('gate', 'delivery')} failures before handoff",
                "learning_objective": card.get("trigger", ""),
                "practice_drill": (
                    "Take one blocked or revision case, ask the listed intake questions, "
                    "attach acceptance evidence, and rerun the delivery gate."
                ),
                "qa_rubric": [
                    {
                        "criterion": "Evidence completeness",
                        "standard": "Required acceptance evidence is attached before the case advances.",
                    },
                    {
                        "criterion": "Client-safe language",
                        "standard": "Advisor wording explains tradeoffs and avoids guarantee-like claims.",
                    },
                    {
                        "criterion": "Gate repair",
                        "standard": "The repaired bundle no longer fails the source gate.",
                    },
                ],
            }
        )

    status = "training_required" if modules else "monitor_only"
    return {
        "status": status,
        "modules": modules,
        "operating_cadence": [
            {
                "cadence": "daily",
                "owner": "advisor_lead",
                "action": "Triage P0/P1 blocked cases and assign the matching playbook module.",
            },
            {
                "cadence": "weekly",
                "owner": "qa_reviewer",
                "action": "Sample repaired bundles and update the playbook if a gate keeps failing.",
            },
            {
                "cadence": "monthly",
                "owner": "institution_operator",
                "action": "Compare ready-to-deliver and blocked rates before changing public quality claims.",
            },
        ],
        "pass_condition": (
            "Training is effective when ready-to-deliver rate rises, blocked rate falls, "
            "and repaired cases pass the relevant delivery gates."
        ),
    }


def _priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(str(priority), 9)


def _action_register(
    *,
    advisor_lead_brief: list[dict[str, Any]],
    advisor_training_plan: dict[str, Any],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for index, brief in enumerate(advisor_lead_brief, 1):
        priority = str(brief.get("priority") or "P2")
        cadence = "daily" if priority in {"P0", "P1"} else "weekly"
        items.append(
            {
                "action_id": f"brief-{index}",
                "priority": priority,
                "source": "advisor_lead_brief",
                "owner": "advisor_lead",
                "cadence": cadence,
                "action": brief.get("focus", ""),
                "why": brief.get("why", ""),
                "success_metric": (
                    "Blocked cases triaged and assigned before client delivery."
                    if priority == "P0"
                    else "Ready-to-deliver rate improves or the blocker is converted into a playbook module."
                ),
            }
        )

    for module in advisor_training_plan.get("modules", []) or []:
        priority = str(module.get("priority") or "P2")
        items.append(
            {
                "action_id": f"training-{module.get('module_id', 'unknown')}",
                "priority": priority,
                "source": "advisor_training_plan",
                "owner": "qa_reviewer",
                "cadence": "weekly",
                "action": module.get("practice_drill", ""),
                "why": module.get("learning_objective", ""),
                "success_metric": "Sampled repaired bundles pass the module QA rubric.",
            }
        )

    items = sorted(
        items,
        key=lambda item: (
            _priority_rank(str(item.get("priority", ""))),
            str(item.get("source", "")),
            str(item.get("action_id", "")),
        ),
    )
    return {
        "status": "active" if items else "waiting_for_cases",
        "item_count": len(items),
        "items": items,
        "register_standard": (
            "Every repeated agency-level blocker should map to an owner, cadence, "
            "and success metric before it becomes a management claim."
        ),
    }


def _executive_decision(
    portfolio: dict[str, Any],
    pain_points: list[dict[str, Any]],
) -> dict[str, Any]:
    case_count = int(portfolio.get("case_count", 0) or 0)
    ready_rate = float(portfolio.get("ready_to_deliver_rate", 0.0) or 0.0)
    blocked_rate = float(portfolio.get("blocked_rate", 0.0) or 0.0)
    primary_pain = pain_points[0] if pain_points else {}
    primary_gate = str(primary_pain.get("gate") or "none")

    if case_count == 0:
        return {
            "decision": "collect_evidence_before_scaling",
            "priority": "P2",
            "summary": "No reviewed delivery cases exist yet, so the agency should collect evidence before making scale or quality claims.",
            "allowed_claims": [
                "Internal pilot is collecting reviewed delivery bundles.",
                "Advisor workflow is being audited before public quality positioning.",
            ],
            "blocked_claims": [
                "No public quality claims before at least one reviewed delivery bundle exists.",
                "No case outcome claims or admission-risk comparisons without audited cases.",
            ],
            "required_evidence": [
                "At least one reviewed delivery bundle with intake, plan, expectation, and report gates.",
                "A repeatable case-review cadence owned by the advisor lead.",
            ],
            "review_cadence": "weekly",
        }

    if blocked_rate >= 0.10:
        return {
            "decision": "hold_scale",
            "priority": "P0",
            "summary": (
                f"Blocked delivery rate is {blocked_rate:.1%}; pause scale claims until blocked cases "
                "are triaged and the main failure gate is repaired."
            ),
            "allowed_claims": [
                "Internal delivery repair is underway.",
                "The advisor team is triaging blocked cases before client handoff.",
            ],
            "blocked_claims": [
                "No public quality claims until blocked rate falls below 10%.",
                "No head-agency positioning or scale promise while blocked cases remain untriaged.",
                "No admission guarantee or outcome certainty claims.",
            ],
            "required_evidence": [
                "Every blocked case has an owner, next action, and repaired delivery gate.",
                f"The top failed gate `{primary_gate}` has a playbook and sampled repaired cases.",
                "Blocked rate is below 10% in the next portfolio audit.",
            ],
            "review_cadence": "daily",
        }

    if ready_rate < 0.80:
        return {
            "decision": "targeted_iteration",
            "priority": "P1",
            "summary": (
                f"Ready-to-deliver rate is {ready_rate:.1%}; keep the agency in targeted iteration "
                "before making broad quality claims."
            ),
            "allowed_claims": [
                "The agency has an audited delivery workflow under active improvement.",
                "Known delivery blockers are being converted into advisor SOP and QA training.",
            ],
            "blocked_claims": [
                "No broad public quality claims until ready-to-deliver rate reaches 80%.",
                "No claim that the process is mature across all advisor teams.",
                "No admission guarantee or outcome certainty claims.",
            ],
            "required_evidence": [
                "Ready-to-deliver rate reaches at least 80% across reviewed cases.",
                f"The top failed gate `{primary_gate}` shows fewer repeat failures after training.",
                "Advisor lead signs off on repaired bundles before client delivery.",
            ],
            "review_cadence": "twice_weekly",
        }

    return {
        "decision": "scale_with_monitoring",
        "priority": "P2",
        "summary": "Current portfolio quality is scale-ready, but claims should stay tied to audited process evidence.",
        "allowed_claims": [
            "The agency runs an audited delivery workflow for reviewed cases.",
            "Advisor QA monitors intake, plan quality, expectation boundaries, and report safety.",
        ],
        "blocked_claims": [
            "No admission guarantee or outcome certainty claims.",
            "No claim that unaudited cases meet the same quality bar.",
        ],
        "required_evidence": [
            "Weekly portfolio audit remains above 80% ready-to-deliver rate.",
            "Blocked rate stays below 10% with no unresolved P0 gate failures.",
            "Sampled cases preserve evidence-backed, non-guarantee client language.",
        ],
        "review_cadence": "weekly",
    }


def build_agency_command_center(manifests: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Build an agency-facing overview from delivery-bundle manifests."""
    portfolio = audit_delivery_portfolio(manifests)
    pain_points = _pain_points(portfolio)
    executive_decision = _executive_decision(portfolio, pain_points)
    client_pain_radar = _client_pain_radar(pain_points)
    proof_gap_ledger = _proof_gap_ledger(portfolio, client_pain_radar, executive_decision)
    communication_guardrails = _communication_guardrails(
        portfolio,
        client_pain_radar,
        proof_gap_ledger,
        executive_decision,
    )
    case_rescue_queue = _case_rescue_queue(portfolio)
    advisor_lead_brief = _advisor_lead_brief(portfolio, pain_points)
    advisor_playbook = _advisor_playbook(pain_points)
    advisor_training_plan = _advisor_training_plan(portfolio, advisor_playbook)
    institution_health_scorecard = _institution_health_scorecard(
        portfolio,
        proof_gap_ledger,
        communication_guardrails,
        advisor_training_plan,
        case_rescue_queue,
    )
    action_register = _action_register(
        advisor_lead_brief=advisor_lead_brief,
        advisor_training_plan=advisor_training_plan,
    )
    return {
        "protocol_version": PROTOCOL_VERSION,
        "agency_positioning": "head_advisor_command_center",
        "status": _status(portfolio),
        "north_star": {
            "case_count": portfolio.get("case_count", 0),
            "ready_to_deliver_rate": portfolio.get("ready_to_deliver_rate", 0.0),
            "blocked_rate": portfolio.get("blocked_rate", 0.0),
            "average_scores": portfolio.get("average_scores", {}),
        },
        "pain_points": pain_points,
        "executive_decision": executive_decision,
        "client_pain_radar": client_pain_radar,
        "proof_gap_ledger": proof_gap_ledger,
        "communication_guardrails": communication_guardrails,
        "case_rescue_queue": case_rescue_queue,
        "institution_health_scorecard": institution_health_scorecard,
        "advisor_lead_brief": advisor_lead_brief,
        "advisor_playbook": advisor_playbook,
        "advisor_training_plan": advisor_training_plan,
        "action_register": action_register,
        "escalation_queue": portfolio.get("worst_cases", [])[:8],
        "repeated_next_actions": portfolio.get("top_next_actions", [])[:8],
        "portfolio": portfolio,
        "notes": [
            "This command center is for internal advisor operations, not a client-facing guarantee.",
            "Repeated pain points should become intake scripts, QA gates, or training materials.",
        ],
    }


def build_markdown_agency_command_center(result: dict[str, Any]) -> str:
    """Render the agency command center as Markdown."""
    north_star = result.get("north_star", {}) or {}
    lines = [
        "# Agency Command Center",
        "",
        f"Status: `{result.get('status', 'unknown')}`",
        f"Cases: {north_star.get('case_count', 0)}",
        f"Ready-to-deliver rate: {float(north_star.get('ready_to_deliver_rate', 0.0)):.1%}",
        f"Blocked rate: {float(north_star.get('blocked_rate', 0.0)):.1%}",
        "",
    ]

    scorecard = result.get("institution_health_scorecard", {}) or {}
    lines.extend(
        [
            "## Institution Health Scorecard",
            "",
            f"Overall status: `{scorecard.get('overall_status', 'unknown')}`",
            "",
            str(scorecard.get("scorecard_standard", "")),
            "",
            "| Status | Dimension | Score | Signal | Management Question | Next Action |",
            "| --- | --- | ---: | --- | --- | --- |",
        ]
    )
    if scorecard.get("dimensions"):
        for item in scorecard["dimensions"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{item.get('status', '')}`",
                        str(item.get("label", item.get("dimension", ""))).replace("|", "/"),
                        str(item.get("score", "")),
                        str(item.get("signal", "")).replace("|", "/"),
                        str(item.get("management_question", "")).replace("|", "/"),
                        str(item.get("next_action", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `yellow` | Collect cases | 0 | No reviewed cases. | Do we have enough delivery bundles? | Collect reviewed delivery bundles. |")
    if scorecard.get("next_management_decision"):
        lines.extend(["", f"Next decision: {scorecard['next_management_decision']}", ""])
    else:
        lines.append("")

    decision = result.get("executive_decision", {}) or {}
    lines.extend(
        [
            "## Executive Decision Gate",
            "",
            f"Decision: `{decision.get('decision', 'unknown')}`",
            f"Priority: `{decision.get('priority', 'P2')}`",
            f"Review cadence: `{decision.get('review_cadence', 'weekly')}`",
            "",
            str(decision.get("summary", "")),
            "",
            "| Allowed Claims | Blocked Claims | Required Evidence |",
            "| --- | --- | --- |",
        ]
    )
    max_rows = max(
        len(decision.get("allowed_claims", []) or []),
        len(decision.get("blocked_claims", []) or []),
        len(decision.get("required_evidence", []) or []),
        1,
    )
    allowed = list(decision.get("allowed_claims", []) or [])
    blocked = list(decision.get("blocked_claims", []) or [])
    evidence = list(decision.get("required_evidence", []) or [])
    for index in range(max_rows):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(allowed[index] if index < len(allowed) else "").replace("|", "/"),
                    str(blocked[index] if index < len(blocked) else "").replace("|", "/"),
                    str(evidence[index] if index < len(evidence) else "").replace("|", "/"),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Client Pain Radar",
            "",
            "| Priority | Gate | User Pain | Advisor Opening | Proof To Show | Success Signal |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if result.get("client_pain_radar"):
        for card in result["client_pain_radar"]:
            proof = "<br>".join(str(item) for item in card.get("proof_to_show", [])[:3])
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{card.get('priority', '')}`",
                        f"`{card.get('gate', '')}`",
                        str(card.get("user_pain", "")).replace("|", "/"),
                        str(card.get("advisor_opening", "")).replace("|", "/"),
                        proof.replace("|", "/"),
                        str(card.get("success_signal", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | `none` | Collect reviewed cases first. | Start with delivery bundles. | At least one reviewed case. | Portfolio has evidence. |")

    proof_gap_ledger = result.get("proof_gap_ledger", {}) or {}
    lines.extend(
        [
            "",
            "## Proof Gap Ledger",
            "",
            f"Status: `{proof_gap_ledger.get('status', 'unknown')}`",
            "",
            "| Priority | Gate | Owner | Cadence | Missing Proof | Client Risk | Evidence Standard |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if proof_gap_ledger.get("items"):
        for item in proof_gap_ledger["items"]:
            missing_proof = "<br>".join(str(proof) for proof in item.get("missing_proof", [])[:3])
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{item.get('priority', '')}`",
                        f"`{item.get('gate', '')}`",
                        f"`{item.get('owner', '')}`",
                        f"`{item.get('review_cadence', '')}`",
                        missing_proof.replace("|", "/"),
                        str(item.get("client_risk", "")).replace("|", "/"),
                        str(item.get("evidence_standard", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | `none` | `advisor_lead` | `weekly` | Collect reviewed delivery bundles. | No portfolio-level pain evidence yet. | At least one reviewed case exists. |")

    guardrails = result.get("communication_guardrails", {}) or {}
    lines.extend(
        [
            "",
            "## Advisor Communication Guardrails",
            "",
            f"Status: `{guardrails.get('status', 'unknown')}`",
            "",
            str(guardrails.get("guardrail_standard", "")),
            "",
            "| Priority | Gate | Approved Opening | Must Disclose | Forbidden Language | Escalate When |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if guardrails.get("cards"):
        for card in guardrails["cards"]:
            must_disclose = "<br>".join(str(item) for item in card.get("must_disclose", [])[:3])
            forbidden = "<br>".join(str(item) for item in card.get("forbidden_language", [])[:3])
            escalate_when = "<br>".join(str(item) for item in card.get("escalate_when", [])[:3])
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{card.get('priority', '')}`",
                        f"`{card.get('gate', '')}`",
                        str(card.get("approved_opening", "")).replace("|", "/"),
                        must_disclose.replace("|", "/"),
                        forbidden.replace("|", "/"),
                        escalate_when.replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | `none` | Collect reviewed cases first. | Do not make quality claims yet. | No guarantee language. | Escalate guarantee requests. |")

    lines.extend(
        [
            "",
            "## Advisor Lead Brief",
            "",
        ]
    )
    for item in result.get("advisor_lead_brief", []) or []:
        lines.append(
            f"- `{item.get('priority', 'P2')}` {item.get('focus', '')} "
            f"Reason: {item.get('why', '')}"
        )

    lines.extend(
        [
            "",
            "## User Pain Points",
            "",
            "| Priority | Gate | Affected | Pain Point | Operator Response |",
            "| --- | --- | ---: | --- | --- |",
        ]
    )
    for point in result.get("pain_points", []) or []:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{point.get('priority', '')}`",
                    f"`{point.get('gate', '')}`",
                    f"{float(point.get('affected_rate', 0.0)):.1%}",
                    str(point.get("pain_point", "")).replace("|", "/"),
                    str(point.get("operator_response", "")).replace("|", "/"),
                ]
            )
            + " |"
        )

    lines.extend(
        [
            "",
            "## Advisor Playbook",
            "",
            "| Priority | Gate | Stage | Intake Questions | Acceptance Evidence |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    if result.get("advisor_playbook"):
        for card in result["advisor_playbook"]:
            questions = "<br>".join(str(item) for item in card.get("intake_questions", [])[:3])
            evidence = "<br>".join(str(item) for item in card.get("acceptance_evidence", [])[:3])
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{card.get('priority', '')}`",
                        f"`{card.get('gate', '')}`",
                        f"`{card.get('handoff_stage', '')}`",
                        questions.replace("|", "/"),
                        evidence.replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | `none` | `portfolio_collection` | Collect delivery bundles. | At least one reviewed case. |")

    training = result.get("advisor_training_plan", {}) or {}
    lines.extend(
        [
            "",
            "## Advisor Training Plan",
            "",
            f"Status: `{training.get('status', 'unknown')}`",
            "",
            "| Priority | Module | Source Gate | Practice Drill |",
            "| --- | --- | --- | --- |",
        ]
    )
    if training.get("modules"):
        for module in training["modules"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{module.get('priority', '')}`",
                        str(module.get("title", "")).replace("|", "/"),
                        f"`{module.get('source_gate', '')}`",
                        str(module.get("practice_drill", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | Collect delivery cases | `none` | Review enough cases before training. |")

    lines.extend(["", "### Operating Cadence", ""])
    for item in training.get("operating_cadence", []) or []:
        lines.append(
            f"- `{item.get('cadence', '')}` `{item.get('owner', '')}`: {item.get('action', '')}"
        )
    if training.get("pass_condition"):
        lines.extend(["", f"Pass condition: {training['pass_condition']}"])

    action_register = result.get("action_register", {}) or {}
    lines.extend(
        [
            "",
            "## Action Register",
            "",
            f"Status: `{action_register.get('status', 'unknown')}`",
            "",
            "| Priority | Owner | Cadence | Source | Action | Success Metric |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    if action_register.get("items"):
        for item in action_register["items"]:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{item.get('priority', '')}`",
                        f"`{item.get('owner', '')}`",
                        f"`{item.get('cadence', '')}`",
                        f"`{item.get('source', '')}`",
                        str(item.get("action", "")).replace("|", "/"),
                        str(item.get("success_metric", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | `advisor_lead` | `weekly` | `portfolio_collection` | Collect delivery bundles. | At least one reviewed case exists. |")

    rescue_queue = result.get("case_rescue_queue", {}) or {}
    lines.extend(
        [
            "",
            "## Case Rescue Queue",
            "",
            f"Status: `{rescue_queue.get('status', 'unknown')}`",
            "",
            "| Priority | Case | Owner | Cadence | Failed Gates | Rescue Steps | Client Update |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    if rescue_queue.get("items"):
        for item in rescue_queue["items"]:
            failed = ", ".join(str(gate) for gate in item.get("failed_gates", []) or [])
            steps = "<br>".join(str(step) for step in item.get("rescue_steps", [])[:3])
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{item.get('priority', '')}`",
                        f"`{item.get('case_id', '')}`",
                        f"`{item.get('owner', '')}`",
                        f"`{item.get('cadence', '')}`",
                        failed.replace("|", "/"),
                        steps.replace("|", "/"),
                        str(item.get("client_update_script", "")).replace("|", "/"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| `P2` | `none` | `advisor_lead` | `weekly` | none | Collect reviewed cases first. | No client update needed. |")

    lines.extend(["", "## Escalation Queue", "", "| Case | Status | Score | Failed Gates |", "| --- | --- | ---: | --- |"])
    for item in result.get("escalation_queue", []) or []:
        failed = ", ".join(
            f"{gate.get('gate')}={gate.get('status')}"
            for gate in item.get("failed_gates", []) or []
        )
        lines.append(
            f"| `{item.get('case_id', '')}` | `{item.get('status', '')}` | "
            f"{float(item.get('portfolio_score', 0.0)):.1%} | {failed} |"
        )

    lines.extend(["", "## Repeated Next Actions", ""])
    for index, item in enumerate(result.get("repeated_next_actions", []) or [], 1):
        lines.append(f"{index}. ({item.get('count', 0)} cases) {item.get('action', '')}")
    if not result.get("repeated_next_actions"):
        lines.append("1. No repeated next actions.")

    return "\n".join(lines) + "\n"
