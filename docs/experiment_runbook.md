# GaokaoAgent Experiment Runbook

This runbook keeps the project entrypoints small and auditable. The rule is:
use one CLI for checks, rollouts, pairwise data, orchestration evaluation, and
2025 backtesting.

## Unified CLI

From the repository root:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py --help
```

Available commands:

```text
smoke
rollout
build-pairwise
eval-orchestration
backtest-2025
quant-calibrate-2025
research-evidence-audit
quant-tune
quant-lab-register
ablate-2025
improvement-audit
next-iteration-plan
plan-quality-audit
parallel-worlds
report-quality-audit
intake-audit
expectation-packet
delivery-bundle
delivery-portfolio-audit
```

## Smoke Checks

Run the stable project checks:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py smoke --fail-fast
```

Run selected checks:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py smoke --tests test_tradeoff_policy_smoke.py test_backtest_2025_smoke.py --fail-fast
```

## Orchestration Experiments

Roll out supervisor traces:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py rollout --input logs\orchestration_cases.jsonl --output logs\orchestration_rollouts.jsonl
```

Build pairwise preferences:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py build-pairwise --input logs\orchestration_rollouts.jsonl --output logs\orchestration_pairwise.jsonl
```

Evaluate rollout behavior:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py eval-orchestration --rollouts logs\orchestration_rollouts.jsonl --output logs\orchestration_eval.json --report-md logs\orchestration_eval.md
```

## Deep Research Evidence

Slow-loop research now treats sources as structured evidence, not just prose.
Search results are converted into `EvidenceCard`-style records with
`source_type`, `confidence`, `source`, and `usable_for_prediction`. The final
research report must include a `引用与证据附录`; fallback/no-network cards are
marked as manual-verification-only and cannot support prediction claims.

Audit rule:

- Missing research report: reject.
- Missing citation appendix or evidence cards: reject.
- No official/semi-official source: pass with a warning and require manual
  official-source review before final fill-in.

Research evidence can now be converted into controlled quant features through
`derive_research_evidence_signals(...)`. The boundary is strict:

- official or semi-official cards may support policy, plan-change, quota, and
  major-group restructuring features.
- WeChat, livestream, creator, and social cards may support only market heat,
  sentiment shock, and rebound-risk features.
- manual-verification or fallback cards are reference-only and must not raise
  admission probability.

Before feeding search/deep-research output into quant features, audit the
evidence cards:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py research-evidence-audit --evidence-json logs\research_state.json --scope-term "Brand Institute" "801" --output logs\research_evidence_audit.json --report-md logs\research_evidence_audit.md
```

The audit blocks quant ingestion if social, WeChat, livestream, creator, or
manual-fallback evidence is marked `usable_for_prediction`. Official and
semi-official cards can become controlled signals only when they keep source
attribution, cutoff date, and scope terms clear.

## Benchmark Coverage Audit

Before trusting aggregate backtest metrics, audit whether the frozen case set
covers the user slices that matter for agency-grade claims:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py benchmark-coverage --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\benchmark_coverage.json --report-md logs\benchmark_coverage.md --repair-plan-output logs\benchmark_coverage_repair_plan.json --repair-plan-md logs\benchmark_coverage_repair_plan.md
```

Coverage checks include subject group, rank bands, city locks, narrow-region
families, blacklist and strict-major constraints, risk/tradeoff modes, high
major-cognition risk, regret sensitivity, and critical intersections such as
history boundary-rank families or boundary-rank families with hard blacklist
constraints. If coverage is `insufficient`, generate more frozen profiles
before making broad quality claims from the leaderboard.

