# 2025 Actual Outcome Inventory

Source workbook:

- `C:/Users/95340/Downloads/(安托生涯)25年广东高考分专业录取数据-26430.xlsx`
- Local reproducible copy: `data/actual_2025_source_antoshengya.xlsx`

This workbook fills the missing 2025 post-hoc admission-label layer for the backtest and ablation pipeline. It is different from the 2025 enrollment-plan expert workbook: this file records actual filing and major-admission outcomes after admission.

## Workbook Structure

| Sheet | Role | Parsed Rows |
| --- | --- | ---: |
| `摘要` | Source notes from 安托生涯 | 8 preview rows |
| `历史科` | History-side major-level actual admission rows | 2,656 |
| `物理科` | Physics-side major-level actual admission rows | 8,324 |
| `历史科投档` | History-side school-major-group filing outcomes | 906 |
| `物理科投档` | Physics-side school-major-group filing outcomes | 2,069 |
| `选科组合` | Subject-combination lookup table | reference sheet |

## Normalized Outputs

| Output | Rows | Purpose |
| --- | ---: | --- |
| `data/actual_2025_major_admissions.csv` | 10,980 | One row per actual admitted major/major class. |
| `data/actual_2025_group_admissions.csv` | 2,975 | One row per school-major group filing result. |
| `data/actual_2025.csv` | 10,980 | Merged pipeline file for `backtest-2025` and `ablate-2025`. Group cutoff fields are repeated onto each major row. |
| `data/actual_2025_data_quality.json` | 1 | Data-quality summary for reproducibility. |

Processing script:

- `backend/process_actual_2025_admissions.py`

Rebuild command:

```powershell
backend\.venv\Scripts\python.exe backend\process_actual_2025_admissions.py --output-dir data
```

The script also works with the bundled spreadsheet runtime, but the project venv is preferred for normal repo work.

## Quality Summary

| Check | Result |
| --- | ---: |
| Schools | 470 |
| Major-level rows | 10,980 |
| Group-level rows | 2,975 |
| Major groups from major rows | 2,975 |
| Major groups from group rows | 2,975 |
| Major rows matched to group filing rows | 100% |
| Missing major minimum rank | 0 |
| Missing group minimum rank | 0 |
| Duplicate full major keys | 0 |
| Duplicate group keys | 0 |
| Duplicate major-name rows within the same group | 445 |
| Duplicate major-name groups within the same group | 195 |

Subject split:

| Subject Group | Major Rows | Group Rows |
| --- | ---: | ---: |
| 物理 | 8,324 | 2,069 |
| 历史 | 2,656 | 906 |

## Schema Mapping

`data/actual_2025.csv` exposes the fields expected by the evaluation loader:

| Pipeline Field | Source Meaning |
| --- | --- |
| `school_code` | 院校代码 |
| `school_name` | 院校名称 |
| `major_group_code` | 专业组 |
| `actual_group_min_score` | 投档分 |
| `actual_group_min_rank` | 专业组投档排位 |
| `major_code` | 专业编号 |
| `major_name` | 专业/类 |
| `actual_major_min_score` | 分专业最低分 |
| `actual_major_min_rank` | 分专业最低分平均排位 |
| `actual_major_admit_count` | 分专业录取人数 |

Important interpretation:

- `actual_group_min_rank` is the group-level filing cutoff and should be used for admission / sliding evaluation.
- `actual_major_min_rank` is the major-level cutoff proxy from the source workbook. The source labels it as lowest-score average rank, so major assignment metrics should describe it as an admission-label proxy unless cross-checked with official school PDFs.
- Some groups contain repeated `major_name` values with different codes or notes, such as different 法学 tracks. The CSV preserves every row. The backtest loader aggregates duplicate names by keeping the largest cutoff rank so assignment is deterministic and not dependent on Excel row order.

## Current Experiment Status

The project now has the missing actual-outcome file required by:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py backtest-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py ablate-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl
```

The remaining blocker for full backtest/ablation is `logs/frozen_plans_2025.jsonl`: frozen plans must include the final full plan plus `candidate_rows` and `user_profile` for baseline reconstruction.
