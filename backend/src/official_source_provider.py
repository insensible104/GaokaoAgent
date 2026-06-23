"""Official-source providers for Evidence Autopilot."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Protocol
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from evidence_autopilot_api import (
        EvidenceAutopilotEvidenceCard,
        EvidenceAutopilotResearchRequest,
    )


SCUT_SCORE_PARENT_URL = "https://admission.scut.edu.cn/30821/list.htm"
SCUT_PLAN_URL = "https://admission.scut.edu.cn/30820/list.htm"
SCUT_CHARTER_2026_URL = "https://xxgk.scut.edu.cn/2026/0528/c132a48854/page.htm"
SCUT_SCORE_QUERY_URL = (
    "https://admission.scut.edu.cn/_web/_apps/commonquery/commonquery/api/"
    "commonqueryCacheResult/16.rst?_p=YXM9MzQ4JnQ9MTcyMyZwPTEmbT1OJg__"
    "&mobileTemplate=false&cq16s188=2025&cq16s189=%25E5%25B9%25BF%25E4%25B8%259C"
    "&cq16s190=%25E6%2599%25AE%25E9%2580%259A%25E7%25B1%25BB"
    "&cq16s191=%25E7%2590%2586%25E5%25B7%25A5%2F%25E7%2589%25A9%25E7%2590%2586%25E7%25B1%25BB"
)


class OfficialSourceProvider(Protocol):
    """Contract for official-source evidence capture providers."""

    def capture(
        self,
        request: "EvidenceAutopilotResearchRequest",
    ) -> list["EvidenceAutopilotEvidenceCard"]:
        """Capture reviewed public evidence cards for one request."""
        ...


@dataclass(frozen=True)
class OfficialSourceCaptureResult:
    """Provider-capture output with explicit failure notes."""

    cards: list["EvidenceAutopilotEvidenceCard"]
    warnings: list[str]


def capture_official_source_evidence(
    request: "EvidenceAutopilotResearchRequest",
    providers: list[OfficialSourceProvider],
) -> OfficialSourceCaptureResult:
    """Capture official-source evidence while isolating provider failures."""
    cards: list["EvidenceAutopilotEvidenceCard"] = []
    warnings: list[str] = []
    for provider in providers:
        try:
            cards.extend(provider.capture(request))
        except Exception as exc:  # noqa: BLE001 - provider failures must not break research task generation.
            warnings.append(f"{provider.__class__.__name__}: {exc}")
    return OfficialSourceCaptureResult(cards=cards, warnings=warnings)


class _TableCellParser(HTMLParser):
    """Collect text cells from simple HTML tables."""

    def __init__(self) -> None:
        super().__init__()
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._current_row = []
        if tag in {"td", "th"}:
            self._current_cell = []

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_cell is not None:
            if self._current_row is not None:
                text = " ".join(part.strip() for part in self._current_cell if part.strip())
                self._current_row.append(text)
            self._current_cell = None
        if tag == "tr" and self._current_row is not None:
            if any(cell.strip() for cell in self._current_row):
                self.rows.append(self._current_row)
            self._current_row = None


class _PlainTextParser(HTMLParser):
    """Collect readable text from official HTML pages."""

    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def _plain_text_from_html(html: str) -> str:
    parser = _PlainTextParser()
    parser.feed(html)
    return " ".join(parser.parts)


def _fetch_url_text(url: str, *, method: str = "GET") -> str:
    data = b"" if method == "POST" else None
    request = Request(
        url,
        data=data,
        headers={"User-Agent": "PathFinder Evidence Autopilot/0.1"},
        method=method,
    )
    with urlopen(request, timeout=8) as response:
        return response.read().decode("utf-8", errors="replace")


def parse_scut_admission_score_rows(html: str) -> list[dict[str, str]]:
    """Parse SCUT official admission score rows from the public result table."""
    parser = _TableCellParser()
    parser.feed(html)
    rows: list[dict[str, str]] = []
    for cells in parser.rows:
        if len(cells) < 8 or not cells[0].isdigit():
            continue
        rows.append(
            {
                "year": cells[0],
                "province": cells[1],
                "category": cells[2],
                "subject": cells[3],
                "major_name": cells[4],
                "max_score": cells[5],
                "min_score": cells[6],
                "avg_score": cells[7],
            }
        )
    return rows


class ScutOfficialAdmissionPlanProvider:
    """Capture SCUT 2026 plan and charter boundary evidence."""

    def __init__(
        self,
        fetch_plan_html: Callable[[], str] | None = None,
        fetch_charter_html: Callable[[], str] | None = None,
    ) -> None:
        self._fetch_plan_html = fetch_plan_html or (
            lambda: _fetch_url_text(SCUT_PLAN_URL)
        )
        self._fetch_charter_html = fetch_charter_html or (
            lambda: _fetch_url_text(SCUT_CHARTER_2026_URL)
        )

    def capture(
        self,
        request: "EvidenceAutopilotResearchRequest",
    ) -> list["EvidenceAutopilotEvidenceCard"]:
        """Return captured official plan and charter evidence for SCUT."""
        if not self._supports(request):
            return []

        plan_text = _plain_text_from_html(self._fetch_plan_html())
        charter_text = _plain_text_from_html(self._fetch_charter_html())
        if not self._has_plan_markers(plan_text) or not self._has_charter_markers(charter_text):
            return []

        from evidence_autopilot_api import EvidenceAutopilotEvidenceCard

        return [
            EvidenceAutopilotEvidenceCard(
                taskId="official-plan-charter",
                claim="official_admission",
                status="captured_candidate",
                sourceTitle="SCUT 2026 undergraduate admissions plan and charter",
                sourceUrl=SCUT_CHARTER_2026_URL,
                sourceType="official",
                excerpt=(
                    "SCUT 2026 admissions page says majors/groups are further optimized "
                    "and 2025 scores are reference only; 2026 charter states "
                    "score-priority admission without major-preference grade difference."
                ),
                capturedAt=date.today().isoformat(),
                confidence="high",
                reviewAction=(
                    "Use as official plan and rule evidence only; it does not prove "
                    "admission probability or final Guangdong professional-group placement."
                ),
            )
        ]

    def _supports(self, request: "EvidenceAutopilotResearchRequest") -> bool:
        province = request.province.lower()
        school = request.schoolName.lower()
        return (
            request.targetYear == 2026
            and province in {"guangdong", "广东"}
            and ("south china university of technology" in school or "华南理工" in school)
        )

    def _has_plan_markers(self, text: str) -> bool:
        return "2026年招生专业和分组进一步优化" in text and "2025年录取分数仅供了解" in text

    def _has_charter_markers(self, text: str) -> bool:
        return "按投档分数优先" in text and "不设置专业志愿级差" in text


class ScutOfficialAdmissionScoreProvider:
    """Capture SCUT historical score evidence from its official admissions site."""

    def __init__(self, fetch_html: Callable[[], str] | None = None) -> None:
        self._fetch_html = fetch_html or self._fetch_official_score_html

    def capture(
        self,
        request: "EvidenceAutopilotResearchRequest",
    ) -> list["EvidenceAutopilotEvidenceCard"]:
        """Return captured official evidence cards for a supported SCUT request."""
        if not self._supports(request):
            return []
        rows = parse_scut_admission_score_rows(self._fetch_html())
        target = next((row for row in rows if self._is_target_row(row)), None)
        if target is None:
            return []

        from evidence_autopilot_api import EvidenceAutopilotEvidenceCard

        excerpt = (
            "2025 Guangdong physics ordinary batch, "
            f"{target['major_name']}: highest {target['max_score']}, "
            f"lowest {target['min_score']}, average {target['avg_score']}."
        )
        return [
            EvidenceAutopilotEvidenceCard(
                taskId="rank-history-band",
                claim="rank_history",
                status="captured_candidate",
                sourceTitle="South China University of Technology admissions score history",
                sourceUrl=SCUT_SCORE_PARENT_URL,
                sourceType="official",
                excerpt=excerpt,
                capturedAt=date.today().isoformat(),
                confidence="high",
                reviewAction=(
                    "Use as historical score evidence only; it does not prove "
                    "2026 admission probability, rank boundary, or professional-group stability."
                ),
            )
        ]

    def _supports(self, request: "EvidenceAutopilotResearchRequest") -> bool:
        province = request.province.lower()
        school = request.schoolName.lower()
        major = request.majorName.lower()
        return (
            province in {"guangdong", "广东"}
            and ("south china university of technology" in school or "华南理工" in school)
            and (
                "intelligent" in major
                or "manufacturing" in major
                or "智能" in major
                or "制造" in major
            )
        )

    def _is_target_row(self, row: dict[str, str]) -> bool:
        return (
            row.get("year") == "2025"
            and row.get("province") == "广东"
            and row.get("category") == "普通类"
            and ("物理" in row.get("subject", "") or "理工" in row.get("subject", ""))
            and "智能装备" in row.get("major_name", "")
            and "先进制造" in row.get("major_name", "")
        )

    def _fetch_official_score_html(self) -> str:
        return _fetch_url_text(SCUT_SCORE_QUERY_URL, method="POST")
