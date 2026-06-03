"""Build a client-facing delivery bundle for one Gaokao planning case."""

from __future__ import annotations

from pathlib import Path
import json
import shutil
from typing import Any

from evaluation.expectation_packet import (
    build_expectation_packet,
    build_markdown_expectation_packet,
)
from evaluation.intake_audit import build_intake_audit, build_markdown_intake_audit
from evaluation.plan_quality_audit import audit_plan_quality, build_markdown_plan_quality_audit
from evaluation.report_quality import (
    audit_report_quality,
    build_markdown_report_quality_audit,
)
from models.game_matrix import VolunteerPlan
from models.user_profile import UserProfile


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _report_markdown_from_payload(payload: str | dict[str, Any]) -> str:
    if isinstance(payload, str):
        return payload
    if payload.get("full_markdown"):
        return str(payload["full_markdown"])
    sections = [
        f"# {payload.get('title', 'GaokaoAgent 志愿填报战略建议书')}",
        "",
        "## 执行摘要",
        str(payload.get("executive_summary", "")),
        "",
        "## 策略分析",
        str(payload.get("strategy_analysis", "")),
        "",
        "## 院校推荐",
    ]
    for idx, item in enumerate(payload.get("school_recommendations", []) or [], 1):
        sections.append(f"{idx}. {item}")
    if payload.get("risk_warnings"):
        sections.extend(["", "## 风险警示"])
        sections.extend(f"- {item}" for item in payload["risk_warnings"])
    return "\n".join(sections).strip() + "\n"


def _expectation_status(packet: dict[str, Any]) -> str:
    if any(item["status"] == "missing" for item in packet.get("confirmation_items", [])):
        return "blocked"
    if packet.get("status") == "needs_confirmation":
        return "pending_signoff"
    return "ready"


def _bundle_status(
    intake_status: str,
    plan_quality_status: str,
    expectation_status: str,
    report_quality: dict[str, Any],
) -> str:
    if intake_status == "blocked_missing_core":
        return "blocked"
    if plan_quality_status == "blocked":
        return "blocked"
    if expectation_status == "blocked":
        return "blocked"
    if plan_quality_status != "pass":
        return "needs_revision"
    if report_quality.get("status") != "pass":
        return "needs_revision"
    if expectation_status == "pending_signoff" or intake_status == "needs_clarification":
        return "pending_signoff"
    return "ready_to_deliver"