The repair plan can be fed back into frozen-plan generation:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\generate_frozen_plans_2025.py --output logs\frozen_plans_2025_repaired.jsonl --num-cases 40 --coverage-repair-plan logs\benchmark_coverage_repair_plan.json
```

Repair profiles are prioritized before the regular rank grid/random samples, so
missing critical slices are represented in the next benchmark before aggregate
metrics are compared.

After generating repaired frozen plans, rerun coverage and compare the delta:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py benchmark-coverage --plans-jsonl logs\frozen_plans_2025_repaired.jsonl --output logs\benchmark_coverage_repaired.json --report-md logs\benchmark_coverage_repaired.md

backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py benchmark-coverage-compare --before logs\benchmark_coverage.json --after logs\benchmark_coverage_repaired.json --output logs\benchmark_coverage_compare.json --report-md logs\benchmark_coverage_compare.md
```

Only treat the repair as successful if coverage score improves without
regressing existing required tags or critical pairs.

## 2025 Backtest

The 2025 actual results are post-hoc labels. They must not be used during plan
generation.

Input plan JSONL format:

```json
{"case_id":"case_001","user_rank":12000,"preferred_majors":["计算机"],"blacklist_majors":["土木"],"plan":{ "...": "VolunteerPlan JSON" }}
```

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py backtest-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\backtest_2025_summary.json --results-jsonl logs\backtest_2025_results.jsonl
```

## Quant Calibration

Calibration checks whether prediction-time probabilities and quant risk bands
match post-hoc outcomes. This is the main loop for making the recommender more
like an agency-grade decision system instead of a narrative generator.

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py quant-calibrate-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --output logs\quant_calibration_summary.json --choice-rows-jsonl logs\quant_calibration_choices.jsonl --report-md logs\quant_calibration_report.md
```

Use the report to inspect:

- probability-bucket calibration
- quant-score bucket calibration
- deterministic risk-band monotonicity
- first-hit probability calibration
- tail-assignment and wasted-score rates by bucket

## Quant Tuning

Quant tuning searches transparent probability/scorecard blends from the
choice-level calibration rows. Treat its output as candidate parameters only;
validate candidates on a separate frozen-plan split before changing runtime
weights.

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py quant-tune --choice-rows-jsonl logs\quant_calibration_choices.jsonl --holdout-fraction 0.25 --output logs\quant_tuning_summary.json --report-md logs\quant_tuning_report.md
```

The objective is:

```text
brier + 0.35 * absolute_calibration_error + 0.20 * bucket_absolute_calibration_error
```

The tuner selects weights on the training split and reports holdout metrics
when there are enough cases. A candidate should not be adopted unless it also
improves the holdout split and a later independent frozen-plan run.

## 2025 Ablation

Ablation uses the same post-hoc 2025 labels, but rebuilds baseline plans from
the same frozen candidate pool. Each JSONL record must include `plan`,
`candidate_rows`, and `user_profile`:

```json
{"case_id":"case_001","user_rank":12000,"preferred_majors":["计算机"],"blacklist_majors":["土木"],"plan":{ "...": "VolunteerPlan JSON" },"candidate_rows":[{ "...": "MajorGroupRow JSON" }],"user_profile":{ "...": "UserProfile JSON" }}
```

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py ablate-2025 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --tuning-summary logs\quant_tuning_summary.json --output logs\ablation_2025_summary.json --results-jsonl logs\ablation_2025_results.jsonl --report-md logs\ablation_2025_report.md
```

Default variants:

```text
full
probability_only
history_tight_rank
safe_first
no_tradeoff_policy
```

When `--tuning-summary` is provided, ablation also adds
`quant_tuned_shadow`. This variant uses the `quant-tune` best weights to
reorder frozen candidate rows offline. It is a shadow test only; it does not
change runtime recommendation weights.

Ablation output also includes a `slice_scoreboard`. This is the main guardrail
against aggregate-metric traps. Inspect variant performance by subject group,
rank band, risk tolerance, school-vs-major tradeoff, region constraint, major
preference / blacklist constraint, major cognition risk, and regret
sensitivity. Do not promote a variant that improves the aggregate table while
harming boundary-rank, region-locked, or blacklist-sensitive families.

## QuantLab Registry

QuantLab registration turns separate experiment artifacts into one auditable
manifest. It records artifact hashes, metric digests, slice availability, and a
shadow promotion gate.

