"""Smoke tests for the narrow official-source provider."""

from __future__ import annotations

from evidence_autopilot_api import (
    EvidenceAutopilotResearchRequest,
    build_evidence_autopilot_research_response,
)
from official_source_provider import (
    ScutOfficialAdmissionScoreProvider,
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
    assert "Live official-source provider captured public score evidence" in response.claimBoundary
