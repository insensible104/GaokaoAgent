"""Agent 4: 反思审查智能体（增强版 - Step-Level Reward）"""
import os

from langchain_core.messages import AIMessage
from typing import List

from models.state import SupervisorState
from models.audit_result import AuditResult, AuditStatus
from models.step_reward import StepReward, ToolCallType, create_step_reward
from prompts.critic import critic_audit_prompt
from utils.agent_bus import get_messages_for_stage, publish_agent_message, remember
from utils import get_llm


def critic_agent_node(state: SupervisorState) -> dict:
    """
    Critic Agent 节点：审计报告 + Step-Level Reward 评估

    新增功能：
    1. 评估每个步骤的执行质量
    2. 记录 Step-Level Reward
    3. 根据负奖励决定是否回退
    """
    print("[Critic Agent] 启动增强审计...")

    report = state.get("report_draft")
    matrix = state.get("game_matrix")
    profile = state.get("user_profile")
    retry_count = state.get("retry_count", 0)
    messages = state.get("messages", [])
    active_loop = state.get("active_loop")
    inbound_messages = get_messages_for_stage(
        state,
        stage="report",
        recipients=["critic_agent"],
    ) + get_messages_for_stage(
        state,
        stage="deep_research",
        recipients=["critic_agent"],
    )

    # 提取用户原始问题
    user_query = messages[0].content if messages else ""

    # === 新增：Step-Level Reward 评估 ===
    step_rewards = evaluate_execution_steps(state, user_query)

    # 检查是否有严重负奖励
    negative_steps = [r for r in step_rewards if r.reward_value < -0.5]

    if negative_steps:
        print(f"[WARN] 检测到 {len(negative_steps)} 个低质量步骤")
        for step in negative_steps:
            print(f"  - Step {step.step_id} ({step.agent_name}): {step.reasoning}")

        # 如果重试次数 < 2，触发回退
        if retry_count < 2:
            # 生成反思建议
            reflection = generate_reflection(negative_steps)

            return {
                "audit_result": AuditResult(
                    status=AuditStatus.REJECT_LOGIC,
                    issues=[f"步骤 {s.step_id} 质量低：{s.reasoning}" for s in negative_steps],
                    suggestions=reflection,
                    reroute_to="profiling_agent"  # 回退到开始
                ),
                "step_rewards": step_rewards,
                "reflection_history": [reflection],
                "agent_messages": publish_agent_message(
                    sender="critic_agent",
                    stage="critic",
                    message_type="critique",
                    content=(
                        f"Step-level audit rejected the run with {len(negative_steps)} negative steps; "
                        f"reroute=profiling_agent, inbound_context={len(inbound_messages)}."
                    ),
                    recipients=["profiling_agent", "broadcast"],
                    action_preference="profiling_agent",
                    confidence=0.9,
                    metadata={
                        "negative_step_count": len(negative_steps),
                        "retry_count": retry_count + 1,
                    },
                )["agent_messages"],
                "agent_memories": remember(
                    agent_name="critic_agent",
                    stage="critic",
                    note_type="reflection",
                    content=f"Rejected run due to negative steps: {[s.step_id for s in negative_steps]}",
                    importance=0.9,
                )["agent_memories"],
                "current_agent": "critic_agent",
                "retry_count": retry_count + 1,
                "debug_logs": [
                    f"[WARN] Step-Level Reward 检测到低质量执行",
                    f"[WARN] 负奖励步骤: {[s.step_id for s in negative_steps]}",
                    f"[Action] 触发回退，重试计数: {retry_count + 1}"
                ],
                "messages": [AIMessage(content=f"""[Step-Level Reward] 检测到执行质量问题

问题步骤：
{format_negative_steps(negative_steps)}

反思建议：
{reflection}

正在回退重新处理...""")]
            }

    # === 原有审计逻辑（针对 Fast Loop）===
    if active_loop and active_loop.value == "fast":
        audit_result = audit_fast_loop(report, matrix, profile, retry_count)
    elif active_loop and active_loop.value == "slow":
        audit_result = audit_slow_loop(state, retry_count)
    elif active_loop and active_loop.value == "multimodal":
        audit_result = audit_multimodal_loop(state, retry_count)
    else:
        # 默认审计
        audit_result = AuditResult(status=AuditStatus.PASS)

    # 如果审计通过，记录正奖励
    audit_result, llm_critic_metadata = _apply_optional_llm_critic(
        audit=audit_result,
        report=report,
        matrix=matrix,
        profile=profile,
        retry_count=retry_count,
    )

    if audit_result.is_approved:
        print("[OK] 审计通过")
        return {
            "audit_result": audit_result,
            "step_rewards": step_rewards,
            "agent_messages": publish_agent_message(
                sender="critic_agent",
                stage="critic",
                message_type="summary",
                content=(
                    f"Audit approved with {len(step_rewards)} step rewards and "
                    f"inbound_context={len(inbound_messages)}."
                ),
                recipients=["broadcast"],
                action_preference="END",
                confidence=0.88,
                metadata={
                    "approved": True,
                    "positive_step_count": len([r for r in step_rewards if r.reward_value > 0]),
                    "negative_step_count": len(negative_steps),
                    **llm_critic_metadata,
                },
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="critic_agent",
                stage="critic",
                note_type="approval",
                content=f"Approved run with {len(step_rewards)} step rewards.",
                importance=0.85,
            )["agent_memories"],
            "current_agent": "critic_agent",
            "retry_count": retry_count,
            "debug_logs": [
                "[OK] Critic Agent: 审计通过",
                f"[OK] Step Rewards: {len([r for r in step_rewards if r.reward_value > 0])} positive, {len(negative_steps)} negative"
            ],
            "messages": [AIMessage(content=f"[OK] 风控审计通过！\n\n{report.full_markdown if report else state.get('research_report', '')}")]
        }
    else:
        print(f"[WARN] 审计失败: {audit_result.issues}")
        return {
            "audit_result": audit_result,
            "step_rewards": step_rewards,
            "agent_messages": publish_agent_message(
                sender="critic_agent",
                stage="critic",
                message_type="critique",
                content=(
                    f"Audit rejected with issues={audit_result.issues[:3]}; "
                    f"reroute={audit_result.reroute_to}, inbound_context={len(inbound_messages)}."
                ),
                recipients=[audit_result.reroute_to or "broadcast", "broadcast"],
                action_preference=audit_result.reroute_to,
                confidence=0.85,
                metadata={
                    "approved": False,
                    "retry_count": retry_count + 1,
                    "issue_count": len(audit_result.issues),
                    **llm_critic_metadata,
                },
            )["agent_messages"],
            "agent_memories": remember(
                agent_name="critic_agent",
                stage="critic",
                note_type="rejection",
                content=f"Rejected run and rerouted to {audit_result.reroute_to}: {audit_result.issues[:3]}",
                importance=0.85,
            )["agent_memories"],
            "current_agent": "critic_agent",
            "retry_count": retry_count + 1,
            "debug_logs": [f"[WARN] Critic Agent: 审计失败 - {audit_result.issues}"],
            "messages": [AIMessage(content=f"[ERROR] 审计未通过（第{retry_count+1}次尝试）\n\n问题:\n" + "\n".join(f"- {issue}" for issue in audit_result.issues) + f"\n\n正在回退到 {audit_result.reroute_to} 重新处理...")]
        }