Run after backtest, calibration, tuning, ablation, and improvement audit:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py quant-lab-register --experiment-id exp_2026_0604_quant_shadow --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --benchmark-coverage logs\benchmark_coverage.json --backtest-summary logs\backtest_2025_summary.json --backtest-results-jsonl logs\backtest_2025_results.jsonl --calibration-summary logs\quant_calibration_summary.json --tuning-summary logs\quant_tuning_summary.json --ablation-summary logs\ablation_2025_summary.json --ablation-results-jsonl logs\ablation_2025_results.jsonl --improvement-audit logs\improvement_audit.json --output logs\quant_lab_manifest.json --report-md logs\quant_lab_report.md
```

Promotion gate rule:

```text
new variant may be promoted only if:
- success_rate is not worse than full
- blacklist_hit_rate does not worsen
- tail_assignment_rate rises by no more than 3 percentage points
- preferred_major_hit_rate or average_assigned_major_utility improves
- critical slices do not regress
```

QuantLab treats these as critical slices: boundary/lower rank, 60k-120k rank,
Guangdong or narrow-region locked families, major blacklist or strict-major
families, high major-cognition risk, regret-sensitive families, and
conservative-risk families. A candidate is blocked when these slices lose
success rate, increase blacklist rate, increase tail-assignment rate by more
than 5 percentage points, or lose preferred-major hit rate by more than 5
percentage points.

The standard experiment suite writes `quant_lab_manifest.json` and
`quant_lab_report.md` when 2025 outcome labels and frozen plans are provided.
It also mines `backtest_2025_results.jsonl` and `ablation_2025_results.jsonl`
for failure buckets, worst cases, and variant-level case regressions.

### QuantLab Leaderboard

Use the leaderboard when comparing many experiment folders instead of judging a
single run in isolation:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py quant-lab-leaderboard --manifest-glob "logs\experiments\*\quant_lab_manifest.json" --baseline-experiment-id exp_2026_0604_baseline --output logs\quant_lab_leaderboard.json --report-md logs\quant_lab_leaderboard.md
```

The leaderboard ranks runs by a conservative triage score that rewards success,
preferred-major hit, and assigned-major utility, while penalizing sliding,
blacklist hits, tail assignment, failure-case rate, calibration error, and
open P0 blockers. The score is not a production proof. It is a review surface:
top candidates still need replay-queue validation, critical-slice guardrails,
and delivery-quality checks before runtime adoption.

### Claim Readiness

Claim readiness translates one QuantLab manifest into allowed and forbidden
public claims:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py claim-readiness --quant-lab-manifest logs\quant_lab_manifest.json --output logs\claim_readiness.json --report-md logs\claim_readiness.md
```

Use the portfolio view when comparing many experiments or preparing any public
quality claim:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py claim-readiness-portfolio --claim-glob "logs\experiments\*\claim_readiness.json" --output logs\claim_readiness_portfolio.json --report-md logs\claim_readiness_portfolio.md
```

Use this before any public demo, sales page, interview claim, or family-facing
quality statement. It blocks agency-grade claims when benchmark coverage,
backtest size, success/sliding/blacklist/tail metrics, calibration, failure
replay, improvement blockers, or critical-slice guardrails are not strong
enough. A leaderboard rank is not sufficient by itself.

Failure buckets:

- `sliding`
- `blacklist_hit`
- `tail_assignment`
- `preferred_major_miss`
- `wasted_score`
- `missing_actual_outcome`

Use the worst-case list as the next replay queue before adopting any aggregate
metric improvement.

### Open-Source Quant Benchmark

The target operating model is closer to mature open-source quant systems than
to a one-shot chatbot:

- Qlib: full pipeline from data processing, model training, backtesting, alpha
  research, risk modeling, portfolio optimization, and execution.
- VectorBT: large-scale vectorized parameter sweeps and fast robustness checks
  before a strategy is trusted.
- Freqtrade: CLI-first workflow for data download, backtesting, analysis,
  hyperparameter optimization, and dry-run/live separation.