def build_delivery_bundle(
    *,
    profile: UserProfile,
    report_payload: str | dict[str, Any],
    output_dir: Path,
    plan: VolunteerPlan | None = None,
    case_id: str = "",
) -> dict[str, Any]:
    """Write intake, plan, expectation, report, audit, and bundle-index artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    case_id = case_id or "gaokao_case"

    intake_audit = build_intake_audit(profile)
    intake_md = build_markdown_intake_audit(intake_audit)
    intake_json_path = output_dir / "intake_audit.json"
    intake_md_path = output_dir / "intake_audit.md"
    _write_json(intake_json_path, intake_audit)
    intake_md_path.write_text(intake_md, encoding="utf-8")

    expectation_packet = build_expectation_packet(profile)
    expectation_md = build_markdown_expectation_packet(expectation_packet)
    expectation_json_path = output_dir / "expectation_packet.json"
    expectation_md_path = output_dir / "expectation_packet.md"
    _write_json(expectation_json_path, expectation_packet)
    expectation_md_path.write_text(expectation_md, encoding="utf-8")

    report_md = _report_markdown_from_payload(report_payload)
    final_report_path = output_dir / "final_report.md"
    final_report_path.write_text(report_md, encoding="utf-8")

    report_quality = audit_report_quality(report_payload)
    quality_json_path = output_dir / "report_quality_audit.json"
    quality_md_path = output_dir / "report_quality_audit.md"
    _write_json(quality_json_path, report_quality)
    quality_md_path.write_text(build_markdown_report_quality_audit(report_quality), encoding="utf-8")

    plan_quality = _build_plan_quality_artifact(plan, profile, output_dir)
    expectation_state = _expectation_status(expectation_packet)
    intake_state = str(intake_audit.get("status") or "unknown")
    plan_quality_state = str(plan_quality.get("status") or "unknown")
    status = _bundle_status(intake_state, plan_quality_state, expectation_state, report_quality)
    manifest = {
        "case_id": case_id,
        "status": status,
        "intake_status": intake_state,
        "intake_readiness_score": intake_audit.get("readiness_score"),
        "plan_quality_status": plan_quality_state,
        "plan_quality_score": plan_quality.get("total_score"),
        "expectation_status": expectation_state,
        "report_quality_status": report_quality.get("status"),
        "report_quality_score": report_quality.get("total_score"),
        "artifacts": [
            {
                "id": "intake_audit",
                "label": "推荐前问诊完备度审计",
                "path": intake_md_path.name,
                "required": True,
            },
            {
                "id": "expectation_packet",
                "label": "推荐前预期确认单",
                "path": expectation_md_path.name,
                "required": True,
            },
            {
                "id": "plan_quality_audit",
                "label": "志愿表结构质量审计",
                "path": plan_quality.get("artifact_path", "plan_quality_audit.md"),
                "required": True,
            },
            {
                "id": "final_report",
                "label": "最终志愿填报建议报告",
                "path": final_report_path.name,
                "required": True,
            },
            {
                "id": "report_quality_audit",
                "label": "报告交付质量审计",
                "path": quality_md_path.name,
                "required": True,
            },
        ],
        "delivery_gates": [
            {
                "gate": "intake_audit",
                "status": intake_state,
                "requirement": "分数、位次、选科、地域、专业边界和学校/专业权衡必须完成问诊。",
            },
            {
                "gate": "plan_quality",
                "status": plan_quality_state,
                "requirement": "志愿表必须通过整体安全性、保底、冲稳保结构、尾部风险和硬边界审计。",
            },
            {
                "gate": "expectation_packet",
                "status": expectation_state,
                "requirement": "学生/家长确认限制条件、风险边界和非承诺条款。",
            },
            {
                "gate": "report_quality",
                "status": report_quality.get("status"),
                "requirement": "最终报告必须通过交付质量审计。",
            },
        ],
        "next_actions": _next_actions(intake_audit, plan_quality, expectation_state, report_quality),
    }
    manifest_path = output_dir / "delivery_bundle.json"
    index_path = output_dir / "delivery_bundle.md"
    _write_json(manifest_path, manifest)
    index_path.write_text(build_markdown_delivery_bundle(manifest), encoding="utf-8")
    return manifest


def _build_plan_quality_artifact(
    plan: VolunteerPlan | None,
    profile: UserProfile,
    output_dir: Path,
) -> dict[str, Any]:
    if plan is None:
        result = {
            "status": "not_provided",
            "total_score": 0.0,
            "finding_count": 1,
            "findings": [
                {
                    "severity": "P1",
                    "area": "plan_quality",
                    "finding": "交付包缺少 VolunteerPlan，无法审计志愿表结构。",
                    "recommendation": "提供冻结后的 VolunteerPlan JSON，并重新生成交付包。",
                    "missing": ["VolunteerPlan JSON"],
                    "evidence": [],
                }
            ],
            "advisor_standard": "Final delivery must include a structured VolunteerPlan quality audit.",
            "artifact_path": "plan_quality_audit.md",
        }
        lines = [
            "# Volunteer Plan Quality Audit",
            "",
            "Status: `not_provided`",
            "Total score: 0.0%",
            "",
            result["advisor_standard"],
            "",
            "## Findings",
            "",
            "1. `P1` plan_quality: 提供冻结后的 VolunteerPlan JSON，并重新生成交付包。",
        ]
        markdown = "\n".join(lines) + "\n"
    else:
        result = audit_plan_quality(plan, profile)
        markdown = build_markdown_plan_quality_audit(result)
        result["artifact_path"] = "plan_quality_audit.md"

    json_path = output_dir / "plan_quality_audit.json"
    md_path = output_dir / "plan_quality_audit.md"
    _write_json(json_path, result)
    md_path.write_text(markdown, encoding="utf-8")
    return result


def _next_actions(
    intake_audit: dict[str, Any],
    plan_quality: dict[str, Any],
    expectation_status: str,
    report_quality: dict[str, Any],
) -> list[str]:
    actions: list[str] = []
    intake_status = intake_audit.get("status")
    if intake_status == "blocked_missing_core":
        actions.append(str(intake_audit.get("minimum_next_step") or "补齐问诊核心信息。"))
    elif intake_status == "needs_clarification":
        actions.append("先完成问诊审计中的必问问题，再冻结推荐输入。")
    plan_quality_status = plan_quality.get("status")
    if plan_quality_status == "not_provided":
        actions.append("提供冻结后的志愿表 JSON，补跑志愿表结构质量审计。")
    elif plan_quality_status == "blocked":
        actions.append("先修复志愿表硬边界或严重安全性问题，再进入客户交付。")
    elif plan_quality_status == "needs_revision":
        actions.append("根据志愿表结构质量审计调整保底、冲稳保比例、尾部风险或关键志愿依据。")
    if expectation_status == "blocked":
        actions.append("补齐分数、位次、选科等硬信息后再继续推荐。")
    elif expectation_status == "pending_signoff":
        actions.append("让学生和家长签署预期确认单，明确地域、调剂、民办/中外合作和非承诺边界。")
    if report_quality.get("status") != "pass":
        actions.append("根据报告质量审计补充限制条件、风险解释、推荐依据和官方复核边界。")
    if not actions:
        actions.append("交付材料已准备好，可进入最终人工复核和客户交付。")
    return actions


def build_markdown_delivery_bundle(manifest: dict[str, Any]) -> str:
    """Build the client-facing delivery bundle index."""
    lines = [
        "# GaokaoAgent 服务交付包",
        "",
        f"Case: `{manifest.get('case_id', '')}`",
        f"Status: `{manifest.get('status', 'unknown')}`",
        f"Intake readiness: `{manifest.get('intake_status', 'unknown')}` "
        f"({float(manifest.get('intake_readiness_score') or 0.0):.1%})",
        f"Plan quality: `{manifest.get('plan_quality_status', 'unknown')}` "
        f"({float(manifest.get('plan_quality_score') or 0.0):.1%})",
        f"Report quality: `{manifest.get('report_quality_status', 'unknown')}` "
        f"({float(manifest.get('report_quality_score') or 0.0):.1%})",
        "",
        "## 交付材料",
        "",
        "| 材料 | 文件 | 必需 |",
        "| --- | --- | --- |",
    ]
    for item in manifest.get("artifacts", []) or []:
        lines.append(
            f"| {item.get('label', '')} | `{item.get('path', '')}` | "
            f"{'yes' if item.get('required') else 'no'} |"
        )

    lines.extend(["", "## 交付门槛", "", "| Gate | Status | Requirement |", "| --- | --- | --- |"])
    for gate in manifest.get("delivery_gates", []) or []:
        lines.append(
            f"| `{gate.get('gate', '')}` | `{gate.get('status', '')}` | "
            f"{gate.get('requirement', '')} |"
        )

    lines.extend(["", "## 下一步", ""])
    for idx, action in enumerate(manifest.get("next_actions", []) or [], 1):
        lines.append(f"{idx}. {action}")
    return "\n".join(lines) + "\n"


def copy_bundle_to(output_dir: Path, target_dir: Path) -> None:
    """Copy a completed delivery bundle directory to another location."""
    target_dir.parent.mkdir(parents=True, exist_ok=True)
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(output_dir, target_dir)
