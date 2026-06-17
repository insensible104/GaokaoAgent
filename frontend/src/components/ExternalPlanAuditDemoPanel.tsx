import React from "react";
import { ExternalPlanComparator } from "./ExternalPlanComparator";
import type { GameMatrix } from "./GameMatrixView";

const demoGameMatrix: GameMatrix = {
  major_group_rows: [
    {
      school_name: "SouthChinaTech",
      major_group_code: "202",
      major_list: ["Computer Science", "Software Engineering", "Automation"],
      major_count: 3,
      admission_prob: 0.42,
      raw_admission_prob: 0.39,
      probability_is_calibrated: true,
      probability_method: "historical_rank_calibration",
      probability_calibration_year: 2025,
      min_rank_pred: 21500,
      rank_ci_lower: 19500,
      rank_ci_upper: 23800,
      volatility: "medium",
      adjustment_risk: 0.18,
      worst_case_major: "Automation",
      is_blacklist_risk: false,
      strategy_tag: "rush",
      choice_index: 1,
      first_hit_prob: 0.42,
      cumulative_hit_prob: 0.42,
      prefix_role: "key_result",
      is_key_prefix: true,
      tail_assignment_risk: 0.18,
      quant_score: 0.71,
      rank_buffer_score: 0.46,
      data_confidence_score: 0.72,
      deterministic_risk_band: "review",
      quant_evidence: [
        "2025 rank calibration is present.",
        "Professional-group tail assignment risk is below the manual review threshold.",
      ],
    },
    {
      school_name: "GuangdongIndustry",
      major_group_code: "205",
      major_list: ["Data Science", "Industrial Design", "Information Management"],
      major_count: 3,
      admission_prob: 0.67,
      raw_admission_prob: 0.63,
      probability_is_calibrated: true,
      probability_method: "historical_rank_calibration",
      probability_calibration_year: 2025,
      min_rank_pred: 26800,
      rank_ci_lower: 24500,
      rank_ci_upper: 29400,
      volatility: "low",
      adjustment_risk: 0.12,
      worst_case_major: "Information Management",
      is_blacklist_risk: false,
      strategy_tag: "target",
      choice_index: 2,
      first_hit_prob: 0.39,
      cumulative_hit_prob: 0.65,
      prefix_role: "active_backup",
      is_key_prefix: true,
      tail_assignment_risk: 0.12,
      quant_score: 0.78,
      rank_buffer_score: 0.64,
      data_confidence_score: 0.76,
      deterministic_risk_band: "usable",
      quant_evidence: [
        "Target row has calibrated probability and acceptable volatility.",
        "No explicit blacklist conflict is detected.",
      ],
    },
    {
      school_name: "FoshanScienceTech",
      major_group_code: "204",
      major_list: ["Electronic Information", "Mechanical Engineering", "Materials"],
      major_count: 3,
      admission_prob: 0.86,
      raw_admission_prob: 0.82,
      probability_is_calibrated: true,
      probability_method: "historical_rank_calibration",
      probability_calibration_year: 2025,
      min_rank_pred: 34800,
      rank_ci_lower: 32100,
      rank_ci_upper: 37600,
      volatility: "low",
      adjustment_risk: 0.08,
      worst_case_major: "Materials",
      is_blacklist_risk: false,
      strategy_tag: "safe",
      choice_index: 3,
      first_hit_prob: 0.3,
      cumulative_hit_prob: 0.9,
      prefix_role: "safety_anchor",
      is_key_prefix: false,
      tail_assignment_risk: 0.08,
      quant_score: 0.74,
      rank_buffer_score: 0.82,
      data_confidence_score: 0.74,
      deterministic_risk_band: "usable",
      quant_evidence: [
        "Safe row keeps a meaningful rank buffer.",
        "Tail-major risk remains visible before counselor signoff.",
      ],
    },
  ],
  rows: [],
  total_rush: 1,
  total_target: 1,
  total_safe: 1,
  expected_utility: 0.74,
  portfolio_risk: 0.23,
  is_balanced: true,
  selection_method: "public_demo_static_case",
  volunteer_plan: {
    expected_admission_prob: 0.9,
    admission_probability_lower_bound: 0.78,
    admission_probability_upper_bound: 0.95,
    probability_method: "demo_calibrated",
    probability_is_calibrated: true,
    probability_calibration_year: 2025,
    expected_first_hit_utility: 0.74,
    expected_tail_risk: 0.13,
    key_prefix_count: 2,
    key_choice_indexes: [1, 2],
    shadowed_choice_count: 0,
    plan_summary: "Static public demo case for external-plan audit.",
  },
  data_vintage: {
    target_year: 2026,
    latest_historical_admission_year: 2025,
    enrollment_plan_year: 2026,
    rank_table_year: 2025,
    formal_recommendation_ready: false,
    limitations: ["Demo data is illustrative and must not be used for final submission."],
  },
};

const externalPlanText = [
  "rush SouthChinaTech 202",
  "target GuangdongIndustry 205",
  "safe UnknownSafeCollege 901",
  "UnknownNoTagSchool 777",
].join("\n");

export const ExternalPlanAuditDemoPanel: React.FC = () => (
  <div className="space-y-5">
    <section className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-xs font-semibold uppercase text-indigo-700">PathFinder Lite demo</p>
      <h1 className="mt-2 text-3xl font-bold text-slate-950">External plan audit</h1>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-slate-700">
        Paste a Qwen, family, teacher, or peer project plan and compare it against a structured PathFinder slate.
        This public demo checks overlap, missing safe anchors, duplicate rows, and review actions. It does not turn
        demo evidence into a final admissions claim.
      </p>
    </section>
    <ExternalPlanComparator gameMatrix={demoGameMatrix} initialText={externalPlanText} />
  </div>
);

export default ExternalPlanAuditDemoPanel;