def evaluate_execution_steps(state: SupervisorState, user_query: str) -> List[StepReward]:
    """
    评估执行步骤（模拟版本）

    在完整实现中，每个 Agent 应该在执行后记录步骤
    这里我们基于 state 中的数据进行事后评估
    """
    step_rewards = []
    step_id = 1

    # 评估 Profiling Agent（如果有）
    if state.get("user_profile"):
        # 假设 Profiling Agent 调用了 LLM
        reward = create_step_reward(
            step_id=step_id,
            agent_name="profiling_agent",
            tool_call_type=ToolCallType.LLM_CALL,
            query="提取用户画像",
            result=str(state["user_profile"]),
            user_query=user_query
        )
        step_rewards.append(reward)
        step_id += 1

    # 评估 Game Agent（如果有）
    if state.get("game_matrix"):
        matrix = state["game_matrix"]
        # 假设 Game Agent 调用了 Quant Engine
        # 使用 major_group_rows 而非旧的 rows
        candidate_count = len(matrix.major_group_rows) if matrix.major_group_rows else len(matrix.rows)
        reward = create_step_reward(
            step_id=step_id,
            agent_name="game_agent",
            tool_call_type=ToolCallType.QUANT_ENGINE,
            query=f"搜索位次 {state.get('user_profile').rank if state.get('user_profile') else 'N/A'}",
            result=f"找到 {candidate_count} 个候选",
            user_query=user_query
        )
        step_rewards.append(reward)
        step_id += 1

    # 评估 Deep Research Agent（如果有）
    if state.get("search_queries") and len(state["search_queries"]) > 0:
        for query in state["search_queries"]:
            reward = create_step_reward(
                step_id=step_id,
                agent_name="deep_research_agent",
                tool_call_type=ToolCallType.SEARCH_TOOL,
                query=query,
                result="搜索结果...",  # 简化
                user_query=user_query
            )
            step_rewards.append(reward)
            step_id += 1

    # 评估 Multimodal Agent（如果有）
    if state.get("pdf_sources") and len(state["pdf_sources"]) > 0:
        for pdf_path in state["pdf_sources"]:
            reward = create_step_reward(
                step_id=step_id,
                agent_name="multimodal_agent",
                tool_call_type=ToolCallType.PDF_PARSER,
                query=f"解析 {pdf_path}",
                result="PDF 解析结果...",
                user_query=user_query
            )
            step_rewards.append(reward)
            step_id += 1

    return step_rewards


