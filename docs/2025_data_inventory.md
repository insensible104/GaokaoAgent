# 2025 Data Inventory

This note records what 2025 data is already present in the repository and how it maps to the backtest / ablation pipeline.

## Files Found

| File | Type | Current Role | Backtest Use |
| --- | --- | --- | --- |
| `data/广东省2025年夏季高考专家版.xlsx` | Excel workbook | 2025 enrollment plan plus historical admission fields and school/major metadata | Candidate generation and historical-risk features. Not a 2025 actual outcome label file. |
| `data/2011-2025广东高考一分一段表.xlsx` | Excel workbook | 2011-2025 score-rank table | Rank / score conversion and 2025 score distribution context. Not actual admission outcomes. |
| `backend/data/2025_enrollment_full.csv` | Processed CSV | Cleaned subset derived from the expert Excel | Runtime enrollment loader input. |
| `backend/data/2025_enrollment_物理.csv` | Processed CSV | Physics-only 2025 enrollment subset | Runtime filtering input. |
| `backend/data/2025_enrollment_历史.csv` | Processed CSV | History-only 2025 enrollment subset | Runtime filtering input. |
| `backend/data/2025_物理_yifenyiduan.csv` | Processed CSV | 2025 physics score-rank table | Runtime score / rank helper. |
| `backend/data/2025_历史_yifenyiduan.csv` | Processed CSV | 2025 history score-rank table | Runtime score / rank helper. |
| `data/actual_2025.csv` | Processed CSV | 2025 post-hoc group and major admission outcomes | Actual labels for `backtest-2025` and `ablate-2025`. |
| `data/actual_2025_group_admissions.csv` | Processed CSV | 2025 school-major-group filing outcomes | Group admission / sliding labels. |
| `data/actual_2025_major_admissions.csv` | Processed CSV | 2025 major-level admission outcomes | Major assignment proxy labels. |

The project now has both prediction-time 2025 enrollment inputs and post-hoc
2025 actual outcome labels. The actual labels must only be loaded after a
volunteer plan is frozen.

## `广东省2025年夏季高考专家版.xlsx`

Workbook structure:

- Sheet: `专家版`
- Raw sheet size: 33,850 rows x 56 columns
- Parsed with row 3 as header: 33,847 data rows x 56 columns
- Processed runtime CSV: 33,846 rows x 22 columns

The one-row difference is caused by a subject-category anomaly in the source (`物理类` instead of the normalized `物理` / `历史`). The current processing script keeps only exact `物理` and `历史`, so that row is dropped.

### Column Blocks

| Columns | Block | Notes |
| --- | --- | --- |
| 1-14 | 2025 enrollment plan | School code/name, batch, subject group, major group, major code/name, remarks, requirements, subject requirement, quota, duration, tuition. |
| 15-19 | 2024 school-major-group filing data | Group plan count, filing count, admitted count, minimum score, minimum rank. |
| 20-23 | 2024 major-level admission / guide fields | Existing processing keeps minimum score and minimum rank from this area as 2024 major-level history. |
| 24-26 | 2023 major-level admission data | Existing processing maps minimum score/rank. |
| 27-29 | 2022 major-level admission data | Existing processing maps minimum score/rank. |
| 30-32 | 2021 major-level admission data | Existing processing maps minimum score/rank. |
| 33-46 | School metadata | Province, city, school tags, level, transfer-major info, institution type, ownership, recommendation rate, ranking, admissions charter. |
| 47-52 | Major metadata | Soft Science rating/ranking, discipline assessment, major level, master/doctoral point flags. |
| 53-56 | Graduate-program metadata | School-level master/doctoral program counts and names. |

### Distribution

| Field | Key Counts |
| --- | --- |
| Subject group | 22,664 `物理`, 11,182 `历史`, 1 anomalous `物理类` |
| Batch | 19,702 undergraduate regular, 12,304 junior-college regular, 1,179 undergraduate early, 392 special type, 270 junior-college early |
| Batch note | 19,702 本科, 12,304 专科, 571 提前批本科.军检院校(含公安), 392 特殊类型招生, 249 提前批本科.非军检院校 |
| Largest school row counts | 深圳职业技术大学 282, 广州大学 198, 华南农业大学 187 |
| Common per-major quotas | 2 seats: 8,030 rows; 1 seat: 4,557 rows; 3 seats: 3,671 rows |

## `2011-2025广东高考一分一段表.xlsx`

Workbook structure:

- Main sheet: `一分一段表`
- Parsed rows: 14,368
- 2025 rows: 1,171
- 2025 subject labels in the workbook: `理科` 598 rows, `文科` 573 rows

2025 ranges:

| Subject Label | Score Range | Max Worst Rank |
| --- | ---: | ---: |
| 理科 | 100-697 | 440,208 |
| 文科 | 100-672 | 292,200 |

For the current project, `理科` should be treated as the 2025 physics-side score-rank table and `文科` as the history-side score-rank table, matching the already processed `backend/data/2025_物理_yifenyiduan.csv` and `backend/data/2025_历史_yifenyiduan.csv`.

## Current Pipeline Fit

What is already enough:

- Generate 2025 candidate school-major groups.
- Use 2021-2024 historical group/major admission data for risk features.
- Use 2025 score-rank tables for rank/score conversion.
- Load real 2025 group/major outcome labels from `data/actual_2025.csv`.
- Build frozen plans for 2025 prospective experiments.
- Run ablation once frozen plans include `candidate_rows` and `user_profile`.

What is still missing before metric claims:

- A frozen plan dataset such as `logs/frozen_plans_2025.jsonl`.
- Each frozen plan record must include the final full plan, `candidate_rows`,
  and `user_profile` so baselines can be reconstructed fairly.
- A completed backtest / ablation result table and claim audit.

With actual labels present, the current remaining integrity boundary is that
the labels must not be used during plan generation. They are outcome-time
labels for evaluation only.

## Recommended Next Data Work

1. Preserve the current expert Excel as the 2025 enrollment-plan source.
2. Keep the actual outcome workbook separate as `data/actual_2025_source_antoshengya.xlsx`.
3. Rebuild actual labels with `backend/process_actual_2025_admissions.py` when the source workbook changes.
4. Upgrade `backend/process_2025_enrollment.py` to preserve the school metadata and major metadata columns from the expert Excel.
5. Normalize source subject labels so the one `物理类` anomaly is not silently dropped.
6. Add a data-quality smoke test that checks row counts, required columns, subject labels, and no accidental use of 2025 actual outcomes during plan generation.

Detailed actual-outcome audit note:

- `docs/2025_actual_outcome_inventory.md`
