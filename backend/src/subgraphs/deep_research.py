"""Deep research subgraph: plan, execute, reflect, synthesize."""

from __future__ import annotations

import os
from typing import Any, List
from urllib.parse import urlparse

from langchain_community.tools.tavily_search import TavilySearchResults
from pydantic import BaseModel, Field

from models.research_state import DeepResearchState
from recommendation.market_evidence import EvidenceCard
from utils.llm_factory import get_llm


class SubQuestionList(BaseModel):
    """Structured planning output for deep research."""

    questions: List[str] = Field(default_factory=list, description="Searchable sub-questions")


class ReflectionResult(BaseModel):
    """Structured reflection output for research sufficiency."""

    is_sufficient: bool = Field(description="Whether current evidence is sufficient")
    knowledge_gaps: List[str] = Field(default_factory=list, description="Missing evidence or gaps")
    information_density: float = Field(ge=0.0, le=1.0, description="Estimated information density")
    reasoning: str = Field(default="", description="Short explanation")


def build_evidence_autopilot_research_topics(
    *,
    province: str,
    school_name: str,
    major_name: str,
    target_year: int,
) -> list[dict[str, Any]]:
    """Build candidate-specific Evidence Autopilot research tasks.

    These tasks are provider requests, not verified evidence. A task may become
    evidence only after source title, URL, excerpt, capture time, and confidence
    are collected by a public provider or a compliant human operator.
    """
    target_label = f"{province} {target_year} {school_name} {major_name}"
    return [
        {
            "id": "official-plan-charter",
            "claim": "official_admission",
            "title": "官方招生计划与章程核验",
            "channel": "official_pdf",
            "priority": "P0",
            "query": f"{target_label} 招生章程 招生计划 专业组 选科要求 校区 PDF",
            "required_fields": ["来源链接", "发布日期", "学校代码", "专业组代码", "计划数", "选科要求", "校区", "原文摘录"],
            "review_action": "核验官方 PDF 或招生网页面，保留原文摘录后才能进入量化定位。",
        },
        {
            "id": "rank-history-band",
            "claim": "rank_history",
            "title": "历史位次与计划变化复核",
            "channel": "official_pdf",
            "priority": "P0",
            "query": f"{province} {school_name} {major_name} 历年投档 最低位次 计划数 {target_year - 3}-{target_year - 1}",
            "required_fields": ["年份", "最低分", "最低位次", "计划数", "第二来源", "原文摘录"],
            "review_action": "至少使用省考试院和学校来源交叉复核，不把位次外推写成录取承诺。",
        },
        {
            "id": "faculty-research-direction",
            "claim": "faculty_research",
            "title": "科研方向与课题组地图",
            "channel": "public_web",
            "priority": "P0",
            "query": f"{school_name} {major_name} 学院 实验室 导师 课题组 科研方向",
            "required_fields": ["导师", "实验室", "研究方向", "项目场景", "近三年动态", "原文摘录"],
            "review_action": "拆出真实课题组和方向，避免只引用学院宣传口号。",
        },
        {
            "id": "undergrad-access",
            "claim": "undergrad_access",
            "title": "本科生可获得性核验",
            "channel": "wechat_operator",
            "priority": "P0",
            "query": f"{school_name} {major_name} 本科生 科研训练 创新项目 竞赛队 公众号",
            "required_fields": ["入口类型", "项目名称", "学生参与方式", "年级限制", "报名方式", "原文摘录"],
            "review_action": "微信公众号和半封闭材料只生成合规人工采集任务，不绕过登录、付费或平台限制。",
        },
        {
            "id": "employment-market",
            "claim": "employment_market",
            "title": "国内岗位样本与真实就业锚点",
            "channel": "job_market_operator",
            "priority": "P0",
            "query": f"{major_name} {school_name} Boss直聘 国企 校招 岗位 技能 学历门槛",
            "required_fields": ["岗位名", "城市", "学历要求", "技能栏", "工作内容", "薪资口径", "来源链接", "原文摘录"],
            "review_action": "招聘平台只做人可见样本记录，不绕过平台限制，也不把岗位样本写成就业确定性。",
        },
        {
            "id": "graduate-progression",
            "claim": "graduate_progression",
            "title": "考研与保研路径核验",
            "channel": "public_web",
            "priority": "P1",
            "query": f"{school_name} {major_name} 保研 去向 考研 研究生 招生目录 课程 项目经历",
            "required_fields": ["去向类型", "目标学科", "保研/考研要求", "项目经历", "课程要求", "原文摘录"],
            "review_action": "只在能连接课程、项目和导师方向时支持中期升学判断。",
        },
        {
            "id": "civil-service-path",
            "claim": "civil_service_path",
            "title": "考公与选调岗位现实核验",
            "channel": "public_web",
            "priority": "P2",
            "query": f"{major_name} 国考 省考 选调 岗位表 专业限制 工学",
            "required_fields": ["公告年份", "岗位类别", "专业限制", "学历限制", "地区", "竞争口径", "原文摘录"],
            "review_action": "考公路径只能作为弱备选，必须说明专业限制和不限专业比例。",
        },
        {
            "id": "counter-evidence",
            "claim": "counter_evidence",
            "title": "反证降权检查",
            "channel": "manual_review",
            "priority": "P0",
            "query": f"{target_label} 调剂风险 黑名单 校区冲突 投诉 培养方案 断档",
            "required_fields": ["反证类型", "命中证据", "影响范围", "降权动作", "是否阻断推荐", "原文摘录"],
            "review_action": "先查不利证据；任何 P0 反证命中都必须降权或阻断推荐。",
        },
    ]


