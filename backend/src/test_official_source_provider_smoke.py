"""Smoke tests for the narrow official-source provider."""

from __future__ import annotations

from evidence_autopilot_api import (
    EvidenceAutopilotEvidenceCard,
    EvidenceAutopilotResearchRequest,
    build_evidence_autopilot_research_response,
)
from official_source_provider import (
    ScutOfficialAdmissionPlanProvider,
    ScutOfficialAdmissionScoreProvider,
    ScutOfficialMajorProfileProvider,
    capture_official_source_evidence,
    parse_scut_admission_score_rows,
)


SCUT_SCORE_HTML = """
<table class="cq_resultTable">
  <tr>
    <th>年份</th><th>省份</th><th>类别</th><th>科类名称</th>
    <th>专业名称</th><th>最高分</th><th>最低分</th><th>平均分</th>
  </tr>
  <tr>
    <td>2025</td><td>广东</td><td>普通类</td><td>理工/物理类</td>
    <td>计算机类</td><td>650</td><td>635</td><td>641.2</td>
  </tr>
  <tr>
    <td>2025</td><td>广东</td><td>普通类</td><td>理工/物理类</td>
    <td>工科试验班(智能装备与先进制造)</td><td>644</td><td>629</td><td>631.9</td>
  </tr>
</table>
"""

SCUT_PLAN_HTML = """
<html><body>
2026年我校普通类继续实施并升级报满6个不同专业志愿零调剂、大类分流100%任选、
转专业不限成功次数、辅修专业零壁垒和推免不限校内外等一系列改革政策。
2026年招生专业和分组进一步优化，2025年录取分数仅供了解。
</body></html>
"""

SCUT_CHARTER_HTML = """
<html><body>
华南理工大学2026年本科招生章程。
平行志愿批次普通类考生调档后，服从调剂且符合专业录取要求者不退档。
学校按投档分数优先的原则从高到低进行专业录取，尊重考生所填的专业志愿顺序，
不设置专业志愿级差。
</body></html>
"""

SCUT_MAJOR_PROFILE_HTML = """
<html><body>
智能制造工程专业是人工智能与高端制造的强交叉学科。
核心课程：人工智能技术及应用、工业大数据分析及应用、制造系统分析及应用、机电一体化。
目前学院在师资建设方面发挥了学科交叉融合特色，已引进具有人工智能、机器人工程、
智能制造、物联网、控制工程、柔性电子、计算机等不同研究领域的青年海外人才二十余人。
学院建立了面向本科生创新创业实践的机器人实验室1间、智能制造实验室1间、3D打印实验室2间。
学院将科研平台全部面向本科生开放，通过强化科研渗透教学，平台建设支撑人才培养。
</body></html>
"""

SCUT_ADMISSIONS_PROFILE_HTML = """
<html><body>
智能制造工程专业是面向智能工程前沿高新技术及其应用的专业性本科专业。
学生毕业后可到高校科研机构、相关企事业单位、政府机关等从事相关领域的研发、管理工作，
也可以继续深造，攻读机器人工程、智能制造及相关学科的研究生。
</body></html>
"""


def test_parse_scut_admission_score_rows_extracts_target_row() -> None:
    rows = parse_scut_admission_score_rows(SCUT_SCORE_HTML)

    target = next(row for row in rows if "智能装备" in row["major_name"])
    assert target == {
        "year": "2025",
        "province": "广东",
        "category": "普通类",
        "subject": "理工/物理类",
        "major_name": "工科试验班(智能装备与先进制造)",
        "max_score": "644",
        "min_score": "629",
        "avg_score": "631.9",
    }


def test_scut_provider_builds_captured_candidate_card_from_official_html() -> None:
    provider = ScutOfficialAdmissionScoreProvider(fetch_html=lambda: SCUT_SCORE_HTML)
    cards = provider.capture(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        )
    )

    assert len(cards) == 1
    card = cards[0]
    assert card.taskId == "rank-history-band"
    assert card.status == "captured_candidate"
    assert card.sourceType == "official"
    assert card.confidence == "high"
    assert card.sourceUrl == "https://admission.scut.edu.cn/30821/list.htm"
    assert "highest 644, lowest 629, average 631.9" in card.excerpt
    assert "does not prove 2026 admission probability" in card.reviewAction


