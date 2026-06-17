from models.game_matrix import MajorOption
from models.user_profile import HollandCode, UserProfile
from recommendation.major_utility import score_major_utility


def _profile(**updates) -> UserProfile:
    values = {
        "score": 610,
        "rank": 22000,
        "subject_group": "物理",
    }
    values.update(updates)
    return UserProfile(**values)


def test_untaken_assessment_keeps_existing_neutral_utility() -> None:
    scored = score_major_utility(MajorOption(major_name="计算机科学与技术"), _profile())

    assert scored.user_utility == 0.45
    assert scored.career_fit_score is None
    assert all("职业兴趣" not in reason for reason in scored.risk_reasons)


def test_investigative_profile_prefers_analytical_major_category() -> None:
    profile = _profile(
        career_assessment_status="completed",
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

    computer = score_major_utility(MajorOption(major_name="计算机科学与技术"), profile)
    management = score_major_utility(MajorOption(major_name="工商管理"), profile)

    assert computer.career_fit_score is not None
    assert management.career_fit_score is not None
    assert computer.career_fit_score > management.career_fit_score
    assert computer.user_utility > management.user_utility
    assert any("职业兴趣" in reason for reason in computer.risk_reasons)


def test_mbti_alone_never_changes_major_utility() -> None:
    option = MajorOption(major_name="计算机科学与技术")

    without_mbti = score_major_utility(option, _profile())
    with_mbti = score_major_utility(option, _profile(mbti_type="INTJ", mbti_source="self_reported"))

    assert with_mbti.user_utility == without_mbti.user_utility
    assert with_mbti.career_fit_score == without_mbti.career_fit_score


def test_blacklist_remains_a_hard_constraint_with_high_career_fit() -> None:
    profile = _profile(
        blacklist_majors=["计算机"],
        career_assessment_status="completed",
        holland_code=HollandCode(investigative=1.0),
        riasec_top_codes=["I"],
    )

    scored = score_major_utility(MajorOption(major_name="计算机科学与技术"), profile)

    assert scored.user_utility == 0.0
    assert scored.is_blacklisted is True
    assert scored.is_acceptable is False