PLAN_PROMPT = """你是研究规划专家，需要把一个复杂问题拆成可搜索、可验证的子问题。

研究主题：
{research_topic}

请输出 2 到 4 个子问题，要求：
1. 每个子问题都应便于通过搜索工具和公开资料验证。
2. 优先拆出与官方要求、量化数据、风险提示相关的内容。
3. 子问题之间尽量互补，不要只是换一种说法。
"""


REFLECT_PROMPT = """你是研究质量评估专家，需要判断当前信息是否足以支持后续决策。

研究主题：
{research_topic}

当前已收集信息：
{search_results}

请判断：
1. 当前信息是否足够；
2. 还缺什么；
3. 信息密度大致是多少（0 到 1）；
4. 给出简短理由。
"""


SYNTHESIZE_PROMPT = """你是研究报告撰写专家，请基于以下材料生成一份简洁、结构化的调研报告。

研究主题：
{research_topic}

当前已收集信息：
{search_results}

请使用 Markdown 输出，至少包含：
1. 核心结论
2. 关键事实或数据
3. 风险与不确定性
4. 后续建议
"""


def _fallback_sub_questions(research_topic: str) -> List[str]:
    topic = research_topic.strip()
    if not topic:
        return []
    return [
        f"{topic}：核心事实和官方要求是什么？",
        f"{topic}：近年录取、培养或就业信息有哪些？",
        f"{topic}：当前决策最需要关注的风险与限制是什么？",
    ]


def _fallback_search_result(question: str) -> str:
    return (
        f"\n### 关于“{question}”的调研提纲\n"
        "- 当前未完成外部网络检索，以下结果仅作为后续人工核验提纲。\n"
        "- 建议优先核查院校官网、招生章程、培养方案、就业质量报告和近年录取数据。\n"
        "- 补充官方来源、时间戳和具体数字后，再进入最终决策。\n"
    )


def _source_type_from_url(url: str) -> tuple[str, float]:
    host = urlparse(url).netloc.lower()
    if not host:
        return "unknown", 0.30
    official_markers = (".edu.cn", ".edu", ".gov.cn", ".gov", "zs.", "admission", "招生")
    semi_official = ("gaokao", "eol.cn", "chsi.com.cn", "阳光高考", "考试院")
    if any(marker in host for marker in official_markers):
        return "official_or_school", 0.86
    if any(marker.lower() in host for marker in semi_official):
        return "semi_official_aggregator", 0.72
    if any(marker in host for marker in ("weixin", "zhihu", "bilibili", "douyin", "toutiao")):
        return "social_media", 0.42
    return "web_search", 0.55


def _evidence_card_from_search_result(question: str, result: dict[str, Any]) -> EvidenceCard:
    url = str(result.get("url") or "")
    title = str(result.get("title") or "Source").strip()
    content = str(result.get("content") or "").strip()
    score = result.get("score", 0.0)
    source_type, base_confidence = _source_type_from_url(url)
    try:
        score_value = float(score or 0.0)
    except (TypeError, ValueError):
        score_value = 0.0
    confidence = min(0.95, base_confidence + min(0.08, max(0.0, score_value) * 0.04))
    claim = content[:220] if content else title
    return EvidenceCard(
        signal_type="external_research",
        source_type=source_type,
        value=0.65 if source_type in {"official_or_school", "semi_official_aggregator"} else 0.45,
        confidence=confidence,
        claim=f"{title}: {claim}",
        source=url,
        cutoff_date="runtime_search",
        usable_for_prediction=source_type in {"official_or_school", "semi_official_aggregator"},
    )


def _fallback_evidence_card(question: str) -> dict:
    return EvidenceCard(
        signal_type="research_todo",
        source_type="manual_verification_required",
        value=0.0,
        confidence=0.20,
        claim=f"Fallback research outline for: {question}. Official source verification is still required.",
        source="fallback_no_web_search",
        cutoff_date="runtime_fallback",
        usable_for_prediction=False,
    ).to_dict()


