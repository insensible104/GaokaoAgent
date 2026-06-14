"""Smoke tests for the career-profile fidelity audit artifact."""

from evaluation.career_profile_fidelity_audit import build_career_profile_fidelity_audit


def test_career_profile_fidelity_audit_gates_are_explicit() -> None:
    audit = build_career_profile_fidelity_audit()

    assert audit["protocol_version"] == "career-profile-fidelity-audit-v1"
    assert audit["quality_claim_allowed"] is False
    assert audit["gates"]["riasec_changes_major_utility"] is True
    assert audit["gates"]["mbti_major_utility_invariant"] is True
    assert audit["gates"]["admission_probability_invariant_under_riasec"] is True
    assert audit["gates"]["admission_probability_invariant_under_mbti"] is True
    assert audit["gates"]["blacklist_remains_hard_boundary"] is True
    assert audit["cases"]["investigative_vs_enterprising"]["utility_delta"] > 0
    assert audit["cases"]["mbti_swap"]["major_utility_delta"] == 0
    assert audit["cases"]["mbti_swap"]["raw_probability_delta"] == 0
    assert audit["cases"]["mbti_swap"]["calibrated_probability_delta"] == 0


if __name__ == "__main__":
    test_career_profile_fidelity_audit_gates_are_explicit()
    print("career profile fidelity audit smoke tests passed")
