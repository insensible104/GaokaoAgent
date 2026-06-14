"""Smoke tests for blocking fabricated recommendation inputs."""

from langchain_core.messages import HumanMessage

from agents import profiling_agent
from models.user_profile import RiskTolerance, SchoolMajorPreference, UserProfile
from rl.supervisor_policy import HeuristicSupervisorPolicy


def test_missing_score_and_rank_block_formal_recommendation() -> None:
    assert hasattr(profiling_agent, "assess_recommendation_readiness")

    profile = UserProfile(
        score=None,
        rank=None,
        subject_group="physics",
        preferred_majors=["computer science"],
    )
    result = profiling_agent.assess_recommendation_readiness(profile)

    assert result["ready"] is False
    assert set(result["missing_fields"]) == {"score", "rank"}
    assert profile.score is None
    assert profile.rank is None


def test_rank_with_subject_group_is_enough_for_quant_recommendation() -> None:
    assert hasattr(profiling_agent, "assess_recommendation_readiness")

    profile = UserProfile(
        score=None,
        rank=12000,
        subject_group="physics",
    )
    result = profiling_agent.assess_recommendation_readiness(profile)

    assert result["ready"] is True
    assert result["missing_fields"] == []


def test_subject_group_is_required_for_formal_recommendation() -> None:
    assert hasattr(profiling_agent, "assess_recommendation_readiness")

    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="",
    )
    result = profiling_agent.assess_recommendation_readiness(profile)

    assert result["ready"] is False
    assert result["missing_fields"] == ["subject_group"]


def test_supervisor_stops_before_game_when_profile_is_not_ready() -> None:
    profile = UserProfile(
        score=None,
        rank=None,
        subject_group="physics",
        recommendation_ready=False,
        missing_critical_fields=["score", "rank"],
    )
    decision = HeuristicSupervisorPolicy().decide_after_profiling(
        {
            "user_profile": profile,
            "intent_classification": None,
            "loop_history": [],
        }
    )

    assert decision.selected_action == "END"
    assert decision.metadata["missing_critical_fields"] == ["score", "rank"]


def test_deterministic_fallback_preserves_structured_user_inputs() -> None:
    profile = profiling_agent.extract_profile_from_text(
        """我的高考信息如下：
- 总分：620
- 全省位次：12000
- 选科组合：物理

偏好专业：计算机
不想学的专业：土木
偏好城市：广州、深圳
风险偏好：balanced
"""
    )

    assert profile.score == 620
    assert profile.rank == 12000
    assert profile.subject_group == "物理"
    assert profile.preferred_majors == ["计算机"]
    assert profile.blacklist_majors == ["土木"]
    assert profile.preferred_cities == ["广州", "深圳"]
    assert profile.recommendation_ready is True


def test_explicit_profile_fields_override_conflicting_inference() -> None:
    assert hasattr(profiling_agent, "merge_explicit_profile")

    inferred = UserProfile(
        score=610,
        rank=16000,
        subject_group="历史",
        preferred_cities=["北京"],
        preferred_majors=["金融"],
        blacklist_majors=[],
        risk_tolerance=RiskTolerance.AGGRESSIVE,
        school_major_preference=SchoolMajorPreference.PRIORITIZE_SCHOOL,
        emotional_concerns=["fear of sliding"],
    )

    merged = profiling_agent.merge_explicit_profile(
        inferred,
        {
            "score": 620,
            "rank": 12000,
            "subject_group": "物理",
            "preferred_cities": ["广州"],
            "preferred_majors": ["计算机"],
            "blacklist_majors": ["土木"],
            "risk_tolerance": "conservative",
            "school_major_preference": "prioritize_major",
        },
    )

    assert merged.score == 620
    assert merged.rank == 12000
    assert merged.subject_group == "物理"
    assert merged.preferred_cities == ["广州"]
    assert merged.preferred_majors == ["计算机"]
    assert merged.blacklist_majors == ["土木"]
    assert merged.risk_tolerance == RiskTolerance.CONSERVATIVE
    assert merged.school_major_preference == SchoolMajorPreference.PRIORITIZE_MAJOR
    assert merged.emotional_concerns == ["fear of sliding"]
    assert merged.field_provenance["risk_tolerance"] == "user_explicit"
    assert merged.field_provenance["emotional_concerns"] == "inferred"


def test_structured_profile_survives_llm_initialization_failure(monkeypatch) -> None:
    def unavailable_llm():
        raise RuntimeError("LLM unavailable")

    monkeypatch.setattr(profiling_agent, "get_llm", unavailable_llm)
    result = profiling_agent.profiling_agent_node(
        {
            "messages": [HumanMessage(content="请直接按表单信息推荐。")],
            "user_profile": None,
            "explicit_profile": {
                "score": 620,
                "rank": 12000,
                "subject_group": "物理",
                "preferred_cities": ["广州"],
                "preferred_majors": ["计算机"],
                "blacklist_majors": ["土木"],
                "risk_tolerance": "conservative",
            },
        }
    )

    profile = result["user_profile"]
    assert profile.recommendation_ready is True
    assert profile.risk_tolerance == RiskTolerance.CONSERVATIVE
    assert profile.preferred_cities == ["广州"]
    assert profile.blacklist_majors == ["土木"]
    assert profile.field_provenance["risk_tolerance"] == "user_explicit"


def test_measured_career_profile_overrides_inferred_personality_fields() -> None:
    inferred = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        mbti_type="ENFP",
    )
    merged = profiling_agent.merge_explicit_profile(
        inferred,
        {
            "holland_code": {
                "realistic": 0.25,
                "investigative": 1.0,
                "artistic": 0.25,
                "social": 0.25,
                "enterprising": 0.25,
                "conventional": 0.25,
            },
            "riasec_top_codes": ["I", "R", "A"],
            "career_assessment_mode": "quick",
            "career_assessment_status": "completed",
            "mbti_type": "INTJ",
            "mbti_source": "self_reported",
            "career_values": ["growth", "autonomy"],
            "_field_provenance": {
                "holland_code": "measured_assessment",
                "riasec_top_codes": "measured_assessment",
                "career_assessment_mode": "measured_assessment",
                "career_assessment_status": "measured_assessment",
                "mbti_type": "user_explicit",
                "mbti_source": "user_explicit",
                "career_values": "user_explicit",
            },
        },
    )

    assert merged.holland_code is not None
    assert merged.holland_code.investigative == 1.0
    assert merged.riasec_top_codes == ["I", "R", "A"]
    assert merged.mbti_type == "INTJ"
    assert merged.career_values == ["growth", "autonomy"]
    assert merged.field_provenance["holland_code"] == "measured_assessment"
    assert merged.field_provenance["mbti_type"] == "user_explicit"


if __name__ == "__main__":
    test_missing_score_and_rank_block_formal_recommendation()
    test_rank_with_subject_group_is_enough_for_quant_recommendation()
    test_subject_group_is_required_for_formal_recommendation()
    test_supervisor_stops_before_game_when_profile_is_not_ready()
    test_deterministic_fallback_preserves_structured_user_inputs()
    print("profiling critical-input smoke tests passed")