def _evidence_appendix(cards: List[dict]) -> str:
    if not cards:
        return "\n\n## 引用与证据附录\n\n- 当前报告没有结构化证据卡，必须人工补充官方来源后再用于最终决策。\n"
    lines = ["", "## 引用与证据附录", ""]
    for index, card in enumerate(cards[:12], 1):
        usable = "可用于预测" if card.get("usable_for_prediction") else "仅供参考/待核验"
        source = card.get("source") or "unknown"
        lines.append(
            f"{index}. `{card.get('source_type', 'unknown')}` {usable}；"
            f"confidence={float(card.get('confidence', 0.0)):.2f}；"
            f"{card.get('claim', '')}；source: {source}"
        )
    return "\n".join(lines) + "\n"


def _heuristic_information_density(search_results: List[str]) -> float:
    valid_results = [result for result in search_results if result and result.strip()]
    if not valid_results:
        return 0.0
    avg_length = sum(len(item) for item in valid_results) / len(valid_results)
    hint_count = sum(item.count("http") + item.count("官网") + item.count("章程") for item in valid_results)
    density = 0.25 + min(0.35, avg_length / 1200.0) + min(0.25, hint_count * 0.04)
    return max(0.0, min(1.0, density))


def _fallback_report(research_topic: str, search_results: List[str], knowledge_gaps: List[str]) -> str:
    key_points: List[str] = []
    for block in search_results[:4]:
        for line in block.splitlines():
            line = line.strip()
            if not line or line.startswith("###"):
                continue
            if len(line) < 8:
                continue
            key_points.append(line[:160])
            if len(key_points) >= 6:
                break
        if len(key_points) >= 6:
            break

    if not key_points:
        key_points.append("当前缺少足够的外部检索结果，建议优先补充官方来源和定量证据。")

    pending_items = knowledge_gaps[:5] if knowledge_gaps else ["仍需补充更高置信度的官方来源和具体数字。"]
    sections = [
        f"# 深度调研报告：{research_topic}",
        "",
        "## 核心结论",
        "当前调研链已完成基础问题拆解，但部分结论仍需结合官方来源进一步核验。",
        "",
        "## 关键发现",
    ]
    sections.extend([f"- {point}" for point in key_points])
    sections.extend(["", "## 待补充信息"])
    sections.extend([f"- {item}" for item in pending_items])
    sections.extend(
        [
            "",
            "## 建议",
            "- 若需要最终志愿表，建议回到量化推荐链并结合位次、招生计划和录取概率做交叉验证。",
            "- 对高风险结论，优先以院校官网、招生章程和当年招生计划为准。",
        ]
    )
    return "\n".join(sections)


def plan_research(state: DeepResearchState) -> dict:
    """Plan sub-questions for the deep research loop."""
    print("[Deep Research - Plan] starting research planning...")

    research_topic = state.get("research_topic", "")
    if not research_topic:
        return {"debug_logs": ["[ERROR] Plan: missing research topic"]}

    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(SubQuestionList)
    prompt = PLAN_PROMPT.format(research_topic=research_topic)

    try:
        result: SubQuestionList = structured_llm.invoke(prompt)
        sub_questions = result.questions or _fallback_sub_questions(research_topic)
        debug_logs = [f"[PLAN] generated {len(sub_questions)} sub-questions"]
        for index, question in enumerate(sub_questions, 1):
            debug_logs.append(f"[PLAN]   {index}. {question}")
        return {"sub_questions": sub_questions, "debug_logs": debug_logs}
    except Exception as exc:
        fallback_questions = _fallback_sub_questions(research_topic) or [research_topic]
        return {
            "sub_questions": fallback_questions,
            "debug_logs": [f"[WARN] Plan fell back to heuristic sub-questions: {exc}"],
        }


