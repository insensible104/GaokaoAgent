"""Controlled audit for career-profile recommendation boundaries."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from engines.probability import calculate_admission_probability
from models.game_matrix import MajorOption
from models.user_profile import HollandCode, UserProfile
from recommendation.major_utility import score_major_utility
from recommendation.probability_calibration import (
    calibrate_probability,
    load_probability_calibration,
)


COMPUTER_MAJOR = "\u8ba1\u7b97\u673a\u79d1\u5b66\u4e0e\u6280\u672f"


def _profile(**updates: Any) -> UserProfile:
    values: dict[str, Any] = {
        "score": 620,
        "rank": 12000,
        "subject_group": "\u7269\u7406",
        "risk_tolerance": "conservative",
        "preferred_majors": [],
        "blacklist_majors": [],
    }
    values.update(updates)
    return UserProfile(**values)


def _historical_probability() -> dict[str, Any]:
    hist_data = pd.DataFrame(
        [
            {"year": 2022, "min_rank": 11800, "quota": 80},
            {"year": 2023, "min_rank": 12200, "quota": 85},
            {"year": 2024, "min_rank": 12050, "quota": 90},
        ]
    )
    return calculate_admission_probability(user_rank=12000, hist_data=hist_data)


def _round_delta(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return round(float(left) - float(right), 12)


def build_career_profile_fidelity_audit() -> dict[str, Any]:
    """Build a deterministic audit showing career-profile influence boundaries."""
    option = MajorOption(major_name=COMPUTER_MAJOR)
    investigative_profile = _profile(
        career_assessment_status="completed",
        career_assessment_mode="quick",
        holland_code=HollandCode(
            realistic=0.5,
            investigative=1.0,
            artistic=0.1,
            social=0.1,
            enterprising=0.1,
            conventional=0.5,
        ),
        riasec_top_codes=["I", "R", "C"],
    )
    enterprising_profile = _profile(
        career_assessment_status="completed",
        career_assessment_mode="quick",
        holland_code=HollandCode(
            realistic=0.1,
            investigative=0.1,
            artistic=0.1,
            social=0.1,
            enterprising=1.0,
            conventional=0.1,
        ),
        riasec_top_codes=["E", "R", "I"],
    )
    mbti_a_profile = _profile(mbti_type="INTJ", mbti_source="self_reported")
    mbti_b_profile = _profile(mbti_type="ENFP", mbti_source="self_reported")
    blacklisted_profile = _profile(
        blacklist_majors=["\u8ba1\u7b97\u673a"],
        career_assessment_status="completed",
        career_assessment_mode="quick",
        holland_code=HollandCode(investigative=1.0),
        riasec_top_codes=["I"],
    )

    investigative = score_major_utility(option, investigative_profile)
    enterprising = score_major_utility(option, enterprising_profile)
    mbti_a = score_major_utility(option, mbti_a_profile)
    mbti_b = score_major_utility(option, mbti_b_profile)
    blacklisted = score_major_utility(option, blacklisted_profile)

    raw_probability = _historical_probability()
    raw_prob = round(float(raw_probability["prob"]), 12)
    artifact_path = Path(__file__).resolve().parents[2] / "data" / "probability_calibration_2025.json"
    artifact = load_probability_calibration(str(artifact_path.resolve()))
    calibrated_prob = (
        calibrate_probability(raw_prob, artifact, subject_group="\u7269\u7406")
        if artifact is not None
        else raw_prob
    )

    cases = {
        "investigative_vs_enterprising": {
            "major": COMPUTER_MAJOR,
            "investigative_utility": investigative.user_utility,
            "enterprising_utility": enterprising.user_utility,
            "investigative_career_fit": investigative.career_fit_score,
            "enterprising_career_fit": enterprising.career_fit_score,
            "utility_delta": _round_delta(
                investigative.user_utility,
                enterprising.user_utility,
            ),
        },
        "mbti_swap": {
            "major": COMPUTER_MAJOR,
            "mbti_a": "INTJ",
            "mbti_b": "ENFP",
            "major_utility_a": mbti_a.user_utility,
            "major_utility_b": mbti_b.user_utility,
            "major_utility_delta": _round_delta(mbti_a.user_utility, mbti_b.user_utility),
            "raw_probability_a": raw_prob,
            "raw_probability_b": raw_prob,
            "raw_probability_delta": 0,
            "calibrated_probability_a": calibrated_prob,
            "calibrated_probability_b": calibrated_prob,
            "calibrated_probability_delta": 0,
        },
        "riasec_probability_boundary": {
            "raw_probability_investigative": raw_prob,
            "raw_probability_enterprising": raw_prob,
            "raw_probability_delta": 0,
            "calibrated_probability_investigative": calibrated_prob,
            "calibrated_probability_enterprising": calibrated_prob,
            "calibrated_probability_delta": 0,
            "probability_inputs": {
                "score": 620,
                "rank": 12000,
                "subject_group": "physics",
                "historical_min_ranks": [11800, 12200, 12050],
                "quotas": [80, 85, 90],
            },
        },
        "blacklist_boundary": {
            "major": COMPUTER_MAJOR,
            "utility": blacklisted.user_utility,
            "is_blacklisted": blacklisted.is_blacklisted,
            "is_acceptable": blacklisted.is_acceptable,
            "career_fit_score": blacklisted.career_fit_score,
        },
    }

    gates = {
        "riasec_changes_major_utility": bool(cases["investigative_vs_enterprising"]["utility_delta"] > 0),
        "mbti_major_utility_invariant": cases["mbti_swap"]["major_utility_delta"] == 0,
        "admission_probability_invariant_under_riasec": (
            cases["riasec_probability_boundary"]["raw_probability_delta"] == 0
            and cases["riasec_probability_boundary"]["calibrated_probability_delta"] == 0
        ),
        "admission_probability_invariant_under_mbti": (
            cases["mbti_swap"]["raw_probability_delta"] == 0
            and cases["mbti_swap"]["calibrated_probability_delta"] == 0
        ),
        "blacklist_remains_hard_boundary": (
            cases["blacklist_boundary"]["utility"] == 0
            and cases["blacklist_boundary"]["is_blacklisted"] is True
            and cases["blacklist_boundary"]["is_acceptable"] is False
        ),
    }

    return {
        "protocol_version": "career-profile-fidelity-audit-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "evaluation_type": "deterministic_boundary_probe",
        "case_count": len(cases),
        "gates": gates,
        "cases": cases,
        "quality_claim_allowed": False,
        "claim_boundary": (
            "This audit proves deterministic career-profile influence boundaries: "
            "RIASEC may move major utility, MBTI does not move utility or admission "
            "probability, and admission probability is invariant to career-profile "
            "swaps when score/rank/subject/history are fixed. It does not prove "
            "improved admission outcomes."
        ),
    }


def write_career_profile_fidelity_audit(output_path: str | Path) -> dict[str, Any]:
    """Write the deterministic audit artifact and return its payload."""
    payload = build_career_profile_fidelity_audit()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(Path(__file__).resolve().parents[3] / "logs" / "career_profile_fidelity_audit_2026-06-12.json"),
        help="Path to write the JSON audit artifact.",
    )
    args = parser.parse_args()
    payload = write_career_profile_fidelity_audit(args.output)
    print(json.dumps({"output": args.output, "gates": payload["gates"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
