# GaokaoAgent Daily Change Log

This note reconstructs what has been done from Git history, file timestamps, and current uncommitted changes. It is written as a research/project record rather than a raw file list.

Generated on 2026-05-12. The main project commit is `ac266af` on 2026-05-06. Older upstream commits belong to the original Google quickstart template and are not counted as GaokaoAgent project work.

## Evidence Used

| Evidence | What It Shows |
| --- | --- |
| `git log --all --name-status` | The project was committed as `Initial GaokaoAgent project` on 2026-05-06. |
| `git status --short` | Current work includes encoding protection, backend/API improvements, agent deliberation metrics, 2025 ablation, and 2025 data inventory. |
| File modification times under `backend/src`, `backend/scripts`, `backend/data`, `data`, and `docs` | Reconstructs the development sequence before the first clean project commit. |
| Existing docs in `docs/` and `backend/docs/` | Shows the intended research narrative, architecture, experiment plan, and governance state. |

## Daily Timeline

| Date | What We Did | Concrete Improvement |
| --- | --- | --- |
| 2025-09-13 | Added or obtained the main 2025 Guangdong expert enrollment workbook: `data/广东省2025年夏季高考专家版.xlsx`. | Established the raw 2025 enrollment-plan source. This is plan data plus historical fields, not actual 2025 admission outcomes. |
| 2025-12-22 | Baseline project/template files existed before the Gaokao-specific work was consolidated. | Provided a runnable web/backend scaffold, but this was still mostly inherited structure. |
| 2026-01-01 | Built the first data-processing layer: 2021-2024 historical admission CSVs, 2025 enrollment CSVs, score-rank tables, SFT/test datasets, PDF/RAG indexing scripts. | Moved the project from concept to data-backed prototype. The system could start reasoning from real admission tables instead of hand-written examples. |
| 2026-01-07 | Added quantitative recommendation components such as admission metrics, sentiment signals, Pareto optimization, search-space reduction, and early backtest machinery. | Recommendation quality became measurable and optimizable rather than a pure LLM narrative. |
| 2026-01-08 | Added school/major scoring, adjustment simulation, city mapping, rate limiting, constants, and medium-fix tests. | Strengthened domain realism: school location, major attributes, transfer/adjustment risk, and engineering robustness entered the pipeline. |
| 2026-01-09 | Added RL/recommendation research components: two-stage recommendation engine, volunteer combination optimizer, GRPO policy, school-selection environment/trainer, realistic data generator, major assignment predictor, preference handler, and deep-research scoring. | Opened the path from static ranking to trainable planning. This is the first point where the project becomes an "agentic recommendation + optimization" research prototype rather than only a rules engine. |
| 2026-01-10 | Added runtime helpers such as LLM factory, local Ollama wrapper, validator, and related tests/utilities. | Improved backend operability and validation, making LLM-backed modules easier to swap and test. |
| 2026-01-12 | Added probability, Monte Carlo simulation, and rank-gradient strategy modules. | Strengthened uncertainty modeling and ranking sensitivity analysis, which are important for explaining risk in志愿填报. |
| 2026-01-13 | Wrote the safe-school fix report: `docs/260113_SAFE_SCHOOLS_FIX_REPORT.md`. | Captured a risk-control milestone: the project started treating "保底" as a formal safety property instead of a vague label. |
| 2026-02-10 | Added FastAPI route documentation and backend package initialization records. | Clarified how the backend should be exposed as an API, preparing the system for frontend/demo integration. |
| 2026-03-20 | Added runtime policy and graph-layer scaffolding. | Began separating orchestration policy from individual agents, which is necessary for multi-step decision control. |
| 2026-03-21 | Added agent protocol smoke tests, deep-research agent, rollout supervisor traces, orchestration cases, pairwise dataset builder, TRL utilities, reward-model training scripts, GRPO training scripts, and HF job entry points. | Built the alignment/research pipeline: traces -> pairwise data -> reward model / GRPO -> runtime policy. This is the core of the "agent behavior can be optimized" claim. |
| 2026-03-23 | Added orchestration evaluation, minimal supervisor reward model training, reward-model scorer, report-agent research-only smoke, and current project status overview. | Turned the alignment layer into something evaluable. Also documented what was complete versus what still needed real benchmark results. |
| 2026-03-31 | Added resume/project reference documentation. | Improved external communication: the project became easier to explain in interviews or applications. |
| 2026-05-05 | Wrote the literature review, two-layer recommendation spec, and volunteer-form refactor spec. Added/refined major taxonomy, major utility, policy config, school signal, bundle risk, enrollment loader, volunteer-plan schema smoke, and tradeoff policy work. | Corrected the project taste toward the real Gaokao object: "院校专业组 / group-level item" rather than generic school recommendation. This is a major domain-model upgrade. |
| 2026-05-06 | Added first-hit prefix tests, critic behavior, GRPO recommendation trainer, orchestration data pipeline, supervisor policy, game agent, tradeoff policy, backtest 2025 schema/metrics/baselines, profiling/user-profile extensions, enhanced critic, report/router graph pieces, and architecture/interview docs. | The backend and agent chain became explainable end to end: profile -> recommendation -> deliberation/audit -> report -> evaluation. |
| 2026-05-06 | Cleaned temporary files, created unified CLI entry points, and added experiment-suite orchestration and runbook docs. | Made the project operable from one command surface instead of scattered scripts. This improves reproducibility and interview/demo readiness. |
| 2026-05-06 | Renamed the project from inherited/old naming to `GaokaoAgent`, updated backend package metadata, Docker/front-end names, page title, and main FastAPI entry. Configured Git remotes so the old upstream cannot be accidentally pushed to. | Converted the repository from "cloned template plus edits" into the user's own named project with cleaner ownership boundaries. |
| 2026-05-06 | Added encoding safeguards: `.editorconfig`, `.gitattributes`, encoding smoke tests, and governance notes for UTF-8 handling on Windows. | Reduced the risk of Chinese text corruption in docs, CSV headers, prompts, and terminal inspection. |
| 2026-05-06 | Improved backend/API surface: request normalization, subject-group handling, runtime status helper, `/api/status`, and backend API smoke tests. | Made the service easier to monitor and less brittle to frontend/user input variants. |
| 2026-05-06 | Improved agent deliberation: added quality score, quality flags, advisor actions, summary/debug metadata, and stronger smoke assertions. | Multi-agent review became auditable. The coordinator no longer only returns a final text summary; it also exposes whether the deliberation itself is healthy. |
| 2026-05-06 | Added 2025 ablation pipeline: `backend/src/evaluation/ablation_2025.py`, CLI command `ablate-2025`, experiment-suite `--run-ablation`, smoke test, and runbook updates. | Closed the experiment-design gap between "has a backtest skeleton" and "can compare Full vs baseline variants." This is required for moving from engineering prototype to experiment loop. |
| 2026-05-06 | Audited available 2025 Excel files and wrote `docs/2025_data_inventory.md`. | Clarified a crucial scientific boundary: current Excel data is enough for 2025 candidate generation and historical-risk features, but not enough to claim real 2025 admission accuracy without a separate `actual_2025.csv`. |
| 2026-05-12 | Organized the 2025 actual admission workbook from 安托生涯, added `backend/process_actual_2025_admissions.py`, and generated `data/actual_2025.csv`, `data/actual_2025_major_admissions.csv`, `data/actual_2025_group_admissions.csv`, and `data/actual_2025_data_quality.json`. | Removed the main outcome-label blocker for real 2025 backtest / ablation. The remaining experimental blocker is generating frozen plan records with candidate rows and user profiles. |

