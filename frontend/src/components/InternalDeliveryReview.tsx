import { useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ClipboardCheck,
  FileDown,
  FileText,
  ShieldAlert,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { buildApiUrl } from "@/lib/api";
import { ReviewedEvidenceCaseBrowserPanel } from "@/components/ReviewedEvidenceCaseBrowserPanel";
import { buildDeliveryReviewedEvidencePlan } from "@/lib/deliveryReviewedEvidencePlan";
import { fetchReviewedEvidenceRecords, type ReviewedEvidenceRecord } from "@/lib/evidenceAutopilotApi";
import {
  buildOperatorEvidenceCaptureGate,
  buildOperatorEvidenceCaptureWorklist,
} from "@/lib/operatorEvidenceCaptureWorklist";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { GameMatrix, MajorGroupRow } from "@/components/GameMatrixView";

interface DeliveryProfile {
  score: number;
  rank?: number;
  subject_group: string;
  preferred_cities?: string[];
  excluded_cities?: string[];
  preferred_majors?: string[];
  blacklist_majors?: string[];
  risk_tolerance?: string;
  school_major_preference?: string;
  stated_misconceptions?: string[];
  emotional_concerns?: string[];
  family_pressure_points?: string[];
  preference_assumptions?: string[];
  preference_confidence?: number;
  major_cognition_risk?: number;
  regret_sensitivity?: number;
  medical_restrictions?: Record<string, boolean>;
  subject_scores?: Record<string, number>;
  holland_code?: Record<string, number>;
  riasec_top_codes?: string[];
  career_assessment_mode?: string;
  career_assessment_status?: string;
  mbti_type?: string;
  mbti_source?: string;
  career_values?: string[];
  field_provenance?: Record<string, string>;
}

export interface DeliveryManifest {
  case_id?: string;
  status: string;
  intake_status?: string;
  intake_readiness_score?: number;
  plan_quality_status?: string;
  plan_quality_score?: number;
  expectation_status?: string;
  report_quality_status?: string;
  report_quality_score?: number;
  client_delivery?: {
    allowed: boolean;
    status: string;
    artifact_audiences?: string[];
    blocked_reason?: string;
  };
  artifacts?: Array<{
    id: string;
    label: string;
    path: string;
    required: boolean;
    audience?: "internal_review" | "client_confirmation" | "client_final" | string;
  }>;
  delivery_gates?: Array<{
    gate: string;
    status: string;
    requirement: string;
  }>;
  next_actions?: string[];
}

interface DeliveryPreview {
  success: boolean;
  message: string;
  case_id: string;
  output_dir: string;
  manifest: DeliveryManifest;
  artifacts: Record<string, string>;
}

interface AgencyCommandCenter {
  success: boolean;
  message: string;
  scanned_bundle_count: number;
  audit: {
    status: string;
    north_star: {
      case_count: number;
      ready_to_deliver_rate: number;
      blocked_rate: number;
      average_scores?: Record<string, number>;
    };
    institution_health_scorecard: {
      overall_status: string;
      next_management_decision: string;
      scorecard_standard: string;
      dimensions: Array<{
        dimension: string;
        label: string;
        score: number;
        status: string;
        signal: string;
        management_question: string;
        next_action: string;
      }>;
    };
    pain_points: Array<{
      priority: string;
      gate: string;
      pain_point: string;
      affected_case_count: number;
      affected_rate: number;
      operator_response: string;
    }>;
    executive_decision: {
      decision: string;
      priority: string;
      summary: string;
      allowed_claims: string[];
      blocked_claims: string[];
      required_evidence: string[];
      review_cadence: string;
    };
    client_pain_radar: Array<{
      priority: string;
      gate: string;
      affected_case_count: number;
      affected_rate: number;
      user_symptom: string;
      user_pain: string;
      advisor_opening: string;
      proof_to_show: string[];
      success_signal: string;
      risk_if_ignored: string;
      source_pain_point: string;
    }>;
    proof_gap_ledger: {
      status: string;
      item_count: number;
      ledger_standard: string;
      items: Array<{
        gap_id: string;
        priority: string;
        gate: string;
        owner: string;
        review_cadence: string;
        missing_proof: string[];
        client_risk: string;
        why_it_matters: string;
        evidence_standard: string;
        success_signal: string;
        unblocks_claims: string[];
      }>;
    };
    communication_guardrails: {
      status: string;
      guardrail_standard: string;
      cards: Array<{
        priority: string;
        gate: string;
        approved_opening: string;
        must_disclose: string[];
        forbidden_language: string[];
        proof_before_claim: string[];
        escalate_when: string[];
        safe_close: string;
      }>;
    };
    advisor_lead_brief: Array<{
      priority: string;
      focus: string;
      why: string;
    }>;
    advisor_playbook: Array<{
      priority: string;
      gate: string;
      handoff_stage: string;
      trigger: string;
      affected_case_count: number;
      affected_rate: number;
      manager_sop: Array<{ owner: string; step: string }>;
      intake_questions: string[];
      client_language: string;
      acceptance_evidence: string[];
    }>;
    advisor_training_plan: {
      status: string;
      modules: Array<{
        module_id: string;
        priority: string;
        source_gate: string;
        title: string;
        learning_objective: string;
        practice_drill: string;
        qa_rubric: Array<{ criterion: string; standard: string }>;
      }>;
      operating_cadence: Array<{
        cadence: string;
        owner: string;
        action: string;
      }>;
      pass_condition: string;
    };
    action_register: {
      status: string;
      item_count: number;
      register_standard: string;
      items: Array<{
        action_id: string;
        priority: string;
        source: string;
        owner: string;
        cadence: string;
        action: string;
        why: string;
        success_metric: string;
      }>;
    };
    case_rescue_queue: {
      status: string;
      item_count: number;
      queue_standard: string;
      items: Array<{
        rescue_id: string;
        priority: string;
        case_id: string;
        status: string;
        portfolio_score: number;
        failed_gates: string[];
        owner: string;
        cadence: string;
        rescue_steps: string[];
        client_update_script: string;
        do_not_release_until: string[];
        escalation_reason: string;
      }>;
    };
    escalation_queue: Array<{
      case_id: string;
      status: string;
      portfolio_score: number;
      failed_gates?: Array<{ gate: string; status: string }>;
    }>;
  };
  markdown: string;
}

interface InternalDeliveryReviewProps {
  profile: DeliveryProfile | null;
  report: string | null;
  gameMatrix?: GameMatrix | null;
  onManifestGenerated?: (manifest: DeliveryManifest) => void;
}

interface VolunteerMajorPayload {
  school_code: string;
  school_name: string;
  major_group_code: string;
  major_name: string;
  is_preferred?: boolean;
  is_acceptable?: boolean;
  is_blacklisted?: boolean;
  user_utility?: number;
  major_rank_risk?: number;
}

interface VolunteerChoicePayload {
  choice_index: number;
  school_code: string;
  school_name: string;
  major_group_code: string;
  major_choices: VolunteerMajorPayload[];
  obey_adjustment: boolean;
  adjustment_advice: "recommend" | "cautious" | "avoid";
  group_admission_prob: number;
  expected_major_utility: number;
  worst_case_major?: string | null;
  tail_assignment_risk: number;
  strategy_tag: "rush" | "target" | "safe";
  explanation: string;
  quant_evidence: string[];
}

interface VolunteerPlanPayload {
  province: string;
  year: number;
  subject_group: string;
  user_score?: number;
  user_rank?: number;
  choices: VolunteerChoicePayload[];
}

const statusLabel: Record<string, string> = {
  ready_to_deliver: "可交付",
  pending_signoff: "待确认",
  needs_revision: "需修订",
  blocked: "阻塞",
  blocked_missing_core: "阻塞",
  ready_for_recommendation: "已就绪",
  needs_clarification: "待澄清",
  not_provided: "未提供",
  pass: "通过",
  blocked_for_scale: "规模阻塞",
  needs_operational_iteration: "需运营迭代",
  needs_targeted_iteration: "需定向迭代",
  on_track: "正常推进",
  no_cases: "暂无案源",
  collect_evidence_before_scaling: "先收证据",
  hold_scale: "暂停放大",
  targeted_iteration: "定向迭代",
  scale_with_monitoring: "监控放大",
  critical_attention: "关键关注",
  needs_management_review: "主管复盘",
  healthy_with_monitoring: "健康监控",
  collect_cases_first: "先收案源",
  daily: "每日复盘",
  twice_weekly: "每周两次",
  weekly: "每周复盘",
};

const CLIENT_FACING_ARTIFACT_IDS = new Set(["expectation_packet", "final_report"]);
const CLIENT_FACING_AUDIENCES = new Set(["client_confirmation", "client_final"]);
const OPERATOR_CAPTURE_WORKFLOW = "captureAndSubmitOperatorReviewedEvidence";

function statusTone(status: string | undefined) {
  if (!status) return "border-slate-300 bg-slate-50 text-slate-700";
  if (["ready_to_deliver", "ready_for_recommendation", "pass", "on_track", "green"].includes(status)) {
    return "border-emerald-300 bg-emerald-50 text-emerald-700";
  }
  if (
    [
      "pending_signoff",
      "needs_clarification",
      "not_provided",
      "needs_operational_iteration",
      "needs_targeted_iteration",
      "yellow",
    ].includes(status)
  ) {
    return "border-amber-300 bg-amber-50 text-amber-700";
  }
  return "border-red-300 bg-red-50 text-red-700";
}

function percent(value: number | undefined) {
  if (value === undefined || Number.isNaN(value)) return "--";
  return `${Math.round(value * 100)}%`;
}

function artifactTitle(id: string) {
  const labels: Record<string, string> = {
    delivery_bundle: "交付包索引",
    intake_audit: "问诊审计",
    expectation_packet: "预期确认单",
    plan_quality_audit: "志愿表质检",
    report_quality_audit: "报告质检",
    final_report: "最终报告",
  };
  return labels[id] || id;
}

function downloadMarkdown(filename: string, content: string) {
  const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 100);
}