- LEAN: modular event-driven engine with local research, backtest, optimize,
  and live commands.

GaokaoAgent should translate these patterns into the admission domain:

- data bundle: frozen plan inputs, post-hoc actual outcomes, source-aware
  research evidence, and schema/version hashes
- strategy variants: full system, quant-only, no-advisor, no-critic,
  no-arbitrage, tuned-shadow, and future intake/report variants
- backtest engine: judge first hit, sliding, blacklist, tail assignment,
  preferred-major hit, score waste, and utility
- parameter search: tune scoring weights offline and validate on holdout
  before runtime adoption
- experiment registry: one manifest with artifact hashes, metric digest,
  promotion gate, failure mining, and replay queue
- replay loop: every worst case becomes a standard frozen-case queue for the
  next run
- delivery gate: client-facing reports must pass expectation, constraint, risk,
  evidence, and disclaimer checks before paid delivery

### Failure Replay Queue

Failure mining is now materialized into a JSONL replay artifact. Build it after
backtest and optional ablation:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py build-replay-queue --plans-jsonl logs\frozen_plans_2025.jsonl --backtest-results-jsonl logs\backtest_2025_results.jsonl --ablation-results-jsonl logs\ablation_2025_results.jsonl --output logs\failure_replay_queue.jsonl --summary-json logs\failure_replay_queue.json --report-md logs\failure_replay_queue.md
```

Each queued JSONL row preserves the original frozen plan record and adds
`replay_metadata`:

- priority: `P0`, `P1`, or `P2`
- failure reasons: sliding, blacklist hit, tail assignment, preferred-major
  miss, wasted score, or missing actual outcome
- source rows: backtest failure and/or ablation regression
- recommended focus: the subsystem that should be inspected in the next
  iteration

The standard experiment suite writes `failure_replay_queue.jsonl`,
`failure_replay_queue.json`, and `failure_replay_queue.md`. Use
`failure_replay_queue.jsonl` as the next `--plans-jsonl` when you need to
pressure-test a candidate fix on known hard cases before accepting aggregate
metric gains.

## Self-Improvement Audit

The improvement audit converts experiment metrics into prioritized engineering
work. It keeps the project aligned to the mission: make volunteer planning more
accessible while approaching the quality of top agencies and high-trust
counselors.

Run after backtest, calibration, research-evidence, and delivery-gate audits:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py improvement-audit --backtest-summary logs\backtest_2025_summary.json --backtest-results-jsonl logs\backtest_2025_results.jsonl --calibration-summary logs\quant_calibration_summary.json --tuning-summary logs\quant_tuning_summary.json --ablation-summary logs\ablation_2025_summary.json --ablation-results-jsonl logs\ablation_2025_results.jsonl --research-evidence-audit logs\research_evidence_audit.json --intake-audit logs\intake_audit.json --plan-quality-audit logs\plan_quality_audit.json --report-quality-audit logs\report_quality_audit.json --delivery-bundle logs\delivery_case_001\delivery_bundle.json --delivery-portfolio logs\delivery_portfolio_audit.json --output logs\improvement_audit.json --report-md logs\improvement_audit.md
```

The audit flags:

- P0 blockers before agency-grade claims
- intake-readiness and client-delivery blockers before paid-case delivery
- portfolio-level delivery blockers such as low ready-to-deliver rate or repeated failed gates
- volunteer-plan structural gaps such as weak safe anchors or hard-boundary violations
- generated-report gaps in risk explanation, evidence, actionability, and official review
- search/deep-research evidence blocked from quant ingestion
- calibration gaps that need probability correction
- tuning candidates that need holdout validation
- risk-band monotonicity failures
- baseline variants that beat the full system
- failure-mining buckets such as sliding, blacklist hit, tail assignment, preferred-major miss, wasted score, and missing actual labels
- ablation variants that introduce new case-level failures versus `full`

## Next Iteration Plan

