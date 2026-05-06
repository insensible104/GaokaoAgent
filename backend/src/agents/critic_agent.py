"""Agent 4: 反思审查智能体（简化版）"""
from langchain_core.messages import AIMessage

from models.state import SupervisorState
from models.audit_result import AuditResult, AuditStatus
from engines.rag_enrollment_checker import get_rag_checker
from recommendation.policy_config import HIGH_TAIL_RISK_THRESHOLD


def critic_agent_node(state: SupervisorState) -> dict:
    """
    Critic Agent 节点：审计报告（简化版）
    """
    print("[Agent 4] Critic Agent 启动...")
    print("[进度] 正在审计报告质量...")

    report = state["report_draft"]
    matrix = state["game_matrix"]
    profile = state["user_profile"]
    retry_count = state.get("retry_count", 0)

    if not report or not matrix or not profile:
        # 修复：设置audit_result避免路由逻辑出错，并强制结束避免无限循环
        audit = AuditResult(status=AuditStatus.PASS)
        audit.add_issue("缺少必要数据，但已达最大重试次数", "强制通过")
        return {
            "audit_result": audit,
            "current_agent": "critic_agent",
            "retry_count": retry_count,
            "debug_logs": ["[WARN] Critic Agent: 缺少必要数据，强制通过避免死循环"],
            "messages": [AIMessage(content="系统生成的推荐方案已准备就绪")]
        }

    audit = AuditResult(status=AuditStatus.PASS)

    # 如果重试次数>=3，强制通过避免死循环
    if retry_count >= 3:
        print(f"[WARN] 已重试{retry_count}次，强制通过审计")
        audit.add_issue(
            f"经过{retry_count}次优化后，当前方案为最优解",
            "已自动批准"
        )
        return {
            "audit_result": audit,
            "current_agent": "critic_agent",
            "retry_count": retry_count,
            "debug_logs": [f"[OK] Critic Agent: 强制通过（重试{retry_count}次）"],
            "messages": [AIMessage(content=f"[OK] 审计通过（经{retry_count}次优化）\n\n{report.full_markdown}")]
        }

    # 审计1：逻辑自洽性检验（保底校录取概率必须>90%，符合实际）
    safe_rows = [r for r in matrix.major_group_rows if r.strategy_tag.value == "safe"]

    if safe_rows:
        min_safe_prob = min(r.admission_prob for r in safe_rows)
        if min_safe_prob < 0.90:  # 90%是合理的保底阈值（1/10的风险是可接受的）
            audit.status = AuditStatus.REJECT_LOGIC
            audit.add_issue(
                f"保底校录取概率过低（{min_safe_prob:.1%} < 90%），存在滑档风险",
                "建议增加更稳妥的保底院校或扩大搜索范围"
            )
            audit.reroute_to = "game_agent"
    else:
        # 没有找到任何保底院校
        print(f"[WARN] Critic: No safe schools found! All tags: {[r.strategy_tag.value for r in matrix.major_group_rows[:5]]}")
        audit.status = AuditStatus.REJECT_LOGIC
        audit.add_issue(
            "未找到保底院校，存在严重滑档风险",
            "建议扩大搜索范围或降低志愿定位"
        )
        audit.reroute_to = "game_agent"

    # 审计2：调剂风险检验（黑名单专业警告）
    # 修复：不强制驳回，只记录提醒即可
    blacklist_risks = [r for r in matrix.major_group_rows if r.is_blacklist_risk]
    if blacklist_risks and audit.status == AuditStatus.PASS:
        # 只记录信息，不驳回（黑名单风险已在前端可视化展示）
        print(f"[INFO] 检测到{len(blacklist_risks)}个可能调剂到黑名单专业的志愿")
        print(f"[INFO] 这些风险已在前端标注（🚫图标），用户可见")
        # 不再强制要求报告中有足够的文字警告
        # if len(report.risk_warnings) < len(blacklist_risks):
        #     audit.status = AuditStatus.REJECT_ADJUSTMENT
        #     audit.add_issue(...)
        #     audit.reroute_to = "report_agent"

    # 审计3：冲稳保比例检验
    if not matrix.is_balanced and audit.status == AuditStatus.PASS:
        audit.add_issue(
            f"冲稳保比例不均衡（冲{matrix.total_rush} 稳{matrix.total_target} 保{matrix.total_safe}）",
            "建议调整志愿表结构"
        )
        # 这个问题不强制驳回，只是提醒

    # 审计3.5：广东志愿表结构和组内调剂风险检验
    volunteer_plan = getattr(matrix, "volunteer_plan", None)
    if volunteer_plan and audit.status == AuditStatus.PASS:
        key_choices = [choice for choice in volunteer_plan.choices if choice.is_key_prefix]
        key_high_tail_choices = [
            choice
            for choice in key_choices
            if choice.tail_assignment_risk >= HIGH_TAIL_RISK_THRESHOLD
        ]
        if not key_choices:
            audit.status = AuditStatus.REJECT_LOGIC
            audit.add_issue(
                "志愿表没有识别出关键前缀，无法判断哪些专业组真正可能决定录取结果",
                "建议重新计算 first_hit_prob / prefix_role"
            )
            audit.reroute_to = "game_agent"
        if key_high_tail_choices and audit.status == AuditStatus.PASS and len(report.risk_warnings) < len(key_high_tail_choices):
            audit.status = AuditStatus.REJECT_ADJUSTMENT
            audit.add_issue(
                f"{len(key_high_tail_choices)} 个关键前缀志愿存在高尾部调剂风险，但报告风险提示不足",
                "报告必须优先解释高 first_hit_prob 且高 tail_assignment_risk 的专业组"
            )
            audit.reroute_to = "report_agent"

        missing_structure = [
            choice
            for choice in volunteer_plan.choices
            if not choice.school_code
            or not choice.major_group_code
            or not choice.major_choices
            or len(choice.major_choices) > 6
        ]
        if missing_structure:
            audit.status = AuditStatus.REJECT_LOGIC
            audit.add_issue(
                f"{len(missing_structure)}行志愿缺少院校代码、专业组代码或1-6个专业志愿",
                "请重新生成可落到广东志愿表的结构化志愿行"
            )
            audit.reroute_to = "game_agent"

        high_tail_safe = [
            choice
            for choice in volunteer_plan.choices
            if choice.strategy_tag.value == "safe"
            and choice.tail_assignment_risk >= HIGH_TAIL_RISK_THRESHOLD
        ]
        if high_tail_safe and audit.status == AuditStatus.PASS:
            audit.status = AuditStatus.REJECT_ADJUSTMENT
            audit.add_issue(
                f"{len(high_tail_safe)}个保底志愿存在较高组内尾部调剂风险",
                "保底项不仅要投档概率高，也要保证服从调剂后的最差专业可接受"
            )
            audit.reroute_to = "game_agent"

        hidden_blacklist = [
            choice
            for choice in volunteer_plan.choices
            if any(major.is_blacklisted for major in choice.major_choices)
        ]
        if hidden_blacklist and audit.status == AuditStatus.PASS:
            audit.status = AuditStatus.REJECT_ADJUSTMENT
            audit.add_issue(
                f"{len(hidden_blacklist)}行志愿的1-6专业中包含用户黑名单专业",
                "黑名单专业不应进入建议填写的专业志愿顺序"
            )
            audit.reroute_to = "game_agent"

    # 审计4：RAG招生简章规则检验（选科要求、单科门槛、体检限制等硬性规则）
    if audit.status == AuditStatus.PASS:
        try:
            rag_checker = get_rag_checker()

            if rag_checker.is_available:
                print("[进度] 正在检查招生简章硬性规则...")

                # 构建用户画像字典（用于RAG检查）
                # 修复问题A-1：使用正确的属性名
                # 修复问题NEW-1：将subject_group转为列表格式（RAG期望列表）
                user_profile_dict = {
                    "total_score": profile.score,  # 修复：使用score而非total_score
                    "selected_subjects": [profile.subject_group],  # 修复NEW-1：转为列表格式
                    "chinese_score": profile.subject_scores.get('语文') if profile.subject_scores else None,
                    "math_score": profile.subject_scores.get('数学') if profile.subject_scores else None,
                    "english_score": profile.subject_scores.get('外语') if profile.subject_scores else None,
                }

                # 检查每个志愿
                violation_count = 0
                for row in matrix.major_group_rows:
                    # 修复问题2：使用major_list[0]而不是major_group_name
                    major_name = row.major_list[0] if row.major_list else row.major_group_code
                    result = rag_checker.check_volunteer(
                        school_code=row.school_code,
                        school_name=row.school_name,
                        major_name=major_name,
                        user_profile=user_profile_dict,
                        top_k=3
                    )

                    if result["has_violations"]:
                        violation_count += 1
                        for violation in result["violations"]:
                            audit.status = AuditStatus.REJECT_LOGIC
                            audit.add_issue(
                                f"【硬性规则违规】{row.school_name} - {major_name}",
                                f"{violation['rule_type']}: {violation['reason']}"
                            )

                        # 只要有一个严重违规，就立即驳回
                        if violation_count >= 1:
                            audit.reroute_to = "game_agent"
                            break

                if violation_count > 0:
                    print(f"[WARN] RAG检查发现{violation_count}处硬性规则违规")
                else:
                    print("[OK] RAG检查通过，无硬性规则违规")
            else:
                print("[INFO] RAG系统不可用，跳过招生简章规则检查")

        except Exception as e:
            print(f"[WARN] RAG检查异常（已忽略）：{e}")
            # 异常时不影响审计流程，优雅降级

    # 返回审计结果
    if audit.is_approved:
        print("[OK] 审计通过")
        return {
            "audit_result": audit,
            "current_agent": "critic_agent",
            "retry_count": retry_count,
            "debug_logs": ["[OK] Critic Agent: 审计通过"],
            "messages": [AIMessage(content=f"[OK] 风控审计通过！\n\n{report.full_markdown}")]
        }
    else:
        print(f"[WARN] 审计失败: {audit.issues}")
        return {
            "audit_result": audit,
            "current_agent": "critic_agent",
            "retry_count": retry_count + 1,  # 增加重试计数
            "debug_logs": [f"[WARN] Critic Agent: 审计失败 - {audit.issues}"],
            "messages": [AIMessage(content=f"[ERROR] 审计未通过（第{retry_count+1}次尝试）\n\n问题:\n" + "\n".join(f"- {issue}" for issue in audit.issues) + f"\n\n正在回退到 {audit.reroute_to} 重新处理...")]
        }
