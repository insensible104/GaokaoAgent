"""Smoke tests for rank-stratified candidate truncation."""

import pandas as pd

from engines.quant_engine import _stratified_candidate_selection


def test_truncation_preserves_harder_near_and_safer_candidates() -> None:
    rows = []
    for idx, min_rank in enumerate(
        [3000, 5000, 7000, 8500, 9500, 11000, 12500, 15000, 17500, 19500, 22000, 26000]
    ):
        rows.append(
            {
                "school": f"School {idx}",
                "major_group": f"{200 + idx}",
                "min_rank": min_rank,
            }
        )

    selected = _stratified_candidate_selection(
        pd.DataFrame(rows),
        user_rank=12000,
        target_count=9,
    )
    rank_diffs = selected["min_rank"] - 12000

    assert len(selected) == 9
    assert (rank_diffs < -3000).any(), "harder-side candidates must survive truncation"
    assert ((rank_diffs >= -3000) & (rank_diffs <= 6000)).any(), "near-rank candidates must survive truncation"
    assert (rank_diffs > 6000).any(), "safer-side candidates must survive truncation"
    assert selected[["school", "major_group"]].duplicated().sum() == 0


def test_unused_bucket_capacity_is_filled_without_duplicates() -> None:
    source = pd.DataFrame(
        [
            {"school": "A", "major_group": "201", "min_rank": 11000},
            {"school": "B", "major_group": "202", "min_rank": 12000},
            {"school": "C", "major_group": "203", "min_rank": 13000},
            {"school": "D", "major_group": "204", "min_rank": 14000},
            {"school": "E", "major_group": "205", "min_rank": 15000},
            {"school": "E", "major_group": "205", "min_rank": 15000},
        ]
    )

    selected = _stratified_candidate_selection(source, user_rank=12000, target_count=5)

    assert len(selected) == 5
    assert selected[["school", "major_group"]].duplicated().sum() == 0


if __name__ == "__main__":
    test_truncation_preserves_harder_near_and_safer_candidates()
    test_unused_bucket_capacity_is_filled_without_duplicates()
    print("candidate search coverage smoke tests passed")
