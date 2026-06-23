"""Official-source providers for Evidence Autopilot."""

from __future__ import annotations

from collections.abc import Callable
from datetime import date
from html.parser import HTMLParser
from typing import TYPE_CHECKING
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from evidence_autopilot_api import (
        EvidenceAutopilotEvidenceCard,
        EvidenceAutopilotResearchRequest,
    )


SCUT_SCORE_PARENT_URL = "https://admission.scut.edu.cn/30821/list.htm"
SCUT_SCORE_QUERY_URL = (
    "https://admission.scut.edu.cn/_web/_apps/commonquery/commonquery/api/"
    "commonqueryCacheResult/16.rst?_p=YXM9MzQ4JnQ9MTcyMyZwPTEmbT1OJg__"
    "&mobileTemplate=false&cq16s188=2025&cq16s189=%25E5%25B9%25BF%25E4%25B8%259C"
    "&cq16s190=%25E6%2599%25AE%25E9%2580%259A%25E7%25B1%25BB"
    "&cq16s191=%25E7%2590%2586%25E5%25B7%25A5%2F%25E7%2589%25A9%25E7%2590%2586%25E7%25B1%25BB"
)


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
        request = Request(
            SCUT_SCORE_QUERY_URL,
            data=b"",
            headers={"User-Agent": "PathFinder Evidence Autopilot/0.1"},
            method="POST",
        )
        with urlopen(request, timeout=8) as response:
            return response.read().decode("utf-8", errors="replace")
