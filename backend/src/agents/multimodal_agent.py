"""Multimodal Agent：整合 PDF 解析和 Vision 分析"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage

from models.state import SupervisorState
from models.user_profile import UserProfile
from tools.pdf_parser import PDFParser, parse_health_restriction
from tools.vision_analyzer import VisionAnalyzer, check_health_restriction_with_vision
from utils.llm_factory import get_llm


class HealthRestrictionQuery(BaseModel):
    """体检限制查询结果"""
    school_name: str = Field(description="学校名称")
    condition: str = Field(description="体检条件（如色弱、色盲）")
    has_restriction: bool = Field(description="是否有限制")
    text_analysis: str = Field(description="文本分析结果")
    vision_analysis: Optional[str] = Field(default=None, description="视觉分析结果")
    restricted_majors: List[str] = Field(default_factory=list, description="受限专业列表")
    severity: str = Field(description="限制严重程度：无/轻度/中度/严重")


class MultimodalAnalysisResult(BaseModel):
    """多模态分析结果"""
    query_type: str = Field(description="查询类型：health_restriction / admission_rules / fees")
    schools_analyzed: List[str] = Field(description="已分析的学校列表")
    findings: List[HealthRestrictionQuery] = Field(description="发现的限制")
    summary: str = Field(description="总结")
    sources: List[str] = Field(description="数据来源（PDF路径）")


def multimodal_agent_node(state: SupervisorState) -> dict:
    """
    Multimodal Agent 节点：处理多模态查询（PDF + Vision）

    职责：
    1. 解析用户查询，提取目标学校和查询类型
    2. 使用 PDF Parser 进行文本分析
    3. 使用 Vision Analyzer 进行图表识别
    4. 整合结果，返回结构化答案
    """
    print("[Multimodal Agent] 启动多模态分析...")

    # === 步骤 1：提取查询信息 ===
    messages = state.get("messages", [])
    if not messages:
        return {
            "current_agent": "multimodal_agent",
            "debug_logs": ["[ERROR] Multimodal: 缺少消息"],
            "messages": [AIMessage(content="错误：缺少查询信息")]
        }

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    user_profile: Optional[UserProfile] = state.get("user_profile")

    print(f"[Multimodal] 用户查询: {user_message}")

    # === 步骤 2：分析查询类型 ===
    llm = get_llm(temperature=0)

    analysis_prompt = f"""分析以下用户查询，判断查询类型和目标学校。

用户查询：{user_message}

用户画像：{user_profile if user_profile else "无"}

请回答：
1. 查询类型（health_restriction / admission_rules / fees / other）
2. 目标学校（如果有多个，列出所有）
3. 具体查询内容（如"色弱是否受限"、"单科成绩要求"等）

