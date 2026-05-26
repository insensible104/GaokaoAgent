"""Smoke tests for enrollment-plan diff signals."""

from __future__ import annotations

from recommendation.enrollment_diff import diff_enrollment_plans


def test_enrollment_diff_detects_new_quota_tuition_and_campus_changes() -> None:
    previous_rows = [
        {
            "school_code": "10001",
            "school_name": "A University",
            "subject_group": "physics",
            "major_group_code": "201",
            "major_code": "01",
            "major_name": "Computer Science",
            "plan_quota": 2,
            "tuition": 5000,
            "remarks": "Main campus",
        },
        {
            "school_code": "10001",
            "school_name": "A University",
            "subject_group": "physics",
            "major_group_code": "201",
            "major_code": "03",
            "major_name": "Data Science",
            "plan_quota": 1,
            "tuition": 5000,
            "remarks": "Main campus",
        },
        {
            "school_code": "10001",
            "school_name": "A University",
            "subject_group": "physics",
            "major_group_code": "201",
            "major_code": "02",
            "major_name": "Software Engineering",
            "plan_quota": 1,
            "tuition": 5000,
            "remarks": "Main campus",
        },
    ]
    current_rows = [
        {
            "school_code": "10001",
            "school_name": "A University",
            "subject_group": "physics",
            "major_group_code": "201",
            "major_code": "01",
            "major_name": "Computer Science",
            "plan_quota": 5,
            "tuition": 80000,
            "remarks": "New campus",
        },
        {
            "school_code": "10001",
            "school_name": "A University",
            "subject_group": "physics",
            "major_group_code": "202",
            "major_code": "03",
            "major_name": "Data Science",
            "plan_quota": 4,
            "tuition": 5000,
            "remarks": "Main campus",
        },
    ]

    report = diff_enrollment_plans(previous_rows, current_rows)

    kinds = {event.change_type for event in report.events}
    assert "new_group" in kinds
    assert "removed_major" in kinds
    assert "quota_increase" in kinds
    assert "tuition_change" in kinds
    assert "campus_or_remark_change" in kinds
    assert "split_or_regroup" in kinds
    assert report.summary["current_group_count"] == 2
    assert report.summary["new_group_count"] == 1
    assert report.summary["quota_increase_count"] == 1
    assert report.summary["tuition_change_count"] == 1


if __name__ == "__main__":
    test_enrollment_diff_detects_new_quota_tuition_and_campus_changes()
    print("enrollment diff smoke tests passed")