def test_scut_plan_provider_builds_plan_and_charter_card() -> None:
    provider = ScutOfficialAdmissionPlanProvider(
        fetch_plan_html=lambda: SCUT_PLAN_HTML,
        fetch_charter_html=lambda: SCUT_CHARTER_HTML,
    )
    cards = provider.capture(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        )
    )

    assert len(cards) == 1
    card = cards[0]
    assert card.taskId == "official-plan-charter"
    assert card.status == "captured_candidate"
    assert card.sourceType == "official"
    assert card.confidence == "high"
    assert card.sourceUrl == "https://xxgk.scut.edu.cn/2026/0528/c132a48854/page.htm"
    assert "majors/groups are further optimized" in card.excerpt
    assert "score-priority admission" in card.excerpt
    assert "does not prove admission probability" in card.reviewAction


def test_scut_major_profile_provider_builds_training_access_and_progression_cards() -> None:
    provider = ScutOfficialMajorProfileProvider(
        fetch_major_html=lambda: SCUT_MAJOR_PROFILE_HTML,
        fetch_admissions_html=lambda: SCUT_ADMISSIONS_PROFILE_HTML,
    )
    cards = provider.capture(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        )
    )

    cards_by_task = {card.taskId: card for card in cards}
    assert set(cards_by_task) == {
        "faculty-research-direction",
        "undergrad-access",
        "graduate-progression",
    }
    assert cards_by_task["faculty-research-direction"].sourceType == "school"
    assert "AI, industrial big data, and manufacturing systems courses" in cards_by_task["faculty-research-direction"].excerpt
    assert "research platforms are open to undergraduates" in cards_by_task["undergrad-access"].excerpt
    assert "graduate study in robotics and intelligent manufacturing" in cards_by_task["graduate-progression"].excerpt
    assert "does not prove graduate-school or employment outcomes" in cards_by_task["graduate-progression"].reviewAction


def test_research_response_can_opt_into_official_source_provider() -> None:
    provider = ScutOfficialAdmissionScoreProvider(fetch_html=lambda: SCUT_SCORE_HTML)
    response = build_evidence_autopilot_research_response(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        ),
        official_source_provider=provider,
    )

    captured = [card for card in response.evidenceCards if card.status == "captured_candidate"]
    assert len(captured) == 1
    assert captured[0].taskId == "rank-history-band"
    assert any(card.status == "requires_capture" for card in response.evidenceCards)
    assert "Live official-source provider captured public evidence" in response.claimBoundary
    assert "score evidence remains historical context only" in response.claimBoundary


def test_research_response_merges_plan_and_score_official_providers() -> None:
    response = build_evidence_autopilot_research_response(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        ),
        official_source_providers=[
            ScutOfficialAdmissionPlanProvider(
                fetch_plan_html=lambda: SCUT_PLAN_HTML,
                fetch_charter_html=lambda: SCUT_CHARTER_HTML,
            ),
            ScutOfficialAdmissionScoreProvider(fetch_html=lambda: SCUT_SCORE_HTML),
        ],
    )

    captured_by_task = {
        card.taskId: card for card in response.evidenceCards if card.status == "captured_candidate"
    }
    assert set(captured_by_task) == {"official-plan-charter", "rank-history-band"}
    assert "majors/groups are further optimized" in captured_by_task["official-plan-charter"].excerpt
    assert "highest 644, lowest 629, average 631.9" in captured_by_task["rank-history-band"].excerpt