Use this after the standard audits when you want one operator-facing plan for
the next experiment cycle:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py next-iteration-plan --improvement-audit logs\improvement_audit.json --coverage-repair-plan logs\benchmark_coverage_repair_plan.json --replay-queue-summary logs\failure_replay_queue.json --replay-queue-jsonl logs\failure_replay_queue.jsonl --delivery-bundle-glob "logs\delivery_*\delivery_bundle.json" --claim-readiness-portfolio logs\claim_readiness_portfolio.json --research-evidence-audit logs\research_evidence_audit.json --output logs\next_iteration_plan.json --report-md logs\next_iteration_plan.md
```

The plan merges P0/P1 findings, benchmark coverage repair specs, replay queue
focus areas, delivery-portfolio blockers, claim-readiness blockers, and
research-evidence blockers. Treat its commands as the starting point for the
next frozen-plan, replay, or delivery-portfolio review run.
- next actions for the next model iteration

## Plan Quality Audit

Plan quality audit checks the ordered volunteer plan itself, not the wording of
the final report. It verifies the structural gates expected from an
agency-grade counselor: overall admission security, safe anchors, risk-policy
consistent rush/target/safe balance, active key-prefix rows, tail and
adjustment risk, hard-boundary compliance, and evidence for key choices.

Run on a `VolunteerPlan` JSON:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py plan-quality-audit --plan-json logs\volunteer_plan.json --profile-json logs\user_profile.json --output logs\plan_quality_audit.json --report-md logs\plan_quality_audit.md
```

`--plan-json` may also point to a frozen record containing a top-level `plan`
field. Use this audit after recommendation generation and before report
delivery; use `backtest-2025` later for post-hoc outcome validation.

Status meanings:

- `blocked`: hard-boundary violation or severe structure problem; do not
  deliver without replacing or re-confirming rows.
- `needs_revision`: plan is usable for analysis but needs better safety,
  ordering, risk handling, or evidence before client delivery.
- `pass`: plan structure meets the deterministic delivery gate.

## Parallel Worlds

Parallel-world analysis stress-tests the same ordered volunteer plan under
explicit scenario branches. It follows the MiroFish-style idea of making
assumptions first-class: baseline, rank rebound, crowding heat, tail-major
worsening, safe-anchor slippage, and hidden-opportunity realization.

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py parallel-worlds --plan-json logs\volunteer_plan.json --profile-json logs\user_profile.json --output logs\parallel_worlds.json --report-md logs\parallel_worlds.md
```

Use it before final delivery to identify which external assumption breaks the
plan first. The output includes weighted pass rate, blocked rate, sensitive
worlds, and tripwires to watch before the real fill-in deadline.

## Report Quality Audit

Report quality audit checks whether a generated report has the delivery
elements expected from an agency-grade counselor: student context, constraint
confirmation, risk explanation, recommendation evidence, actionable fill-in
steps, expectation management, and official-data boundaries.

Run on Markdown:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py report-quality-audit --report-md logs\report.md --output logs\report_quality_audit.json --audit-md logs\report_quality_audit.md
```

Run on a `ReportDraft` JSON:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py report-quality-audit --report-json logs\report_draft.json --output logs\report_quality_audit.json --audit-md logs\report_quality_audit.md
```

## Intake Audit

Intake audit is the pre-recommendation gate. It checks whether a family has
provided enough information to start ranking choices: score, rank, subject
group, region boundary, major boundary, school-vs-major tradeoff, risk
tolerance, budget/pathway constraints, preference cognition, and official
restriction review.

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py intake-audit --profile-json logs\user_profile.json --output logs\intake_audit.json --report-md logs\intake_audit.md
```

Status meanings:

- `blocked_missing_core`: do not recommend yet; score, rank, or subject-group
  information is missing.
- `needs_clarification`: ask the generated clarification questions before
  freezing the recommendation input.
- `ready_for_recommendation`: candidate-pool generation can start, while final
  delivery still requires expectation sign-off and official-data review.

## Expectation Packet

