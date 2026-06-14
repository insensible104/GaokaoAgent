"""Smoke tests for representative-profile runtime mix auditing."""

from evaluation.runtime_mix_audit import audit_runtime_mix_cases


def test_runtime_mix_audit_aggregates_coverage_without_quality_claim() -> None:
    cases = [
        {
            "case_id": "physics-12k",
            "subject_group": "physics",
            "rank_band": "5k_20k",
            "incomplete_data": False,
            "response_seconds": 8.0,
            "row_count": 10,
            "plan_change_explanation_count": 3,
            "plan_change_applied_count": 2,
            "plan_change_review_count": 0,
            "probability_is_calibrated": True,
            "plan_probability_lower": 0.46,
            "plan_probability_upper": 0.72,
            "key_prefix_count": 5,
            "shadowed_choice_count": 5,
            "capacity_fill": {
                "requested_count": 10,
                "initial_count": 8,
                "filled_count": 2,
                "final_count": 10,
                "remaining_shortfall": 0,
            },
            "coverage_report": {
                "classified": {"rush": 8, "target": 9, "safe": 7},
                "selected": {"rush": 3, "target": 4, "safe": 3},
                "deficits": {},
                "coverage_sufficient": True,
            },
        },
        {
            "case_id": "physics-45k",
            "subject_group": "physics",
            "rank_band": "20k_60k",
            "incomplete_data": True,
            "response_seconds": 12.0,
            "row_count": 8,
            "plan_change_explanation_count": 1,
            "plan_change_applied_count": 1,
            "plan_change_review_count": 1,
            "probability_is_calibrated": True,
            "plan_probability_lower": 0.44,
            "plan_probability_upper": 0.68,
            "key_prefix_count": 4,
            "shadowed_choice_count": 4,
            "coverage_report": {
                "classified": {"rush": 6, "target": 5, "safe": 1},
                "selected": {"rush": 3, "target": 4, "safe": 1},
                "deficits": {"safe": 2},
                "coverage_sufficient": False,
            },
        },
        {
            "case_id": "history-18k",
            "subject_group": "history",
            "rank_band": "5k_20k",
            "incomplete_data": False,
            "response_seconds": 10.0,
            "row_count": 10,
            "plan_change_explanation_count": 0,
            "plan_change_applied_count": 0,
            "plan_change_review_count": 0,
            "coverage_report": {
                "classified": {"rush": 7, "target": 8, "safe": 5},
                "selected": {"rush": 3, "target": 4, "safe": 3},
                "deficits": {},
                "coverage_sufficient": True,
            },
        },
        {
            "case_id": "history-70k",
            "subject_group": "history",
            "rank_band": "60k_120k",
            "incomplete_data": False,
            "response_seconds": 14.0,
            "row_count": 8,
            "plan_change_explanation_count": 2,
            "plan_change_applied_count": 1,
            "plan_change_review_count": 0,
            "coverage_report": {
                "classified": {"rush": 4, "target": 3, "safe": 2},
                "selected": {"rush": 3, "target": 3, "safe": 2},
                "deficits": {"target": 1, "safe": 1},
                "coverage_sufficient": False,
            },
        },
    ]

    audit = audit_runtime_mix_cases(cases)

    assert audit["case_count"] == 4
    assert audit["coverage_sufficient_case_count"] == 2
    assert audit["coverage_sufficient_rate"] == 0.5
    assert audit["aggregate_classified"] == {"rush": 25, "target": 25, "safe": 15}
    assert audit["aggregate_selected"] == {"rush": 12, "target": 15, "safe": 9}
    assert audit["aggregate_deficits"] == {"rush": 0, "target": 1, "safe": 3}
    assert audit["incomplete_data_case_count"] == 1
    assert audit["average_response_seconds"] == 11.0
    assert audit["plan_change_explained_case_count"] == 3
    assert audit["plan_change_explanation_count"] == 6
    assert audit["plan_change_applied_count"] == 4
    assert audit["plan_change_review_count"] == 1
    assert audit["calibrated_case_count"] == 2
    assert audit["average_key_prefix_count"] == 2.25
    assert audit["average_shadowed_ratio"] == 0.25
    assert audit["average_plan_probability_lower"] == 0.45
    assert audit["average_plan_probability_upper"] == 0.7
    assert audit["capacity_filled_case_count"] == 1
    assert audit["capacity_filled_row_count"] == 2
    assert audit["remaining_capacity_shortfall"] == 0
    assert audit["by_subject"]["physics"]["coverage_sufficient_rate"] == 0.5
    assert audit["by_subject"]["history"]["case_count"] == 2
    assert audit["quality_claim_allowed"] is False
    assert "admission quality" in audit["claim_boundary"]


if __name__ == "__main__":
    test_runtime_mix_audit_aggregates_coverage_without_quality_claim()
    print("runtime mix audit smoke test passed")