def generate_reflection(negative_steps: List[StepReward]) -> str:
    """
    根据负奖励步骤生成反思建议
    """
    reflections = []

    for step in negative_steps:
        if step.is_result_empty:
            reflections.append(f"步骤 {step.step_id}：工具调用返回空结果，建议检查查询参数或换用其他工具")

        if not step.is_tool_appropriate:
            reflections.append(f"步骤 {step.step_id}：工具选择不当（{step.tool_call_type.value}），建议分析问题类型后选择正确工具")

        if not step.is_result_relevant:
            reflections.append(f"步骤 {step.step_id}：结果与问题不相关，建议优化查询关键词")

        if step.token_efficiency < 0.5:
            reflections.append(f"步骤 {step.step_id}：Token 效率低（{step.token_efficiency:.2f}），建议使用更精准的查询")

    return "\n".join(reflections) if reflections else "请重新评估任务并选择合适的工具"


def format_negative_steps(negative_steps: List[StepReward]) -> str:
    """格式化负奖励步骤"""
    result = []
    for step in negative_steps:
        result.append(f"- Step {step.step_id} ({step.agent_name}): {step.reasoning} (奖励: {step.reward_value:.2f})")
    return "\n".join(result)


def _llm_critic_enabled() -> bool:
    return os.getenv("ENABLE_LLM_CRITIC", "0").lower() in {"1", "true", "yes", "on"}


def _apply_optional_llm_critic(
    *,
    audit: AuditResult,
    report,
    matrix,
    profile,
    retry_count: int,
) -> tuple[AuditResult, dict]:
    """Use an LLM as a final report auditor without replacing deterministic checks."""
    metadata = {"llm_critic_used": False}
    if not _llm_critic_enabled() or not report or not matrix or not profile:
        return audit, metadata

    try:
        report_payload = report.model_dump() if hasattr(report, "model_dump") else str(report)
        matrix_payload = matrix.model_dump() if hasattr(matrix, "model_dump") else str(matrix)
        profile_payload = profile.model_dump() if hasattr(profile, "model_dump") else str(profile)
        prompt = critic_audit_prompt.format(
            report_draft=report_payload,
            game_matrix=matrix_payload,
            user_profile=profile_payload,
        )
        structured_llm = get_llm(temperature=0).with_structured_output(AuditResult)
        llm_audit: AuditResult = structured_llm.invoke(prompt)
        metadata.update(
            {
                "llm_critic_used": True,
                "llm_critic_status": llm_audit.status.value,
                "llm_critic_issue_count": len(llm_audit.issues),
            }
        )

        for issue in llm_audit.issues:
            if issue not in audit.issues:
                audit.issues.append(issue)
        for suggestion in llm_audit.fix_suggestions:
            if suggestion not in audit.fix_suggestions:
                audit.fix_suggestions.append(suggestion)

        if (
            audit.status == AuditStatus.PASS
            and llm_audit.status != AuditStatus.PASS
            and retry_count < 3
        ):
            audit.status = llm_audit.status
            audit.reroute_to = llm_audit.reroute_to or "report_agent"
        return audit, metadata
    except Exception as exc:
        metadata["llm_critic_error"] = str(exc)
        return audit, metadata


def _report_text(report) -> str:
    parts = [
        getattr(report, "full_markdown", "") or "",
        getattr(report, "executive_summary", "") or "",
        getattr(report, "strategy_analysis", "") or "",
    ]
    parts.extend(getattr(report, "school_recommendations", []) or [])
    parts.extend(getattr(report, "risk_warnings", []) or [])
    return "\n".join(str(part) for part in parts if part)