Expectation packets are pre-recommendation delivery artifacts. They reduce
post-service disputes by making constraints, unknowns, risk tolerance, and
non-guarantee boundaries explicit before the final plan is accepted.

Input is a `UserProfile` JSON:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py expectation-packet --profile-json logs\user_profile.json --output logs\expectation_packet.json --report-md logs\expectation_packet.md
```

Use this before final recommendation delivery when the family has hard limits
such as "省内 only", "不接受民办", "不接受中外合作", "专业黑名单", or a strong
school-vs-major tradeoff preference. The packet includes a structured
client-signoff checklist for constraint freeze, adjustment/tail risk,
private/joint-program fee pathways, non-guarantee terms, and final official
review.

## Delivery Bundle

Delivery bundles package the intake audit, volunteer-plan quality audit,
expectation packet, final report, and report quality audit into one
client-facing folder. This is the operational delivery gate for a paid or
high-stakes case.

Run:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py delivery-bundle --profile-json logs\user_profile.json --plan-json logs\volunteer_plan.json --report-md logs\report.md --output-dir logs\delivery_case_001 --case-id case_001
```

The bundle writes:

- `intake_audit.md`
- `intake_audit.json`
- `plan_quality_audit.md`
- `plan_quality_audit.json`
- `expectation_packet.md`
- `final_report.md`
- `report_quality_audit.md`
- `delivery_bundle.md`
- `delivery_bundle.json`

Bundle status can be `blocked`, `needs_revision`, `pending_signoff`, or
`ready_to_deliver`. Missing `--plan-json` is treated as `needs_revision`
because a final paid-case handoff must include a structural audit of the
ordered volunteer plan. The bundle manifest also carries
`client_signoff_checklist` so internal tools can verify which customer
signatures are required before family-facing delivery.

## Delivery Portfolio Audit

Delivery portfolio audit aggregates many `delivery_bundle.json` manifests into
service-quality metrics. Use it after a batch of paid or trial cases to see
which gate repeatedly blocks delivery.

The web app also includes an internal batch review panel. Single-case delivery
previews generated in the current browser session are added automatically. The
panel can also load recent local manifests from `backend/logs/delivery_bundles`
or accept older `delivery_bundle.json` manifests pasted as a JSON array or
JSONL.

Run with explicit bundle manifests:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py delivery-portfolio-audit --bundle-json logs\delivery_case_001\delivery_bundle.json logs\delivery_case_002\delivery_bundle.json --output logs\delivery_portfolio_audit.json --report-md logs\delivery_portfolio_audit.md
```

Run with a glob:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\gaokao_agent.py delivery-portfolio-audit --bundle-glob "logs\delivery_*\delivery_bundle.json" --output logs\delivery_portfolio_audit.json --report-md logs\delivery_portfolio_audit.md
```

The audit reports ready-to-deliver rate, blocked rate, client-delivery allowed
rate, client-delivery blocked reasons, average intake/plan/report scores, top
failed gates, repeated next actions, and worst cases. Treat repeated failed
gates as product work, not one-off customer-service noise.

## One-Shot Suite

Use this when you want one command to create an experiment folder:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\run_experiment_suite.py --output-dir logs\experiments\run_001 --cases logs\orchestration_cases.jsonl --limit 20
```

Add post-hoc 2025 evaluation when frozen plans and actual outcomes are ready:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\run_experiment_suite.py --output-dir logs\experiments\run_001 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl
```

