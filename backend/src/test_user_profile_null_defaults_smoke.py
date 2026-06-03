"""Smoke tests for tolerant profile parsing from LLM JSON."""

from models.user_profile import UserProfile


def test_user_profile_accepts_null_collection_defaults() -> None:
    profile = UserProfile(
        score=620,
        rank=12000,
        subject_group="物理",
        preferred_cities=None,
        preferred_majors=None,
        blacklist_majors=None,
        emotional_concerns=None,
        medical_restrictions=None,
    )

    assert profile.preferred_cities == []
    assert profile.preferred_majors == []
    assert profile.blacklist_majors == []
    assert profile.emotional_concerns == []
    assert profile.medical_restrictions == {}


if __name__ == "__main__":
    test_user_profile_accepts_null_collection_defaults()
    print("user profile null defaults smoke tests passed")