def test_research_response_merges_all_scut_live_school_and_official_providers() -> None:
    response = build_evidence_autopilot_research_response(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        ),
        official_source_providers=[
            ScutOfficialAdmissionPlanProvider(
                fetch_plan_html=lambda: SCUT_PLAN_HTML,
                fetch_charter_html=lambda: SCUT_CHARTER_HTML,
            ),
            ScutOfficialAdmissionScoreProvider(fetch_html=lambda: SCUT_SCORE_HTML),
            ScutOfficialMajorProfileProvider(
                fetch_major_html=lambda: SCUT_MAJOR_PROFILE_HTML,
                fetch_admissions_html=lambda: SCUT_ADMISSIONS_PROFILE_HTML,
            ),
        ],
    )

    captured_tasks = {
        card.taskId for card in response.evidenceCards if card.status == "captured_candidate"
    }
    assert captured_tasks >= {
        "official-plan-charter",
        "rank-history-band",
        "faculty-research-direction",
        "undergrad-access",
        "graduate-progression",
    }


class StaticOfficialProvider:
    """Test provider that returns one reviewed official card."""

    def capture(
        self,
        request: EvidenceAutopilotResearchRequest,
    ) -> list[EvidenceAutopilotEvidenceCard]:
        return [
            EvidenceAutopilotEvidenceCard(
                taskId="official-plan-charter",
                claim="official_admission",
                status="captured_candidate",
                sourceTitle="Official static source",
                sourceUrl="https://example.edu/official",
                sourceType="official",
                excerpt=f"Official source captured for {request.schoolName}.",
                capturedAt="2026-06-24",
                confidence="high",
                reviewAction="Use as official source evidence only; do not infer admission outcomes.",
            )
        ]


class FailingOfficialProvider:
    """Test provider that simulates a network or parser failure."""

    def capture(
        self,
        request: EvidenceAutopilotResearchRequest,
    ) -> list[EvidenceAutopilotEvidenceCard]:
        raise RuntimeError("official source timeout")


class ExplodingIfCalledProvider:
    """Test provider that proves default requests do not touch live providers."""

    def capture(
        self,
        request: EvidenceAutopilotResearchRequest,
    ) -> list[EvidenceAutopilotEvidenceCard]:
        raise AssertionError("provider should not be called without opt-in")


def test_capture_official_source_evidence_merges_cards_and_warnings() -> None:
    request = EvidenceAutopilotResearchRequest(
        province="Guangdong",
        schoolName="South China University of Technology",
        majorName="intelligent manufacturing / data engineering opportunity path",
        targetYear=2026,
        enableOfficialSourceProvider=True,
    )

    result = capture_official_source_evidence(
        request,
        providers=[FailingOfficialProvider(), StaticOfficialProvider()],
    )

    assert [card.taskId for card in result.cards] == ["official-plan-charter"]
    assert result.warnings == ["FailingOfficialProvider: official source timeout"]


def test_research_response_isolates_official_source_provider_failures() -> None:
    response = build_evidence_autopilot_research_response(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
            enableOfficialSourceProvider=True,
        ),
        official_source_providers=[FailingOfficialProvider(), StaticOfficialProvider()],
    )

    captured = [card for card in response.evidenceCards if card.status == "captured_candidate"]
    assert len(captured) == 1
    assert captured[0].taskId == "official-plan-charter"
    assert any(card.taskId == "rank-history-band" and card.status == "requires_capture" for card in response.evidenceCards)
    assert "Live official-source provider captured public evidence" in response.claimBoundary
    assert "Official-source provider warning: FailingOfficialProvider: official source timeout" in response.claimBoundary


def test_research_response_does_not_call_provider_without_opt_in() -> None:
    response = build_evidence_autopilot_research_response(
        EvidenceAutopilotResearchRequest(
            province="Guangdong",
            schoolName="South China University of Technology",
            majorName="intelligent manufacturing / data engineering opportunity path",
            targetYear=2026,
        ),
        official_source_providers=[ExplodingIfCalledProvider()],
    )

    statuses = {card.status for card in response.evidenceCards}
    assert statuses <= {"requires_capture", "operator_review"}