格式：
查询类型: xxx
目标学校: [学校1, 学校2]
具体内容: xxx
"""

    try:
        analysis = llm.invoke(analysis_prompt)
        analysis_text = analysis.content

        print(f"[Multimodal] LLM 分析结果:\n{analysis_text}")

        # 简单解析（生产环境应使用 structured output）
        query_type = "health_restriction"  # 默认
        target_schools = []
        query_content = user_message

        if "体检" in user_message or "色" in user_message or "视力" in user_message:
            query_type = "health_restriction"
        elif "录取规则" in user_message or "调剂" in user_message:
            query_type = "admission_rules"
        elif "学费" in user_message or "费用" in user_message:
            query_type = "fees"

        # 提取目标学校（简单实现）
        if user_profile and user_profile.preferred_schools:
            target_schools = user_profile.preferred_schools
        else:
            # 从用户消息中提取学校名（简单匹配）
            # 这里应该用 NER，暂时简化
            target_schools = ["清华大学"]  # Placeholder

    except Exception as e:
        print(f"[ERROR] Multimodal 分析失败: {e}")
        return {
            "current_agent": "multimodal_agent",
            "debug_logs": [f"[ERROR] Multimodal 分析失败: {e}"],
            "messages": [AIMessage(content=f"多模态分析失败：{e}")]
        }

    # === 步骤 3：执行多模态分析 ===
    if query_type == "health_restriction":
        result = analyze_health_restrictions(
            target_schools=target_schools,
            user_message=user_message,
            user_profile=user_profile
        )
    elif query_type == "admission_rules":
        result = analyze_admission_rules(target_schools)
    else:
        result = {
            "summary": f"暂不支持查询类型：{query_type}",
            "findings": []
        }

    # === 步骤 4：返回结果 ===
    summary = result.get("summary", "")
    findings = result.get("findings", [])
    sources = result.get("sources", [])

    return {
        "vision_results": [summary] + [str(f) for f in findings],
        "pdf_sources": sources,
        "loop_history": ["multimodal"],
        "current_agent": "multimodal_agent",
        "debug_logs": [
            f"[Multimodal] 查询类型: {query_type}",
            f"[Multimodal] 分析学校: {target_schools}",
            f"[Multimodal] 找到 {len(findings)} 条结果"
        ],
        "messages": [AIMessage(content=f"# 多模态分析结果\n\n{summary}")]
    }


def analyze_health_restrictions(
    target_schools: List[str],
    user_message: str,
    user_profile: Optional[UserProfile]
) -> Dict:
    """
    分析体检限制（核心逻辑）

    流程：
    1. 提取用户体检条件（如"色弱"）
    2. 查找目标学校的 PDF
    3. 文本分析 + Vision 分析
    4. 整合结果
    """
    # 提取体检条件
    conditions = extract_health_conditions(user_message)

    if not conditions:
        conditions = ["色弱", "色盲"]  # 默认查询常见限制

    print(f"[Multimodal] 体检条件: {conditions}")

    # 初始化工具
    pdf_parser = PDFParser(pdf_dir="data/pdfs")

    findings = []
    sources = []

    for school in target_schools:
        print(f"[Multimodal] 分析学校: {school}")

        # 查找 PDF
        pdf_path = pdf_parser.find_school_pdf(school)

        if not pdf_path:
            print(f"[WARN] 未找到 {school} 的招生章程 PDF")
            continue

        sources.append(pdf_path)

        for condition in conditions:
            # === 方法 1：文本分析 ===
            text_result = parse_health_restriction(school, pdf_dir="data/pdfs")
            text_analysis = text_result.get("content", "")

            # === 方法 2：Vision 分析（如果文本中包含"表"或"图"）===
            vision_analysis = None
            has_restriction_from_vision = False

            if "表" in text_analysis or "图" in text_analysis:
                print(f"[Multimodal] 检测到表格，启动 Vision 分析...")
                try:
                    vision_result = check_health_restriction_with_vision(
                        pdf_path,
                        condition=condition,
                        page_numbers=None  # 分析所有页
                    )
                    vision_analysis = vision_result.get("details", "")
                    has_restriction_from_vision = vision_result.get("has_restriction", False)
                except Exception as e:
                    print(f"[WARN] Vision 分析失败: {e}")
                    vision_analysis = f"Vision 分析失败：{e}"

            # === 整合结果 ===
            has_restriction = (
                condition in text_analysis or
                has_restriction_from_vision
            )

            # 提取受限专业（简单实现）
            restricted_majors = extract_restricted_majors(text_analysis, vision_analysis)

            # 判断严重程度
            severity = judge_severity(has_restriction, restricted_majors)

            finding = HealthRestrictionQuery(
                school_name=school,
                condition=condition,
                has_restriction=has_restriction,
                text_analysis=text_analysis[:500],  # 限制长度
                vision_analysis=vision_analysis[:500] if vision_analysis else None,
                restricted_majors=restricted_majors,
                severity=severity
            )

            findings.append(finding)

    # 生成总结
    summary = generate_summary(findings)

    return {
        "summary": summary,
        "findings": findings,
        "sources": sources
    }


def analyze_admission_rules(target_schools: List[str]) -> Dict:
    """分析录取规则"""
    pdf_parser = PDFParser(pdf_dir="data/pdfs")

    findings = []
    sources = []

    for school in target_schools:
        pdf_path = pdf_parser.find_school_pdf(school)
        if not pdf_path:
            continue

        sources.append(pdf_path)

        # 提取录取规则段落
        rules_text = pdf_parser.extract_admission_rules(pdf_path)

        findings.append({
            "school": school,
            "rules": rules_text[:1000]
        })

    summary = f"分析了 {len(findings)} 所学校的录取规则"

    return {
        "summary": summary,
        "findings": findings,
        "sources": sources
    }


# === 辅助函数 ===
def extract_health_conditions(text: str) -> List[str]:
    """从文本中提取体检条件"""
    conditions = []
    keywords = {
        "色弱": "色弱",
        "色盲": "色盲",
        "视力": "视力",
        "近视": "近视",
        "身高": "身高",
        "听力": "听力"
    }

    for key, value in keywords.items():
        if key in text:
            conditions.append(value)

    return conditions


def extract_restricted_majors(text_analysis: str, vision_analysis: Optional[str]) -> List[str]:
    """提取受限专业"""
    majors = []

    combined_text = text_analysis
    if vision_analysis:
        combined_text += " " + vision_analysis

    # 简单匹配（生产环境应使用 NER）
    major_keywords = [
        "计算机", "软件工程", "电子信息", "化工", "生物",
        "医学", "护理", "交通运输", "飞行"
    ]

    for keyword in major_keywords:
        if keyword in combined_text:
            majors.append(keyword)

    return majors


def judge_severity(has_restriction: bool, restricted_majors: List[str]) -> str:
    """判断限制严重程度"""
    if not has_restriction:
        return "无"
    elif len(restricted_majors) == 0:
        return "轻度"
    elif len(restricted_majors) <= 3:
        return "中度"
    else:
        return "严重"


def generate_summary(findings: List[HealthRestrictionQuery]) -> str:
    """生成总结报告"""
    if not findings:
        return "未找到相关信息"

    summary = "# 体检限制分析报告\n\n"

    for finding in findings:
        summary += f"## {finding.school_name} - {finding.condition}\n\n"
        summary += f"- **是否受限**: {'是' if finding.has_restriction else '否'}\n"
        summary += f"- **严重程度**: {finding.severity}\n"

        if finding.restricted_majors:
            summary += f"- **受限专业**: {', '.join(finding.restricted_majors)}\n"

        summary += "\n"

        if finding.vision_analysis:
            summary += "### 图表识别结果\n"
            summary += f"{finding.vision_analysis}\n\n"

    return summary