## Current Uncommitted Work

The current working tree contains the latest engineering improvements and has not yet been committed:

| Area | Files |
| --- | --- |
| Encoding guardrails | `.editorconfig`, `.gitattributes`, `backend/src/test_encoding_smoke.py`, `docs/project_governance_status.md` |
| Backend/API status | `backend/src/main.py`, `backend/src/test_backend_api_status_smoke.py`, `backend/src/gaokao_agent_cli.py` |
| Agent deliberation quality | `backend/src/agents/deliberation_agents.py`, `backend/src/models/agent_communication.py`, `backend/src/test_multi_agent_deliberation_smoke.py` |
| 2025 ablation | `backend/src/evaluation/ablation_2025.py`, `backend/src/test_ablation_2025_smoke.py`, `backend/scripts/run_experiment_suite.py`, `docs/experiment_runbook.md` |
| 2025 data audit and actual labels | `backend/process_actual_2025_admissions.py`, `data/actual_2025.csv`, `data/actual_2025_major_admissions.csv`, `data/actual_2025_group_admissions.csv`, `data/actual_2025_data_quality.json`, `docs/2025_data_inventory.md`, `docs/2025_actual_outcome_inventory.md` |

Latest verified state from the current work:

- `backend/.venv/Scripts/python.exe -m pytest backend/src/test_encoding_smoke.py -q`: 3 passed.
- `backend/.venv/Scripts/python.exe backend/scripts/gaokao_agent.py smoke --fail-fast`: 12 smoke tests passed.
- `backend/.venv/Scripts/python.exe backend/scripts/gaokao_agent.py ablate-2025 --help`: command is available.
- `backend/.venv/Scripts/python.exe backend/scripts/run_experiment_suite.py --help`: experiment suite supports the ablation option.