def _missing_key_decision_evidence(report, volunteer_plan) -> list:
    """Return key prefix choices whose decision evidence is not explained."""
    if not report or not volunteer_plan:
        return []
    text = _report_text(report)
    evidence_markers = (
        "机会逻辑",
        "适配理由",
        "风险边界",
        "opportunity_thesis",
        "student_fit",
        "downside_guard",
    )
    missing = []
    for choice in volunteer_plan.choices:
        if not getattr(choice, "is_key_prefix", False):
            continue
        cards = getattr(choice, "market_evidence_cards", []) or []
        decision_cards = [
            card
            for card in cards
            if card.get("signal_type") in {"opportunity_thesis", "student_fit", "downside_guard"}
        ]
        if not decision_cards:
            continue
        claims = [str(card.get("claim") or "") for card in decision_cards]
        has_marker = any(marker in text for marker in evidence_markers)
        has_claim = any(claim and claim[:40] in text for claim in claims)
        if not has_marker and not has_claim:
            missing.append(choice)
    return missing


def audit_fast_loop(report, matrix, profile, retry_count) -> AuditResult:
    """审计快思考循环（改进版 - 移除强制通过）"""
    if not report or not matrix or not profile:
        return AuditResult(
            status=AuditStatus.REJECT_LOGIC,
            issues=["缺少必要数据"],
            reroute_to="profiling_agent"
        )

    audit = AuditResult(status=AuditStatus.PASS)
    volunteer_plan = getattr(matrix, "volunteer_plan", None)

    if volunteer_plan:
        key_choices = [choice for choice in volunteer_plan.choices if choice.is_key_prefix]
        key_high_tail_choices = [
            choice
            for choice in key_choices
            if choice.tail_assignment_risk >= 0.55
        ]

        if not key_choices and retry_count < 3:
            audit.status = AuditStatus.REJECT_LOGIC
            audit.add_issue(
                "志愿表没有识别出关键前缀，无法判断哪些专业组真正可能决定录取结果",
                "建议：重新计算 first_hit_prob / prefix_role，再生成报告"
            )
            audit.reroute_to = "game_agent"

        if (
            key_high_tail_choices
            and audit.status == AuditStatus.PASS
            and report
            and len(report.risk_warnings) < len(key_high_tail_choices)
            and retry_count < 3
        ):
            audit.status = AuditStatus.REJECT_ADJUSTMENT
            audit.add_issue(
                f"{len(key_high_tail_choices)} 个关键前缀志愿存在高尾部调剂风险，但报告风险提示不足",
                "建议：报告必须优先解释高 first_hit_prob 且高 tail_assignment_risk 的专业组"
            )
            audit.reroute_to = "report_agent"

        if volunteer_plan.expected_admission_prob < 0.90 and audit.status == AuditStatus.PASS:
            audit.add_issue(
                f"整张志愿表累计投档命中概率偏低（{volunteer_plan.expected_admission_prob:.1%}）",
                "建议：补充更可靠的保底专业组，避免只优化前几个机会项"
            )

        missing_decision_evidence = _missing_key_decision_evidence(report, volunteer_plan)
        if missing_decision_evidence and audit.status == AuditStatus.PASS and retry_count < 3:
            audit.status = AuditStatus.REJECT_LOGIC
            audit.add_issue(
                f"{len(missing_decision_evidence)} key prefix choices have decision evidence cards, "
                "but the report does not explain their opportunity thesis, student fit, or downside guard.",
                "Recommendation: regenerate the report and use decision_evidence_cards as the explanation spine."
            )
            audit.reroute_to = "report_agent"

    # 审计1：保底校概率（降低到90%，更实际）
    safe_rows = [r for r in matrix.major_group_rows if r.strategy_tag.value == "safe"]
    if safe_rows:
        min_safe_prob = min(r.admission_prob for r in safe_rows)
        if min_safe_prob < 0.90:
            # 只有在重试次数 < 5 时才回退
            if retry_count < 5:
                audit.status = AuditStatus.REJECT_LOGIC
                audit.add_issue(
                    f"保底校录取概率过低（{min_safe_prob:.1%} < 90%），存在滑档风险",
                    f"建议扩大搜索范围，寻找更稳妥的保底院校（已重试 {retry_count} 次）"
                )
                audit.reroute_to = "game_agent"
            else:
                # 重试5次后，放宽标准但给出警告
                print(f"[WARN] 已重试{retry_count}次，保底概率为{min_safe_prob:.1%}，建议用户谨慎选择")
                audit.add_issue(
                    f"保底校录取概率为{min_safe_prob:.1%}，略低于理想标准",
                    "建议填报时额外关注本省补录政策"
                )
    else:
        # 没有保底校 - 严重问题
        if retry_count < 5:
            audit.status = AuditStatus.REJECT_LOGIC
            audit.add_issue(
                "未找到保底院校，存在严重滑档风险",
                "必须扩大位次搜索范围，寻找保底院校"
            )
            audit.reroute_to = "game_agent"
        else:
            # 实在找不到保底校，给出严重警告
            audit.add_issue(
                "警告：未找到符合标准的保底院校",
                "建议：1）考虑降低专业要求 2）考虑省外院校 3）关注征集志愿"
            )

    # 审计2：调剂风险（修复：添加重试次数限制）
    blacklist_risks = [r for r in matrix.major_group_rows if r.is_blacklist_risk]
    if blacklist_risks and audit.status == AuditStatus.PASS:
        if len(report.risk_warnings) < len(blacklist_risks):
            # 只有在重试次数 < 3 时才回退（黑名单问题通常是数据问题，重试无意义）
            if retry_count < 3:
                audit.status = AuditStatus.REJECT_ADJUSTMENT
                audit.add_issue(
                    f"检测到{len(blacklist_risks)}个可能调剂到黑名单专业的志愿，但报告中警告不足",
                    f"必须在报告中明确标注所有黑名单调剂风险（已重试 {retry_count} 次）"
                )
                audit.reroute_to = "report_agent"
            else:
                # 重试3次后，放行但给出强警告
                print(f"[WARN] 已重试{retry_count}次，仍有{len(blacklist_risks)}个黑名单风险志愿，放行但标注警告")
                audit.add_issue(
                    f"警告：{len(blacklist_risks)}个志愿存在调剂到不喜欢专业的风险",
                    "建议：填报时务必关注专业组内所有专业，或选择服从调剂前仔细考虑"
                )

    # 审计3：冲稳保比例（仅提示，不强制驳回）
    if not matrix.is_balanced and audit.status == AuditStatus.PASS:
        audit.add_issue(
            f"冲稳保比例不均衡（冲{matrix.total_rush} 稳{matrix.total_target} 保{matrix.total_safe}）",
            "建议：冲刺30%、稳妥50%、保底20%"
        )

    return audit