Add ablation when the frozen plan records also contain candidate rows and user
profiles:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\run_experiment_suite.py --output-dir logs\experiments\run_001 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --run-ablation
```

Add deep-research evidence when search output should be audited and fed into
the same improvement queue:

```powershell
backend\.venv\Scripts\python.exe backend\scripts\run_experiment_suite.py --output-dir logs\experiments\run_001 --actual-outcomes data\actual_2025.csv --plans-jsonl logs\frozen_plans_2025.jsonl --research-evidence-json logs\research_state.json --research-scope-term "Brand Institute" "801"
```

When actual outcomes and frozen plans are provided, the suite also writes
`benchmark_coverage.json`, `benchmark_coverage.md`,
`benchmark_coverage_repair_plan.json`,
`benchmark_coverage_repair_plan.md`,
`benchmark_coverage_compare.json` when a before/after repair comparison is run,
`quant_calibration_summary.json`, `quant_calibration_report.md`,
`quant_tuning_summary.json`, `quant_tuning_report.md`,
`improvement_audit.json`, `improvement_audit.md`,
`failure_replay_queue.jsonl`, `failure_replay_queue.json`, and
`failure_replay_queue.md`, plus `quant_lab_leaderboard.json` and
`quant_lab_leaderboard.md`, `claim_readiness.json`, and
`claim_readiness.md`, plus `claim_readiness_portfolio.json` and
`claim_readiness_portfolio.md`, plus `next_iteration_plan.json` and
`next_iteration_plan.md`.

When `--research-evidence-json` or `--research-evidence-glob` is provided, the
suite also writes `research_evidence_audit.json` and
`research_evidence_audit.md`, then passes that audit into
`improvement_audit.json`.

## Claim-Evidence Mapping

Use these outputs for project claims:

| Claim | Evidence artifact |
| --- | --- |
| Frozen benchmark covers critical user slices | `benchmark_coverage.json`, `benchmark_coverage.md` |
| Recommendation core is backtestable | `backtest_2025_summary.json`, `backtest_2025_results.jsonl` |
| Admission probabilities and quant risk bands are calibrated | `quant_calibration_summary.json`, `quant_calibration_report.md` |
| Candidate quant weights are being searched offline | `quant_tuning_summary.json`, `quant_tuning_report.md` |
| Candidate quant weights improve frozen-plan ordering before runtime adoption | `ablation_2025_summary.json`, `ablation_2025_report.md` with `quant_tuned_shadow` |
| Case intake is complete enough to begin recommendation | `intake_audit.json`, `intake_audit.md` |
| Volunteer-plan structure meets agency-grade gates | `plan_quality_audit.json`, `plan_quality_audit.md` |
| Plan robustness across parallel-world assumptions is known | `parallel_worlds.json`, `parallel_worlds.md` |
| Generated reports meet delivery-quality gates | `report_quality_audit.json`, `report_quality_audit.md` |
| Client constraints and expectation boundaries are confirmed | `expectation_packet.json`, `expectation_packet.md` |
| Client-facing delivery is packaged consistently | `delivery_bundle.json`, `delivery_bundle.md` |
| Batch delivery quality is improving over cases | `delivery_portfolio_audit.json`, `delivery_portfolio_audit.md` |
| External research is auditable and source-aware | `research_evidence_cards`, `引用与证据附录` in `research_report` |
| Search/deep-research evidence is safe for quant ingestion | `research_evidence_audit.json`, `research_evidence_audit.md` |
| Agentic orchestration is not decorative | `orchestration_rollouts.jsonl`, `orchestration_eval.json` |
| RL/reward direction has trainable traces | `orchestration_pairwise.jsonl` |
| LLM components can be ablated | compare runs with `ENABLE_LLM_ADVISORS` / `ENABLE_LLM_CRITIC` on and off |
| Tradeoff/re-ranking choices improve 2025 outcomes | `ablation_2025_summary.json`, `ablation_2025_report.md` |
| The next iteration is metric-driven | `improvement_audit.json`, `improvement_audit.md` |
| The next experiment run is operationalized from audits | `next_iteration_plan.json`, `next_iteration_plan.md` |
| Known failures are replayable | `failure_replay_queue.jsonl`, `failure_replay_queue.md` |
| Multiple experiments can be compared | `quant_lab_leaderboard.json`, `quant_lab_leaderboard.md` |
| Public quality claims are bounded by evidence | `claim_readiness.json`, `claim_readiness.md` |
| Public claim readiness is monitored across experiments | `claim_readiness_portfolio.json`, `claim_readiness_portfolio.md` |