## Net Improvement By Research Dimension

| Dimension | Before | Now | Remaining Gap |
| --- | --- | --- | --- |
| Domain modeling | Generic recommendation tendency. | Group-level Gaokao item modeling with major group, major code, quota, transfer/adjustment risk, school and major metadata. | Preserve more metadata columns from the 2025 expert Excel and normalize source anomalies. |
| Backend operability | Multiple scattered scripts and partially inherited naming. | Unified `GaokaoAgent` naming, CLI, FastAPI entry, status endpoint, smoke command, experiment suite. | Commit current changes and keep a single documented demo path. |
| Agent system | Agents existed but quality of coordination was harder to inspect. | Typed communication, message bus, deliberation coordinator, quality score/flags/actions, protocol smoke tests. | More real cases and finer-grained advisor disagreement analysis. |
| Evaluation | 2025 backtest framework existed but was not enough for claims. | Backtest plus ablation CLI, experiment-suite integration, and real 2025 group/major outcome labels. | Generate frozen plans, run the backtest/ablation table, and audit claims against the produced metrics. |
| RL/alignment | Training scripts and traces existed as research scaffolding. | Rollout, pairwise, reward model, GRPO, supervisor policy, and evaluation hooks are present. | Need repeated experiments with metrics and ablation tables. |
| Documentation | Many reports existed, but ownership and next steps were fragmented. | Governance, architecture, runbook, data inventory, and this daily log are now aligned around the same story. | Keep future runs logged with datasets, commands, metrics, and claims. |

## Taste Calibration

Strong claims the project can currently support:

- This is a runnable Gaokao志愿规划 research prototype with real 2025 enrollment-plan data, 2021-2024 historical references, real 2025 post-hoc outcome labels, multi-agent audit, and a unified experiment interface.
- The main engineering improvement is not "more agents"; it is better domain modeling, typed agent coordination, risk auditing, and experiment reproducibility.
- The 2025 ablation framework and actual labels are now in place, so the next meaningful upgrade is frozen-plan generation and metric-backed comparison.

Claims that should not be made yet:

- Do not claim final 2025 admission accuracy.
- Do not claim the LLM advisor improves outcomes until advisor/no-advisor ablation has been run on real labels.
- Do not claim RL/GRPO improves the recommendation policy until trained policies beat deterministic baselines on a held-out benchmark.

## Next Daily Milestone

The next day of work should focus on one of these:

1. Generate `logs/frozen_plans_2025.jsonl` with frozen full plans, candidate rows, and user profiles.
2. Run `backtest-2025` and `ablate-2025` on the frozen plans.
3. Produce a results table with Full, no-tradeoff, no-advisor, probability-only, safe-first, and history-tight-rank variants.
4. Convert the results into a short claim audit: what is proven, what is suggestive, and what remains unproven.