def audit_slow_loop(state: SupervisorState, retry_count: int) -> AuditResult:
    """审计慢思考循环"""
    research_report = state.get("research_report")
    evidence_cards = state.get("research_evidence_cards", []) or []

    if not research_report:
        return AuditResult(
            status=AuditStatus.REJECT_LOGIC,
            issues=["深度研究未生成报告"],
            reroute_to="deep_research"
        )

    if "引用与证据附录" not in research_report:
        return AuditResult(
            status=AuditStatus.REJECT_LOGIC,
            issues=["深度研究报告缺少引用与证据附录"],
            fix_suggestions=["必须输出结构化来源证据卡和引用附录，不能只给无来源摘要。"],
            reroute_to="deep_research",
        )

    if not evidence_cards:
        return AuditResult(
            status=AuditStatus.REJECT_LOGIC,
            issues=["深度研究未返回结构化 evidence cards"],
            fix_suggestions=["搜索结果必须转换为 EvidenceCard，标注 source_type、confidence 和 usable_for_prediction。"],
            reroute_to="deep_research",
        )

    official_cards = [
        card
        for card in evidence_cards
        if str(card.get("source_type") or "") in {"official_or_school", "semi_official_aggregator"}
    ]
    usable_cards = [card for card in evidence_cards if card.get("usable_for_prediction")]
    audit = AuditResult(status=AuditStatus.PASS)
    if not official_cards:
        audit.add_issue(
            "深度研究缺少官方/准官方来源证据卡",
            "无网或非官方来源只能作为人工核验提纲，最终填报前必须补充院校官网、招生章程、考试院或阳光高考等来源。",
        )
    if not usable_cards:
        audit.add_issue(
            "当前 evidence cards 均不可直接用于预测",
            "请把 fallback/社媒信息升级为可核验来源后，再支撑高风险填报建议。",
        )
    return audit


def audit_multimodal_loop(state: SupervisorState, retry_count: int) -> AuditResult:
    """审计多模态循环"""
    vision_results = state.get("vision_results", [])

    if not vision_results:
        return AuditResult(
            status=AuditStatus.REJECT_LOGIC,
            issues=["多模态分析未返回结果"],
            reroute_to="multimodal_parser"
        )

    return AuditResult(status=AuditStatus.PASS)