def execute_research(state: DeepResearchState) -> dict:
    """Execute web search or a fallback local evidence-collection stub."""
    print("[Deep Research - Execute] executing search...")

    sub_questions = state.get("sub_questions", [])
    if not sub_questions:
        return {"debug_logs": ["[ERROR] Execute: missing sub-questions"]}

    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    search_tool = None
    debug_logs = ["[EXECUTE] starting evidence collection"]
    if tavily_key:
        try:
            search_tool = TavilySearchResults(max_results=3)
        except Exception as exc:
            debug_logs.append(f"[EXECUTE] Tavily init failed, switching to fallback mode: {exc}")
    else:
        debug_logs.append("[EXECUTE] TAVILY_API_KEY missing, using fallback research mode")

    all_results: List[str] = []
    all_queries: List[str] = []
    all_evidence_cards: List[dict] = []

    for index, question in enumerate(sub_questions, 1):
        all_queries.append(question)
        try:
            debug_logs.append(f"[EXECUTE]   {index}/{len(sub_questions)} query: {question}")
            if search_tool is None:
                all_results.append(_fallback_search_result(question))
                all_evidence_cards.append(_fallback_evidence_card(question))
                debug_logs.append("[EXECUTE]   fallback result generated")
                continue

            results = search_tool.invoke(question)
            formatted_results = [f"\n### 关于“{question}”的搜索结果"]
            for result in results:
                content = result.get("content", "")
                url = result.get("url", "")
                title = result.get("title", "Source")
                formatted_results.append(f"- {content} ([{title}]({url}))")
                all_evidence_cards.append(_evidence_card_from_search_result(question, result).to_dict())
            all_results.append("\n".join(formatted_results))
            debug_logs.append(f"[EXECUTE]   collected {len(results)} results")
        except Exception as exc:
            all_results.append(_fallback_search_result(question))
            all_evidence_cards.append(_fallback_evidence_card(question))
            debug_logs.append(f"[WARN] Execute fallback for '{question}': {exc}")

    return {
        "search_results": all_results,
        "search_queries": all_queries,
        "research_evidence_cards": all_evidence_cards,
        "debug_logs": debug_logs,
    }


def reflect_research(state: DeepResearchState) -> dict:
    """Estimate whether current evidence is sufficient."""
    print("[Deep Research - Reflect] checking evidence sufficiency...")

    research_topic = state.get("research_topic", "")
    search_results = state.get("search_results", [])
    evidence_cards = state.get("research_evidence_cards", [])
    loop_count = state.get("research_loop_count", 0) + 1
    max_loops = state.get("max_research_loops", 2)

    if not search_results:
        return {
            "is_sufficient": False,
            "knowledge_gaps": ["缺少搜索结果"],
            "information_density": 0.0,
            "research_loop_count": loop_count,
            "debug_logs": ["[REFLECT] no search results found"],
        }

    llm = get_llm(temperature=0.3)
    structured_llm = llm.with_structured_output(ReflectionResult)
    prompt = REFLECT_PROMPT.format(
        research_topic=research_topic,
        search_results="\n---\n".join(search_results),
    )

    try:
        result: ReflectionResult = structured_llm.invoke(prompt)
        is_sufficient = result.is_sufficient or loop_count >= max_loops
        debug_logs = [
            f"[REFLECT] loop={loop_count}/{max_loops}",
            f"[REFLECT] density={result.information_density:.2f}",
            f"[REFLECT] reasoning={result.reasoning}",
        ]
        for gap in result.knowledge_gaps:
            debug_logs.append(f"[REFLECT] gap: {gap}")
        return {
            "is_sufficient": is_sufficient,
            "knowledge_gaps": result.knowledge_gaps,
            "information_density": result.information_density,
            "research_loop_count": loop_count,
            "debug_logs": debug_logs,
        }
    except Exception as exc:
        density = _heuristic_information_density(search_results)
        return {
            "is_sufficient": density >= 0.6 or loop_count >= max_loops,
            "knowledge_gaps": [] if density >= 0.6 else ["仍缺少高置信度官方数据或定量证据"],
            "information_density": density,
            "research_loop_count": loop_count,
            "debug_logs": [f"[WARN] Reflect fell back to heuristic density estimation: {exc}"],
        }


def synthesize_report(state: DeepResearchState) -> dict:
    """Generate the final research report."""
    print("[Deep Research - Synthesize] generating report...")

    research_topic = state.get("research_topic", "")
    search_results = state.get("search_results", [])
    evidence_cards = state.get("research_evidence_cards", [])

    if not search_results:
        return {
            "research_report": f"# 深度调研报告：{research_topic}\n\n当前未检索到有效信息。",
            "debug_logs": ["[SYNTHESIZE] generated empty fallback report"],
        }

    llm = get_llm(temperature=0.5)
    prompt = SYNTHESIZE_PROMPT.format(
        research_topic=research_topic,
        search_results="\n---\n".join(search_results),
    )

    try:
        result = llm.invoke(prompt)
        report = str(result.content).rstrip() + _evidence_appendix(evidence_cards)
        return {
            "research_report": report,
            "debug_logs": [f"[SYNTHESIZE] generated report length={len(report)}"],
        }
    except Exception as exc:
        fallback = _fallback_report(
            research_topic,
            search_results,
            state.get("knowledge_gaps", []),
        ).rstrip() + _evidence_appendix(evidence_cards)
        return {
            "research_report": fallback,
            "debug_logs": [f"[WARN] Synthesize fell back to structured local report: {exc}"],
        }


def should_continue_research(state: DeepResearchState) -> str:
    """Route either back to planning or to report synthesis."""
    return "synthesize" if state.get("is_sufficient", False) else "plan"