function boundedNumber(value: unknown, fallback: number, min = 0, max = 1) {
  if (typeof value !== "number" || Number.isNaN(value)) return fallback;
  return Math.max(min, Math.min(max, value));
}

function stringFromRecord(value: unknown, key: string) {
  if (!value || typeof value !== "object" || Array.isArray(value)) return "";
  const item = (value as Record<string, unknown>)[key];
  return typeof item === "string" ? item : "";
}

function majorFromRecord(
  value: unknown,
  row: MajorGroupRow,
  profile: DeliveryProfile
): VolunteerMajorPayload | null {
  if (!value || typeof value !== "object" || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const majorName = typeof record.major_name === "string" ? record.major_name : "";
  if (!majorName) return null;
  return {
    school_code: stringFromRecord(record, "school_code") || row.school_code || "",
    school_name: stringFromRecord(record, "school_name") || row.school_name,
    major_group_code: stringFromRecord(record, "major_group_code") || row.major_group_code,
    major_name: majorName,
    is_preferred: (profile.preferred_majors || []).some((major) => majorName.includes(major)),
    is_acceptable: record.is_acceptable !== false,
    is_blacklisted:
      record.is_blacklisted === true ||
      (profile.blacklist_majors || []).some((major) => majorName.includes(major)),
    user_utility: boundedNumber(record.user_utility, row.major_utility_mean ?? 0.55),
    major_rank_risk: boundedNumber(record.major_rank_risk, row.tail_assignment_risk ?? row.adjustment_risk),
  };
}

function fallbackMajors(row: MajorGroupRow, profile: DeliveryProfile): VolunteerMajorPayload[] {
  const structured = [...(row.suggested_major_choices || []), ...(row.major_options || [])]
    .map((item) => majorFromRecord(item, row, profile))
    .filter((item): item is VolunteerMajorPayload => item !== null)
    .slice(0, 6);
  if (structured.length > 0) return structured;

  const majors = row.major_list.length > 0
    ? row.major_list.slice(0, 6)
    : [row.worst_case_major || "待人工复核专业"];
  return majors.map((majorName) => ({
    school_code: row.school_code || "",
    school_name: row.school_name,
    major_group_code: row.major_group_code,
    major_name: majorName,
    is_preferred: (profile.preferred_majors || []).some((major) => majorName.includes(major)),
    is_acceptable: !(profile.blacklist_majors || []).some((major) => majorName.includes(major)),
    is_blacklisted:
      (row.is_blacklist_risk && majorName === row.worst_case_major) ||
      (profile.blacklist_majors || []).some((major) => majorName.includes(major)),
    user_utility: boundedNumber(row.major_utility_mean, row.strategy_tag === "safe" ? 0.62 : 0.70),
    major_rank_risk: boundedNumber(row.tail_assignment_risk ?? row.adjustment_risk, 0.20),
  }));
}

function buildPlanFromGameMatrix(
  profile: DeliveryProfile | null,
  gameMatrix?: GameMatrix | null
): VolunteerPlanPayload | Record<string, unknown> | undefined {
  if (!profile || !gameMatrix) return undefined;
  if (gameMatrix.volunteer_plan && typeof gameMatrix.volunteer_plan === "object") {
    const rawPlan = gameMatrix.volunteer_plan as Record<string, unknown>;
    return {
      ...rawPlan,
      subject_group: stringFromRecord(rawPlan, "subject_group") || profile.subject_group,
      user_score: Number(rawPlan.user_score ?? profile.score),
      user_rank: rawPlan.user_rank || profile.rank ? Number(rawPlan.user_rank ?? profile.rank) : undefined,
    };
  }

  const rows = [...(gameMatrix.major_group_rows || [])]
    .sort((left, right) => (left.choice_index || 999) - (right.choice_index || 999))
    .slice(0, 45);
  if (rows.length === 0) return undefined;

  return {
    province: "广东",
    year: 2025,
    subject_group: profile.subject_group,
    user_score: profile.score,
    user_rank: profile.rank,
    choices: rows.map((row, index) => ({
      choice_index: row.choice_index || index + 1,
      school_code: row.school_code || "",
      school_name: row.school_name,
      major_group_code: row.major_group_code,
      major_choices: fallbackMajors(row, profile),
      obey_adjustment: row.obey_adjustment ?? true,
      adjustment_advice:
        row.adjustment_advice ||
        (row.adjustment_risk >= 0.55
          ? "avoid"
          : row.adjustment_risk >= 0.32
            ? "cautious"
            : "recommend"),
      group_admission_prob: boundedNumber(row.admission_prob, 0),
      expected_major_utility: boundedNumber(row.major_utility_mean, row.strategy_tag === "safe" ? 0.62 : 0.72),
      worst_case_major: row.worst_case_major,
      tail_assignment_risk: boundedNumber(row.tail_assignment_risk ?? row.adjustment_risk, 0),
      strategy_tag: row.strategy_tag,
      explanation:
        row.tradeoff_summary ||
        row.risk_reasons?.join("；") ||
        `基于录取概率、位次区间、调剂风险和${row.strategy_tag}策略标签生成。`,
      quant_evidence: row.quant_evidence || [
        `admission_prob=${row.admission_prob.toFixed(3)}`,
        `min_rank_pred=${row.min_rank_pred}`,
        `rank_ci=${row.rank_ci_lower}-${row.rank_ci_upper}`,
      ],
    })),
  };
}

export function InternalDeliveryReview({
  profile,
  report,
  gameMatrix,
  onManifestGenerated,
}: InternalDeliveryReviewProps) {
  const [preview, setPreview] = useState<DeliveryPreview | null>(null);
  const [commandCenter, setCommandCenter] = useState<AgencyCommandCenter | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isPortfolioLoading, setIsPortfolioLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolioError, setPortfolioError] = useState<string | null>(null);
  const [reviewedEvidenceRecords, setReviewedEvidenceRecords] = useState<ReviewedEvidenceRecord[]>([]);
  const [reviewedEvidenceError, setReviewedEvidenceError] = useState<string | null>(null);

  const canRun = Boolean(profile?.score && profile?.subject_group && report);
  const plan = useMemo(() => buildPlanFromGameMatrix(profile, gameMatrix), [profile, gameMatrix]);
  const reviewedEvidencePlan = useMemo(
    () => buildDeliveryReviewedEvidencePlan({ profile, gameMatrix }),
    [profile, gameMatrix]
  );
  const operatorCaptureWorklist = useMemo(() => {
    const caseId = preview?.manifest.case_id || preview?.case_id;
    if (!caseId) return null;
    return buildOperatorEvidenceCaptureWorklist({
      caseId,
      plan: reviewedEvidencePlan,
      records: reviewedEvidenceRecords,
    });
  }, [preview, reviewedEvidencePlan, reviewedEvidenceRecords]);
  const operatorCaptureGate = useMemo(
    () => (operatorCaptureWorklist ? buildOperatorEvidenceCaptureGate(operatorCaptureWorklist) : null),
    [operatorCaptureWorklist]
  );
  const orderedArtifacts = useMemo(() => {
    if (!preview) return [];
    const preferredOrder = [
      "delivery_bundle",
      "intake_audit",
      "expectation_packet",
      "plan_quality_audit",
      "report_quality_audit",
      "final_report",
    ];
    return Object.entries(preview.artifacts).sort(
      ([left], [right]) => preferredOrder.indexOf(left) - preferredOrder.indexOf(right)
    );
  }, [preview]);
  const clientFacingArtifacts = useMemo(
    () => {
      const artifactAudienceById = new Map(
        (preview?.manifest.artifacts || []).map((artifact) => [artifact.id, artifact.audience])
      );
      return orderedArtifacts.filter(([id]) => {
        const audience = artifactAudienceById.get(id);
        if (audience) return CLIENT_FACING_AUDIENCES.has(audience);
        return CLIENT_FACING_ARTIFACT_IDS.has(id);
      });
    },
    [orderedArtifacts, preview]
  );
  const clientDeliveryAllowed =
    (preview?.manifest.client_delivery?.allowed ?? true) && !(operatorCaptureGate?.blocksClientDelivery ?? false);
  const clientDeliveryBlockedReason =
    (operatorCaptureGate?.blocksClientDelivery ? operatorCaptureGate.blockedReason : undefined) ||
    preview?.manifest.client_delivery?.blocked_reason ||
    "客户确认包暂不可下载，请先修订内部质检问题。";

  function downloadCombinedBundle() {
    if (!preview || orderedArtifacts.length === 0) return;
    const content = [
      `# GaokaoAgent 交付预检包`,
      "",
      `Case: ${preview.case_id}`,
      `Status: ${preview.manifest.status}`,
      "",
      ...orderedArtifacts.flatMap(([id, artifact]) => [
        "---",
        "",
        `# ${artifactTitle(id)}`,
        "",
        artifact.trim(),
        "",
      ]),
    ].join("\n");
    downloadMarkdown(`${preview.case_id}-delivery-preview.md`, content);
  }

  function downloadClientBundle() {
    if (!preview || clientFacingArtifacts.length === 0) return;
    const content = [
      `# GaokaoAgent 客户确认包`,
      "",
      `Case: ${preview.case_id}`,
      "",
      ...clientFacingArtifacts.flatMap(([id, artifact]) => [
        "---",
        "",
        `# ${artifactTitle(id)}`,
        "",
        artifact.trim(),
        "",
      ]),
    ].join("\n");
    downloadMarkdown(`${preview.case_id}-client-confirmation.md`, content);
  }

  async function runReview() {
    if (!profile || !report) return;
    setIsLoading(true);
    setError(null);
    setReviewedEvidenceRecords([]);
    setReviewedEvidenceError(null);

    try {
      const response = await fetch(buildApiUrl("/api/delivery/preview"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          profile,
          report,
          plan,
          case_id: `web-${profile.subject_group}-${profile.rank || profile.score}`,
        }),
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `交付预检失败 (${response.status})`);
      }

      const nextPreview: DeliveryPreview = await response.json();
      setPreview(nextPreview);
      onManifestGenerated?.(nextPreview.manifest);
      const reviewedEvidenceCaseId = nextPreview.manifest.case_id || nextPreview.case_id;
      try {
        const listing = await fetchReviewedEvidenceRecords({ caseId: reviewedEvidenceCaseId });
        setReviewedEvidenceRecords(listing.records);
      } catch (reviewedEvidenceErr) {
        const reason = reviewedEvidenceErr instanceof Error ? reviewedEvidenceErr.message : String(reviewedEvidenceErr);
        setReviewedEvidenceError(`operator-review ledger unavailable: ${reason}`);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "交付预检失败");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadCommandCenter() {
    setIsPortfolioLoading(true);
    setPortfolioError(null);

    try {
      const response = await fetch(buildApiUrl("/api/delivery/portfolio"));

      if (!response.ok) {
        const body = await response.text();
        throw new Error(body || `机构全局视图加载失败 (${response.status})`);
      }

      setCommandCenter(await response.json());
    } catch (err) {
      setPortfolioError(err instanceof Error ? err.message : "机构全局视图加载失败");
    } finally {
      setIsPortfolioLoading(false);
    }
  }

  return (
    <section className="rounded-xl border border-slate-300 bg-white p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-2 text-slate-900">
            <ClipboardCheck className="size-5 text-cyan-700" aria-hidden="true" />
            <h2 className="text-xl font-semibold">内部交付预检</h2>
          </div>
          <p className="mt-2 text-sm leading-6 text-slate-600">
            生成客户交付前的问诊、预期确认、风险解释、推荐依据和免责边界质检。
            {plan ? " 已带入结构化志愿表。" : " 当前未检测到结构化志愿表。"}
          </p>
        </div>
        <Button
          type="button"
          onClick={runReview}
          disabled={!canRun || isLoading}
          className="bg-cyan-700 text-white hover:bg-cyan-800"
        >
          {isLoading ? "预检中..." : "生成交付预检"}
        </Button>
      </div>

      <div className="mt-6 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-start gap-3">
            <BarChart3 className="mt-0.5 size-5 text-cyan-700" aria-hidden="true" />
            <div>
              <h3 className="text-base font-semibold text-slate-900">机构全局案源驾驶舱</h3>
              <p className="mt-1 text-sm leading-6 text-slate-600">
                汇总已生成的交付包，识别重复失败门槛、阻塞个案和顾问主管下一步动作。
              </p>
            </div>
          </div>
          <Button
            type="button"
            variant="outline"
            onClick={loadCommandCenter}
            disabled={isPortfolioLoading}
            className="border-cyan-700 text-cyan-800 hover:bg-cyan-50"
          >
            {isPortfolioLoading ? "扫描中..." : "扫描全局案源"}
          </Button>
        </div>

        {portfolioError && (
          <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
            {portfolioError}
          </div>
        )}

        {commandCenter && (
          <div className="mt-5 space-y-4">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
              {[
                ["案源数", commandCenter.audit.north_star.case_count, ""],
                ["可交付率", percent(commandCenter.audit.north_star.ready_to_deliver_rate), ""],
                ["阻塞率", percent(commandCenter.audit.north_star.blocked_rate), ""],
                ["状态", statusLabel[commandCenter.audit.status] || commandCenter.audit.status, ""],
              ].map(([label, value]) => (
                <div key={String(label)} className="rounded-lg border border-slate-200 bg-white p-4">
                  <div className="text-xs text-slate-500">{label}</div>
                  <div className="mt-2 text-lg font-semibold text-slate-900">{value}</div>
                </div>
              ))}
            </div>

            {commandCenter.audit.institution_health_scorecard.dimensions.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">机构经营体检卡</div>
                  <Badge
                    className={statusTone(
                      commandCenter.audit.institution_health_scorecard.overall_status === "critical_attention"
                        ? "blocked"
                        : "pending_signoff"
                    )}
                    variant="outline"
                  >
                    {statusLabel[commandCenter.audit.institution_health_scorecard.overall_status] ||
                      commandCenter.audit.institution_health_scorecard.overall_status}
                  </Badge>
                </div>
                <p className="mb-4 text-sm leading-6 text-slate-600">
                  {commandCenter.audit.institution_health_scorecard.next_management_decision}
                </p>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
                  {commandCenter.audit.institution_health_scorecard.dimensions.map((item) => (
                    <div key={item.dimension} className="rounded-md bg-slate-50 p-3 text-sm">
                      <div className="mb-2 flex items-center justify-between gap-2">
                        <span className="font-medium text-slate-800">{item.label}</span>
                        <Badge className={statusTone(item.status)} variant="outline">
                          {item.score}
                        </Badge>
                      </div>
                      <p className="mb-2 text-xs leading-5 text-slate-500">{item.signal}</p>
                      <p className="leading-6 text-slate-700">{item.management_question}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-lg border border-slate-200 bg-white p-4">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div className="text-sm font-semibold text-slate-800">主管决策门</div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    className={statusTone(
                      commandCenter.audit.executive_decision.priority === "P0" ? "blocked" : "pending_signoff"
                    )}
                    variant="outline"
                  >
                    {commandCenter.audit.executive_decision.priority}
                  </Badge>
                  <Badge className="border-slate-300 bg-slate-50 text-slate-700" variant="outline">
                    {statusLabel[commandCenter.audit.executive_decision.decision] ||
                      commandCenter.audit.executive_decision.decision}
                  </Badge>
                  <Badge className="border-cyan-200 bg-cyan-50 text-cyan-800" variant="outline">
                    {statusLabel[commandCenter.audit.executive_decision.review_cadence] ||
                      commandCenter.audit.executive_decision.review_cadence}
                  </Badge>
                </div>
              </div>
              <p className="mb-4 text-sm leading-6 text-slate-600">
                {commandCenter.audit.executive_decision.summary}
              </p>
              <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
                {[
                  ["可对外表达", commandCenter.audit.executive_decision.allowed_claims],
                  ["暂时不能说", commandCenter.audit.executive_decision.blocked_claims],
                  ["还缺证据", commandCenter.audit.executive_decision.required_evidence],
                ].map(([title, items]) => (
                  <div key={String(title)} className="rounded-md bg-slate-50 p-4 text-sm">
                    <div className="mb-2 font-semibold text-slate-800">{title}</div>
                    <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-600">
                      {(items as string[]).slice(0, 3).map((item) => (
                        <li key={item}>{item}</li>
                      ))}
                    </ul>
                  </div>
                ))}
              </div>
            </div>

            {commandCenter.audit.client_pain_radar.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">用户痛点雷达</div>
                  <Badge className="border-slate-300 bg-slate-50 text-slate-700" variant="outline">
                    {commandCenter.audit.client_pain_radar.length} 个高频痛点
                  </Badge>
                </div>
                <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
                  {commandCenter.audit.client_pain_radar.slice(0, 3).map((card) => (
                    <div key={`${card.gate}-${card.user_pain}`} className="rounded-md bg-slate-50 p-4 text-sm">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge
                          className={statusTone(card.priority === "P0" ? "blocked" : "pending_signoff")}
                          variant="outline"
                        >
                          {card.priority}
                        </Badge>
                        <span className="font-medium text-slate-800">{card.gate}</span>
                        <span className="text-xs text-slate-500">{Math.round(card.affected_rate * 100)}%</span>
                      </div>
                      <p className="mb-2 leading-6 text-slate-700">{card.user_pain}</p>
                      <div className="mb-3 rounded-md border border-slate-200 bg-white p-3 leading-6 text-slate-600">
                        {card.advisor_opening}
                      </div>
                      <div className="mb-3">
                        <div className="mb-1 text-xs font-semibold text-slate-500">证据物</div>
                        <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-600">
                          {card.proof_to_show.slice(0, 3).map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="text-xs leading-5 text-slate-500">{card.success_signal}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {commandCenter.audit.proof_gap_ledger.items.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">证据缺口台账</div>
                  <Badge className={statusTone("pending_signoff")} variant="outline">
                    {commandCenter.audit.proof_gap_ledger.item_count} 个待补证据
                  </Badge>
                </div>
                <p className="mb-4 text-sm leading-6 text-slate-600">
                  {commandCenter.audit.proof_gap_ledger.ledger_standard}
                </p>
                <div className="space-y-3">
                  {commandCenter.audit.proof_gap_ledger.items.slice(0, 4).map((item) => (
                    <div
                      key={item.gap_id}
                      className="grid gap-3 rounded-md bg-slate-50 p-4 text-sm lg:grid-cols-[90px_130px_1.2fr_1fr]"
                    >
                      <div className="flex flex-wrap items-start gap-2">
                        <Badge
                          className={statusTone(item.priority === "P0" ? "blocked" : "pending_signoff")}
                          variant="outline"
                        >
                          {item.priority}
                        </Badge>
                        <span className="font-medium text-slate-800">{item.gate}</span>
                      </div>
                      <div className="leading-6 text-slate-600">
                        <div className="font-medium text-slate-800">{item.owner}</div>
                        <div>{statusLabel[item.review_cadence] || item.review_cadence}</div>
                      </div>
                      <div>
                        <div className="mb-1 text-xs font-semibold text-slate-500">待补证据</div>
                        <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-700">
                          {item.missing_proof.slice(0, 3).map((proof) => (
                            <li key={proof}>{proof}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="leading-6 text-slate-600">
                        <div className="mb-1 text-xs font-semibold text-slate-500">验收标准</div>
                        <p>{item.evidence_standard}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {commandCenter.audit.communication_guardrails.cards.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">顾问沟通护栏</div>
                  <Badge
                    className={statusTone(
                      commandCenter.audit.communication_guardrails.status === "restricted"
                        ? "blocked"
                        : "pending_signoff"
                    )}
                    variant="outline"
                  >
                    {commandCenter.audit.communication_guardrails.status === "restricted" ? "受限沟通" : "可用话术"}
                  </Badge>
                </div>
                <p className="mb-4 text-sm leading-6 text-slate-600">
                  {commandCenter.audit.communication_guardrails.guardrail_standard}
                </p>
                <div className="grid grid-cols-1 gap-3 xl:grid-cols-2">
                  {commandCenter.audit.communication_guardrails.cards.slice(0, 4).map((card) => (
                    <div key={`${card.gate}-${card.approved_opening}`} className="rounded-md bg-slate-50 p-4 text-sm">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge
                          className={statusTone(card.priority === "P0" ? "blocked" : "pending_signoff")}
                          variant="outline"
                        >
                          {card.priority}
                        </Badge>
                        <span className="font-medium text-slate-800">{card.gate}</span>
                      </div>
                      <div className="mb-3 rounded-md border border-slate-200 bg-white p-3 leading-6 text-slate-700">
                        {card.approved_opening}
                      </div>
                      <div className="grid gap-3 md:grid-cols-2">
                        <div>
                          <div className="mb-1 text-xs font-semibold text-slate-500">必须披露</div>
                          <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-600">
                            {card.must_disclose.slice(0, 3).map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </div>
                        <div>
                          <div className="mb-1 text-xs font-semibold text-slate-500">禁用表达</div>
                          <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-600">
                            {card.forbidden_language.slice(0, 3).map((item) => (
                              <li key={item}>{item}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                      <div className="mt-3 text-xs leading-5 text-slate-500">{card.safe_close}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 text-sm font-semibold text-slate-800">顾问主管动作</div>
                <div className="space-y-3">
                  {commandCenter.audit.advisor_lead_brief.map((item) => (
                    <div key={`${item.priority}-${item.focus}`} className="text-sm leading-6">
                      <Badge className={statusTone(item.priority === "P0" ? "blocked" : "pending_signoff")} variant="outline">
                        {item.priority}
                      </Badge>
                      <span className="ml-2 font-medium text-slate-800">{item.focus}</span>
                      <p className="mt-1 text-slate-600">{item.why}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 text-sm font-semibold text-slate-800">用户痛点聚类</div>
                <div className="space-y-3">
                  {commandCenter.audit.pain_points.slice(0, 4).map((point) => (
                    <div key={point.gate} className="grid gap-2 text-sm md:grid-cols-[70px_1fr]">
                      <Badge className={statusTone(point.priority === "P0" ? "blocked" : "pending_signoff")} variant="outline">
                        {point.priority}
                      </Badge>
                      <div>
                        <div className="font-medium text-slate-800">
                          {point.gate} · {Math.round(point.affected_rate * 100)}%
                        </div>
                        <p className="text-slate-600">{point.pain_point}</p>
                        <p className="text-slate-500">{point.operator_response}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {commandCenter.audit.advisor_playbook.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 text-sm font-semibold text-slate-800">顾问 SOP / 问诊脚本</div>
                <div className="grid grid-cols-1 gap-3 xl:grid-cols-3">
                  {commandCenter.audit.advisor_playbook.slice(0, 3).map((card) => (
                    <div key={`${card.gate}-${card.handoff_stage}`} className="rounded-md bg-slate-50 p-4 text-sm">
                      <div className="mb-2 flex flex-wrap items-center gap-2">
                        <Badge className={statusTone(card.priority === "P0" ? "blocked" : "pending_signoff")} variant="outline">
                          {card.priority}
                        </Badge>
                        <span className="font-medium text-slate-800">{card.gate}</span>
                        <span className="text-xs text-slate-500">{card.handoff_stage}</span>
                      </div>
                      <p className="mb-3 leading-6 text-slate-600">{card.trigger}</p>
                      <div className="mb-3">
                        <div className="mb-1 text-xs font-semibold text-slate-500">必问问题</div>
                        <ol className="list-decimal space-y-1 pl-4 leading-6 text-slate-700">
                          {card.intake_questions.slice(0, 3).map((question) => (
                            <li key={question}>{question}</li>
                          ))}
                        </ol>
                      </div>
                      <div className="mb-3">
                        <div className="mb-1 text-xs font-semibold text-slate-500">验收证据</div>
                        <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-700">
                          {card.acceptance_evidence.slice(0, 2).map((item) => (
                            <li key={item}>{item}</li>
                          ))}
                        </ul>
                      </div>
                      <div className="rounded-md border border-slate-200 bg-white p-3 text-slate-600">
                        {card.client_language}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {commandCenter.audit.advisor_training_plan.modules.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">团队训练与质检节奏</div>
                  <Badge className={statusTone("pending_signoff")} variant="outline">
                    {commandCenter.audit.advisor_training_plan.status}
                  </Badge>
                </div>
                <div className="grid grid-cols-1 gap-4 lg:grid-cols-[1.4fr_1fr]">
                  <div className="space-y-3">
                    {commandCenter.audit.advisor_training_plan.modules.slice(0, 3).map((module) => (
                      <div key={module.module_id} className="rounded-md bg-slate-50 p-4 text-sm">
                        <div className="mb-2 flex flex-wrap items-center gap-2">
                          <Badge className={statusTone(module.priority === "P0" ? "blocked" : "pending_signoff")} variant="outline">
                            {module.priority}
                          </Badge>
                          <span className="font-medium text-slate-800">{module.title}</span>
                        </div>
                        <p className="mb-2 leading-6 text-slate-600">{module.practice_drill}</p>
                        <div className="space-y-1">
                          {module.qa_rubric.slice(0, 2).map((item) => (
                            <div key={item.criterion} className="text-xs leading-5 text-slate-600">
                              <span className="font-semibold text-slate-700">{item.criterion}：</span>
                              {item.standard}
                            </div>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                  <div className="rounded-md border border-slate-200 p-4 text-sm">
                    <div className="mb-2 font-semibold text-slate-800">运营节奏</div>
                    <div className="space-y-3">
                      {commandCenter.audit.advisor_training_plan.operating_cadence.map((item) => (
                        <div key={`${item.cadence}-${item.owner}`} className="leading-6">
                          <Badge className="border-slate-300 bg-slate-50 text-slate-700" variant="outline">
                            {item.cadence}
                          </Badge>
                          <span className="ml-2 font-medium text-slate-700">{item.owner}</span>
                          <p className="mt-1 text-slate-600">{item.action}</p>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 rounded-md bg-slate-50 p-3 leading-6 text-slate-600">
                      {commandCenter.audit.advisor_training_plan.pass_condition}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {commandCenter.audit.action_register.items.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">机构行动台账</div>
                  <Badge className={statusTone(commandCenter.audit.action_register.status === "active" ? "pending_signoff" : "not_provided")} variant="outline">
                    {commandCenter.audit.action_register.status}
                  </Badge>
                </div>
                <p className="mb-4 text-sm leading-6 text-slate-600">
                  {commandCenter.audit.action_register.register_standard}
                </p>
                <div className="space-y-2">
                  {commandCenter.audit.action_register.items.slice(0, 6).map((item) => (
                    <div
                      key={item.action_id}
                      className="grid gap-2 rounded-md bg-slate-50 p-3 text-sm lg:grid-cols-[70px_110px_90px_1fr_1fr]"
                    >
                      <Badge className={statusTone(item.priority === "P0" ? "blocked" : "pending_signoff")} variant="outline">
                        {item.priority}
                      </Badge>
                      <span className="font-medium text-slate-800">{item.owner}</span>
                      <span className="text-slate-600">{item.cadence}</span>
                      <div>
                        <div className="text-xs text-slate-500">{item.source}</div>
                        <div className="leading-6 text-slate-800">{item.action}</div>
                      </div>
                      <div className="leading-6 text-slate-600">{item.success_metric}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {commandCenter.audit.case_rescue_queue.items.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                  <div className="text-sm font-semibold text-slate-800">个案救援队列</div>
                  <Badge className={statusTone("blocked")} variant="outline">
                    {commandCenter.audit.case_rescue_queue.item_count} 个待救援
                  </Badge>
                </div>
                <p className="mb-4 text-sm leading-6 text-slate-600">
                  {commandCenter.audit.case_rescue_queue.queue_standard}
                </p>
                <div className="space-y-3">
                  {commandCenter.audit.case_rescue_queue.items.slice(0, 5).map((item) => (
                    <div key={item.rescue_id} className="rounded-md bg-slate-50 p-4 text-sm">
                      <div className="mb-3 flex flex-wrap items-center gap-2">
                        <Badge
                          className={statusTone(item.priority === "P0" ? "blocked" : "pending_signoff")}
                          variant="outline"
                        >
                          {item.priority}
                        </Badge>
                        <span className="font-semibold text-slate-800">{item.case_id}</span>
                        <span className="text-slate-500">{statusLabel[item.status] || item.status}</span>
                        <span className="text-slate-500">{percent(item.portfolio_score)}</span>
                      </div>
                      <div className="grid gap-3 lg:grid-cols-[140px_1.3fr_1fr]">
                        <div className="leading-6 text-slate-600">
                          <div className="font-medium text-slate-800">{item.owner}</div>
                          <div>{statusLabel[item.cadence] || item.cadence}</div>
                          <div>{item.failed_gates.join(" / ") || "none"}</div>
                        </div>
                        <div>
                          <div className="mb-1 text-xs font-semibold text-slate-500">救援步骤</div>
                          <ul className="list-disc space-y-1 pl-4 leading-6 text-slate-700">
                            {item.rescue_steps.slice(0, 4).map((step) => (
                              <li key={step}>{step}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="leading-6 text-slate-600">
                          <div className="mb-1 text-xs font-semibold text-slate-500">客户同步</div>
                          <p>{item.client_update_script}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {commandCenter.audit.escalation_queue.length > 0 && (
              <div className="rounded-lg border border-slate-200 bg-white p-4">
                <div className="mb-3 text-sm font-semibold text-slate-800">升级队列</div>
                <div className="space-y-2">
                  {commandCenter.audit.escalation_queue.slice(0, 5).map((item) => (
                    <div
                      key={item.case_id}
                      className="grid gap-2 rounded-md bg-slate-50 p-3 text-sm md:grid-cols-[1fr_120px_90px]"
                    >
                      <span className="font-medium text-slate-800">{item.case_id}</span>
                      <Badge className={statusTone(item.status)} variant="outline">
                        {statusLabel[item.status] || item.status}
                      </Badge>
                      <span className="text-slate-600">{percent(item.portfolio_score)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {!canRun && (
        <div className="mt-4 rounded-lg border border-amber-300 bg-amber-50 p-4 text-sm text-amber-800">
          需要先生成报告，并保留分数、选科等画像信息，才能进行内部交付预检。
        </div>
      )}

      {error && (
        <div className="mt-4 rounded-lg border border-red-300 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {preview && (
        <div className="mt-6 space-y-5">
          <div className="grid grid-cols-1 gap-3 md:grid-cols-4">
            {[
              ["总状态", preview.manifest.status, undefined],
              ["问诊", preview.manifest.intake_status, preview.manifest.intake_readiness_score],
              ["志愿表", preview.manifest.plan_quality_status, preview.manifest.plan_quality_score],
              ["报告", preview.manifest.report_quality_status, preview.manifest.report_quality_score],
            ].map(([label, status, score]) => (
              <div key={String(label)} className="rounded-lg border border-slate-200 p-4">
                <div className="text-xs text-slate-500">{label}</div>
                <div className="mt-2 flex items-center justify-between gap-2">
                  <Badge className={statusTone(String(status))} variant="outline">
                    {statusLabel[String(status)] || String(status || "unknown")}
                  </Badge>
                  {typeof score === "number" && (
                    <span className="text-sm font-semibold text-slate-700">{percent(score)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
              <ShieldAlert className="size-4 text-slate-600" aria-hidden="true" />
              交付门槛
            </div>
            <div className="space-y-3">
              {(preview.manifest.delivery_gates || []).map((gate) => (
                <div key={gate.gate} className="grid gap-2 text-sm md:grid-cols-[160px_110px_1fr]">
                  <span className="font-medium text-slate-700">{gate.gate}</span>
                  <Badge className={statusTone(gate.status)} variant="outline">
                    {statusLabel[gate.status] || gate.status}
                  </Badge>
                  <span className="text-slate-600">{gate.requirement}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 text-sm font-semibold text-slate-800">case-scoped reviewed evidence</div>
            {reviewedEvidenceError && (
              <div className="mb-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
                {reviewedEvidenceError}
              </div>
            )}
            <ReviewedEvidenceCaseBrowserPanel
              caseId={preview.manifest.case_id || preview.case_id}
              records={reviewedEvidenceRecords}
              plan={reviewedEvidencePlan}
            />
            {operatorCaptureWorklist && operatorCaptureWorklist.totalItems > 0 ? (
              <div className="mt-3 rounded-md border border-amber-200 bg-amber-50 p-3 text-sm text-amber-900">
                <div className="font-medium">operator capture worklist</div>
                <p className="mt-1">
                  {operatorCaptureWorklist.blockingItemCount} blocking / {operatorCaptureWorklist.totalItems} item(s)
                  must use {OPERATOR_CAPTURE_WORKFLOW}.
                </p>
                <ul className="mt-2 space-y-1">
                  {operatorCaptureWorklist.items.slice(0, 3).map((item) => (
                    <li key={item.taskId} className="break-words">
                      {item.taskId} - {item.priority} - {item.captureStatus} - {item.reason}
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>

          <div className="rounded-lg border border-slate-200 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-slate-800">
              {preview.manifest.status === "ready_to_deliver" ? (
                <CheckCircle2 className="size-4 text-emerald-600" aria-hidden="true" />
              ) : (
                <AlertTriangle className="size-4 text-amber-600" aria-hidden="true" />
              )}
              下一步动作
            </div>
            <ol className="list-decimal space-y-2 pl-5 text-sm leading-6 text-slate-700">
              {(preview.manifest.next_actions || []).map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ol>
          </div>

          {orderedArtifacts.length > 0 && (
            <Tabs defaultValue={orderedArtifacts[0][0]} className="rounded-lg border border-slate-200 p-4">
              <div className="mb-3 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                  <FileText className="size-4 text-slate-600" aria-hidden="true" />
                  交付材料预览
                </div>
                <div className="flex flex-col gap-2 md:flex-row">
                  <Button
                    type="button"
                    onClick={downloadClientBundle}
                    disabled={clientFacingArtifacts.length === 0 || !clientDeliveryAllowed}
                    className="w-full bg-cyan-700 text-white hover:bg-cyan-800 md:w-auto"
                  >
                    <FileDown className="size-4" aria-hidden="true" />
                    下载客户确认包
                  </Button>
                  <Button
                    type="button"
                    onClick={downloadCombinedBundle}
                    className="w-full bg-slate-800 text-white hover:bg-slate-900 md:w-auto"
                  >
                    <FileDown className="size-4" aria-hidden="true" />
                    下载完整预检包
                  </Button>
                </div>
              </div>
              {!clientDeliveryAllowed && (
                <div className="mb-3 rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-800">
                  {clientDeliveryBlockedReason}
                </div>
              )}
              <TabsList className="flex h-auto w-full flex-wrap justify-start gap-2 bg-slate-100">
                {orderedArtifacts.map(([id]) => (
                  <TabsTrigger key={id} value={id} className="min-h-8 flex-none">
                    {artifactTitle(id)}
                  </TabsTrigger>
                ))}
              </TabsList>
              {orderedArtifacts.map(([id, content]) => (
                <TabsContent key={id} value={id} className="mt-4">
                  <div className="max-h-[520px] overflow-auto rounded-md bg-slate-950 p-5">
                    <ReactMarkdown
                      components={{
                        h1: ({ children }) => (
                          <h1 className="mb-4 text-2xl font-semibold text-cyan-100">{children}</h1>
                        ),
                        h2: ({ children }) => (
                          <h2 className="mb-3 mt-6 text-lg font-semibold text-cyan-200">{children}</h2>
                        ),
                        p: ({ children }) => (
                          <p className="mb-3 text-sm leading-6 text-slate-200">{children}</p>
                        ),
                        li: ({ children }) => (
                          <li className="mb-1 text-sm leading-6 text-slate-200">{children}</li>
                        ),
                        table: ({ children }) => (
                          <table className="mb-4 w-full border-collapse text-sm text-slate-200">
                            {children}
                          </table>
                        ),
                        th: ({ children }) => (
                          <th className="border border-slate-700 px-2 py-1 text-left">{children}</th>
                        ),
                        td: ({ children }) => (
                          <td className="border border-slate-700 px-2 py-1 align-top">{children}</td>
                        ),
                      }}
                    >
                      {content}
                    </ReactMarkdown>
                  </div>
                </TabsContent>
              ))}
            </Tabs>
          )}
        </div>
      )}
    </section>
  );
}
