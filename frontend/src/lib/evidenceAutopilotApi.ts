import { buildApiUrl } from "./api";
import type { DeepEvidenceCollectionContext, DeepEvidenceCollectionPlan } from "./deepEvidenceCollectionPlan";
import type { EvidenceAutopilotSearchTask } from "./evidenceAutopilot";
import type { EvidenceAutopilotProviderResult } from "./evidenceAutopilotProvider";
import { buildEvidenceAutopilotSnapshotProviderResults } from "./evidenceAutopilotSnapshotProvider";

export type EvidenceAutopilotBackendStatus =
  | "demo_snapshot"
  | "backend_connected"
  | "backend_failed_snapshot_fallback"
  | "real_case_fixture";

type BackendEvidenceCardStatus = "requires_capture" | "operator_review" | "captured_candidate";
export type ReviewedEvidenceAttachmentKind = "screenshot" | "page_capture" | "pdf" | "image" | "other";
export type ReviewedEvidenceRedactionStatus = "pending" | "redacted" | "not_required";
export type ReviewedEvidenceReviewerRole = "operator" | "counselor" | "qa_reviewer" | "lead_counselor";

export interface ReviewedEvidenceAttachment {
  attachmentId: string;
  kind: ReviewedEvidenceAttachmentKind;
  storageRef: string;
  capturedAt: string;
  redactionStatus: ReviewedEvidenceRedactionStatus;
  redactionChecklist?: ReviewedEvidenceRedactionChecklist;
}

export interface ReviewedEvidenceRedactionChecklist {
  studentPersonalInfoRemoved: boolean;
  privateContactInfoRemoved: boolean;
  accountIdentifiersRemoved: boolean;
  thirdPartyPersonalInfoRemoved: boolean;
  reviewerConfirmed: boolean;
  notes?: string;
}

export type ReviewedEvidenceAttachmentAuditStatus = "valid" | "invalid" | "not_applicable";

export interface ReviewedEvidenceAttachmentAuditFinding {
  attachmentId: string;
  storageRef: string;
  valid: boolean;
  detail: string;
}

export interface ReviewedEvidenceAttachmentAudit {
  status: ReviewedEvidenceAttachmentAuditStatus;
  validAttachmentCount: number;
  invalidAttachmentCount: number;
  checkedAt?: string;
  findings: ReviewedEvidenceAttachmentAuditFinding[];
}

export interface ReviewedEvidenceReviewerIdentity {
  reviewerId: string;
  displayName: string;
  role: ReviewedEvidenceReviewerRole;
}

export interface BackendEvidenceCard {
  taskId: string;
  claim: string;
  status: BackendEvidenceCardStatus;
  sourceTitle: string;
  sourceUrl: string;
  sourceType: EvidenceAutopilotProviderResult["sourceType"];
  excerpt: string;
  capturedAt: string;
  confidence: EvidenceAutopilotProviderResult["confidence"];
  reviewAction: string;
  attachments?: ReviewedEvidenceAttachment[];
  redactionStatus?: ReviewedEvidenceRedactionStatus;
  reviewerIdentity?: ReviewedEvidenceReviewerIdentity;
}

const VALID_CARD_STATUSES = new Set(["requires_capture", "operator_review", "captured_candidate"]);
const VALID_SOURCE_TYPES = new Set(["official", "school", "paper", "job", "wechat", "discussion", "other"]);
const VALID_CONFIDENCE_LEVELS = new Set(["high", "medium", "low"]);
const VALID_REDACTION_STATUSES = new Set(["pending", "redacted", "not_required"]);
const VALID_ATTACHMENT_KINDS = new Set(["screenshot", "page_capture", "pdf", "image", "other"]);

export interface EvidenceAutopilotBackendResponse {
  success: boolean;
  targetLabel: string;
  tasks: unknown[];
  searchQueries: string[];
  evidenceCards: BackendEvidenceCard[];
  evidenceCoverage: EvidenceAutopilotBackendCoverage;
  claimBoundary: string;
}

export interface EvidenceAutopilotBackendCoverage {
  totalTasks: number;
  capturedTaskIds: string[];
  missingP0TaskIds: string[];
  operatorTaskIds: string[];
  readyForCounselorReview: boolean;
  reviewBlockers: string[];
}

export interface EvidenceAutopilotApiState {
  status: EvidenceAutopilotBackendStatus;
  providerResults: EvidenceAutopilotProviderResult[];
  claimBoundary: string;
  evidenceCoverage?: EvidenceAutopilotBackendCoverage;
  backendResponse?: EvidenceAutopilotBackendResponse;
  error?: string;
}

export interface ReviewedEvidenceRecord {
  reviewId: string;
  targetLabel: string;
  reviewedEvidenceCard: BackendEvidenceCard;
  reviewer: string;
  caseId: string;
  recordedAt: string;
  ledgerPath: string;
  attachmentAudit?: ReviewedEvidenceAttachmentAudit;
}

export interface ReviewedEvidenceListingResponse {
  success: boolean;
  caseId: string;
  recordCount: number;
  records: ReviewedEvidenceRecord[];
}

export interface ReviewedEvidenceAttachmentUploadPayload {
  caseId: string;
  taskId: string;
  reviewerId: string;
  kind: ReviewedEvidenceAttachment["kind"];
  contentType: string;
  contentBase64: string;
  capturedAt: string;
  redactionStatus: ReviewedEvidenceRedactionStatus;
  redactionChecklist?: ReviewedEvidenceRedactionChecklist;
  originalFileName?: string;
}

export interface ReviewedEvidenceAttachmentUploadResponse {
  success: boolean;
  attachment: ReviewedEvidenceAttachment;
  byteSize: number;
  sha256: string;
  metadataPath: string;
}

export interface OperatorReviewedEvidenceCardInput {
  taskId: string;
  claim: string;
  sourceTitle: string;
  sourceType: EvidenceAutopilotProviderResult["sourceType"];
  excerpt: string;
  capturedAt: string;
  confidence: EvidenceAutopilotProviderResult["confidence"];
  reviewAction: string;
  attachments: ReviewedEvidenceAttachment[];
  redactionStatus: ReviewedEvidenceRedactionStatus;
  reviewerIdentity?: ReviewedEvidenceReviewerIdentity;
}

export interface ReviewedEvidenceSubmissionPayload {
  targetLabel: string;
  card: BackendEvidenceCard;
  reviewer: string;
  caseId?: string;
}

export interface ReviewedEvidenceSubmissionResponse {
  success: boolean;
  reviewId: string;
  reviewedEvidenceCard: BackendEvidenceCard;
  ledgerPath: string;
  recordedAt: string;
}

export interface OperatorReviewedEvidenceCaptureInput {
  targetLabel: string;
  caseId?: string;
  reviewer: string;
  attachmentPayload: ReviewedEvidenceAttachmentUploadPayload;
  card: Omit<OperatorReviewedEvidenceCardInput, "attachments">;
}

export interface OperatorReviewedEvidenceCaptureResult {
  upload: ReviewedEvidenceAttachmentUploadResponse;
  submission: ReviewedEvidenceSubmissionResponse;
  reviewedEvidenceCard: BackendEvidenceCard;
}

type FetchLike = (url: string, init: RequestInit) => Promise<{
  ok: boolean;
  status?: number;
  json(): Promise<unknown>;
}>;

export interface EvidenceAutopilotResearchPayloadOptions {
  caseId?: string;
  enableReviewedEvidenceLedger?: boolean;
}

export function buildEvidenceAutopilotResearchPayload(
  context: DeepEvidenceCollectionContext,
  options: EvidenceAutopilotResearchPayloadOptions = {},
) {
  const payload: {
    province: string;
    schoolName: string;
    majorName: string;
    targetYear: number;
    caseId?: string;
    enableReviewedEvidenceLedger?: boolean;
  } = {
    province: context.province,
    schoolName: context.schoolName,
    majorName: context.majorName,
    targetYear: context.targetYear,
  };
  if (options.caseId) {
    payload.caseId = options.caseId;
  }
  if (options.enableReviewedEvidenceLedger) {
    payload.enableReviewedEvidenceLedger = true;
  }
  return payload;
}

export function mapBackendEvidenceCardsToProviderResults(
  response: EvidenceAutopilotBackendResponse,
): EvidenceAutopilotProviderResult[] {
  return response.evidenceCards
    .filter((card, index) => {
      assertValidBackendEvidenceCard(card, index);
      return card.status === "captured_candidate" && card.sourceUrl.trim() && card.excerpt.trim();
    })
    .map((card, index) => ({
      requestId: `backend-${card.taskId}-${index + 1}`,
      taskId: card.taskId,
      sourceTitle: card.sourceTitle,
      sourceUrl: card.sourceUrl,
      sourceType: card.sourceType,
      excerpt: card.excerpt,
      capturedAt: card.capturedAt || "backend_runtime",
      confidence: card.confidence,
    }));
}

export function buildEvidenceAutopilotSnapshotFallback({
  plan,
  searchTasks,
  targetLabel,
  reason,
}: {
  plan: DeepEvidenceCollectionPlan;
  searchTasks: EvidenceAutopilotSearchTask[];
  targetLabel: string;
  reason: string;
}): EvidenceAutopilotApiState {
  return {
    status: "backend_failed_snapshot_fallback",
    providerResults: buildEvidenceAutopilotSnapshotProviderResults({ plan, searchTasks, targetLabel }),
    claimBoundary: `Using demo snapshot fallback: ${reason}. Live backend evidence still requires source URL, excerpt, capture time, and confidence.`,
    error: reason,
  };
}

export function buildEvidenceAutopilotRealCaseState({
  providerResults,
  claimBoundary,
}: {
  providerResults: EvidenceAutopilotProviderResult[];
  claimBoundary: string;
}): EvidenceAutopilotApiState {
  return {
    status: "real_case_fixture",
    providerResults,
    claimBoundary,
  };
}

export async function fetchEvidenceAutopilotResearch({
  context,
  caseId,
  enableReviewedEvidenceLedger,
  fetchImpl = fetch,
  fallback,
}: {
  context: DeepEvidenceCollectionContext;
  caseId?: string;
  enableReviewedEvidenceLedger?: boolean;
  fetchImpl?: FetchLike;
  fallback?: {
    plan: DeepEvidenceCollectionPlan;
    searchTasks: EvidenceAutopilotSearchTask[];
    targetLabel: string;
  };
}): Promise<EvidenceAutopilotApiState> {
  try {
    const response = await fetchImpl(buildApiUrl("/api/evidence-autopilot/research"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildEvidenceAutopilotResearchPayload(context, {
        caseId,
        enableReviewedEvidenceLedger,
      })),
    });
    if (!response.ok) {
      throw new Error(`backend returned HTTP ${response.status ?? "error"}`);
    }
    const backendResponse = responseFromJson(await response.json());
    const providerResults = mapBackendEvidenceCardsToProviderResults(backendResponse);
    if (providerResults.length === 0 && fallback) {
      return buildEvidenceAutopilotSnapshotFallback({
        ...fallback,
        reason: "backend returned task placeholders without captured evidence",
      });
    }
    return {
      status: "backend_connected",
      providerResults,
      claimBoundary: backendResponse.claimBoundary,
      evidenceCoverage: backendResponse.evidenceCoverage,
      backendResponse,
    };
  } catch (error) {
    const reason = error instanceof Error ? error.message : String(error);
    if (fallback) {
      return buildEvidenceAutopilotSnapshotFallback({ ...fallback, reason });
    }
    return {
      status: "backend_failed_snapshot_fallback",
      providerResults: [],
      claimBoundary: `Using demo snapshot fallback: ${reason}.`,
      error: reason,
    };
  }
}

export async function fetchReviewedEvidenceRecords({
  caseId,
  fetchImpl = fetch,
}: {
  caseId: string;
  fetchImpl?: FetchLike;
}): Promise<ReviewedEvidenceListingResponse> {
  const encodedCaseId = encodeURIComponent(caseId);
  const response = await fetchImpl(
    buildApiUrl(`/api/evidence-autopilot/reviewed-evidence/${encodedCaseId}`),
    {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    },
  );
  if (!response.ok) {
    throw new Error(`backend returned HTTP ${response.status ?? "error"}`);
  }
  return reviewedEvidenceListingFromJson(await response.json());
}

export async function uploadReviewedEvidenceAttachment({
  payload,
  fetchImpl = fetch,
}: {
  payload: ReviewedEvidenceAttachmentUploadPayload;
  fetchImpl?: FetchLike;
}): Promise<ReviewedEvidenceAttachmentUploadResponse> {
  const response = await fetchImpl(
    buildApiUrl("/api/evidence-autopilot/reviewed-evidence/attachments"),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`backend returned HTTP ${response.status ?? "error"}`);
  }
  return reviewedEvidenceAttachmentUploadFromJson(await response.json());
}

export function buildOperatorReviewedEvidenceCard(
  input: OperatorReviewedEvidenceCardInput,
): BackendEvidenceCard {
  if (!input.reviewerIdentity) {
    throw new Error("operator reviewed evidence requires reviewer identity");
  }
  if (!input.attachments.length) {
    throw new Error("operator reviewed evidence requires at least one attachment");
  }
  if (input.redactionStatus === "pending") {
    throw new Error("operator reviewed evidence requires a completed redaction status");
  }
  input.attachments.forEach((attachment, index) => {
    assertValidReviewedEvidenceAttachment(attachment, `operator card attachment ${index + 1}`);
    if (attachment.redactionStatus === "pending") {
      throw new Error("operator reviewed evidence attachment requires a completed redaction status");
    }
    if (attachment.redactionStatus === "redacted") {
      assertValidReviewedEvidenceRedactionChecklist(
        attachment.redactionChecklist,
        `operator card attachment ${index + 1}`,
      );
    }
  });
  return {
    taskId: input.taskId,
    claim: input.claim,
    status: "captured_candidate",
    sourceTitle: input.sourceTitle,
    sourceUrl: "",
    sourceType: input.sourceType,
    excerpt: input.excerpt,
    capturedAt: input.capturedAt,
    confidence: input.confidence,
    reviewAction: input.reviewAction,
    attachments: input.attachments,
    redactionStatus: input.redactionStatus,
    reviewerIdentity: input.reviewerIdentity,
  };
}

export async function submitReviewedEvidenceCard({
  payload,
  fetchImpl = fetch,
}: {
  payload: ReviewedEvidenceSubmissionPayload;
  fetchImpl?: FetchLike;
}): Promise<ReviewedEvidenceSubmissionResponse> {
  const response = await fetchImpl(
    buildApiUrl("/api/evidence-autopilot/reviewed-evidence"),
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
  );
  if (!response.ok) {
    throw new Error(`backend returned HTTP ${response.status ?? "error"}`);
  }
  return reviewedEvidenceSubmissionFromJson(await response.json());
}

export async function captureAndSubmitOperatorReviewedEvidence({
  targetLabel,
  caseId,
  reviewer,
  attachmentPayload,
  card,
  fetchImpl = fetch,
}: OperatorReviewedEvidenceCaptureInput & {
  fetchImpl?: FetchLike;
}): Promise<OperatorReviewedEvidenceCaptureResult> {
  const upload = await uploadReviewedEvidenceAttachment({
    payload: attachmentPayload,
    fetchImpl,
  });
  const reviewedEvidenceCard = buildOperatorReviewedEvidenceCard({
    ...card,
    attachments: [upload.attachment],
  });
  const submission = await submitReviewedEvidenceCard({
    payload: {
      targetLabel,
      caseId,
      reviewer,
      card: reviewedEvidenceCard,
    },
    fetchImpl,
  });
  return {
    upload,
    submission,
    reviewedEvidenceCard: submission.reviewedEvidenceCard,
  };
}

function responseFromJson(value: unknown): EvidenceAutopilotBackendResponse {
  if (!value || typeof value !== "object") {
    throw new Error("backend response was not an object");
  }
  const response = value as EvidenceAutopilotBackendResponse;
  if (!Array.isArray(response.evidenceCards)) {
    throw new Error("backend response evidenceCards was not an array");
  }
  assertValidBackendCoverage(response.evidenceCoverage);
  return response;
}

function reviewedEvidenceListingFromJson(value: unknown): ReviewedEvidenceListingResponse {
  if (!value || typeof value !== "object") {
    throw new Error("reviewed evidence listing response was not an object");
  }
  const response = value as ReviewedEvidenceListingResponse;
  if (!Array.isArray(response.records)) {
    throw new Error("reviewed evidence listing records was not an array");
  }
  response.records.forEach((record, index) => {
    if (!record.reviewId || typeof record.reviewId !== "string") {
      throw new Error(`invalid reviewed evidence record ${index + 1}: reviewId`);
    }
    if (!record.reviewedEvidenceCard || typeof record.reviewedEvidenceCard !== "object") {
      throw new Error(`invalid reviewed evidence record ${index + 1}: reviewedEvidenceCard`);
    }
    assertValidBackendEvidenceCard(record.reviewedEvidenceCard, index);
    if (record.attachmentAudit) {
      assertValidReviewedEvidenceAttachmentAudit(record.attachmentAudit, index);
    }
  });
  return response;
}

function reviewedEvidenceAttachmentUploadFromJson(
  value: unknown,
): ReviewedEvidenceAttachmentUploadResponse {
  if (!value || typeof value !== "object") {
    throw new Error("invalid reviewed evidence attachment upload response: not an object");
  }
  const response = value as ReviewedEvidenceAttachmentUploadResponse;
  if (response.success !== true) {
    throw new Error("invalid reviewed evidence attachment upload response: success");
  }
  if (!response.attachment || typeof response.attachment !== "object") {
    throw new Error("invalid reviewed evidence attachment upload response: attachment");
  }
  assertValidReviewedEvidenceAttachment(response.attachment, "upload response");
  if (response.attachment.redactionStatus === "redacted") {
    assertValidReviewedEvidenceRedactionChecklist(response.attachment.redactionChecklist, "upload response");
  }
  if (typeof response.byteSize !== "number" || response.byteSize <= 0) {
    throw new Error("invalid reviewed evidence attachment upload response: byteSize");
  }
  if (typeof response.sha256 !== "string" || !/^[a-f0-9]{64}$/i.test(response.sha256)) {
    throw new Error("invalid reviewed evidence attachment upload response: sha256");
  }
  if (typeof response.metadataPath !== "string" || !response.metadataPath.trim()) {
    throw new Error("invalid reviewed evidence attachment upload response: metadataPath");
  }
  return response;
}

function reviewedEvidenceSubmissionFromJson(value: unknown): ReviewedEvidenceSubmissionResponse {
  if (!value || typeof value !== "object") {
    throw new Error("invalid reviewed evidence submission response: not an object");
  }
  const response = value as ReviewedEvidenceSubmissionResponse;
  if (response.success !== true) {
    throw new Error("invalid reviewed evidence submission response: success");
  }
  if (!response.reviewId || typeof response.reviewId !== "string") {
    throw new Error("invalid reviewed evidence submission response: reviewId");
  }
  if (!response.reviewedEvidenceCard || typeof response.reviewedEvidenceCard !== "object") {
    throw new Error("invalid reviewed evidence submission response: reviewedEvidenceCard");
  }
  assertValidBackendEvidenceCard(response.reviewedEvidenceCard, 0);
  if (!response.ledgerPath || typeof response.ledgerPath !== "string") {
    throw new Error("invalid reviewed evidence submission response: ledgerPath");
  }
  if (!response.recordedAt || typeof response.recordedAt !== "string") {
    throw new Error("invalid reviewed evidence submission response: recordedAt");
  }
  return response;
}

function assertValidBackendEvidenceCard(card: BackendEvidenceCard, index: number): void {
  if (!VALID_CARD_STATUSES.has(card.status)) {
    throw new Error(`invalid backend evidence card ${index + 1}: status ${card.status}`);
  }
  if (!VALID_SOURCE_TYPES.has(card.sourceType)) {
    throw new Error(`invalid backend evidence card ${index + 1}: sourceType ${card.sourceType}`);
  }
  if (!VALID_CONFIDENCE_LEVELS.has(card.confidence)) {
    throw new Error(`invalid backend evidence card ${index + 1}: confidence ${card.confidence}`);
  }
  if (card.redactionStatus && !VALID_REDACTION_STATUSES.has(card.redactionStatus)) {
    throw new Error(`invalid backend evidence card ${index + 1}: redactionStatus ${card.redactionStatus}`);
  }
  if (card.attachments && !Array.isArray(card.attachments)) {
    throw new Error(`invalid backend evidence card ${index + 1}: attachments`);
  }
  card.attachments?.forEach((attachment, attachmentIndex) => {
    assertValidReviewedEvidenceAttachment(
      attachment,
      `backend evidence card ${index + 1} attachment ${attachmentIndex + 1}`,
    );
  });
  if (
    card.reviewerIdentity
    && (
      typeof card.reviewerIdentity.reviewerId !== "string"
      || typeof card.reviewerIdentity.displayName !== "string"
      || typeof card.reviewerIdentity.role !== "string"
    )
  ) {
    throw new Error(`invalid backend evidence card ${index + 1}: reviewerIdentity`);
  }
}

function assertValidReviewedEvidenceAttachment(
  attachment: ReviewedEvidenceAttachment,
  label: string,
): void {
  if (!attachment.attachmentId || typeof attachment.attachmentId !== "string") {
    throw new Error(`invalid reviewed evidence attachment ${label}: attachmentId`);
  }
  if (!VALID_ATTACHMENT_KINDS.has(attachment.kind)) {
    throw new Error(`invalid reviewed evidence attachment ${label}: kind`);
  }
  if (!attachment.storageRef || typeof attachment.storageRef !== "string") {
    throw new Error(`invalid reviewed evidence attachment ${label}: storageRef`);
  }
  if (!attachment.capturedAt || typeof attachment.capturedAt !== "string") {
    throw new Error(`invalid reviewed evidence attachment ${label}: capturedAt`);
  }
  if (!VALID_REDACTION_STATUSES.has(attachment.redactionStatus)) {
    throw new Error(`invalid reviewed evidence attachment ${label}: redactionStatus`);
  }
}

function assertValidReviewedEvidenceRedactionChecklist(
  checklist: ReviewedEvidenceRedactionChecklist | undefined,
  label: string,
): void {
  if (!checklist || typeof checklist !== "object") {
    throw new Error(`invalid reviewed evidence attachment ${label}: redactionChecklist`);
  }
  for (const field of [
    "studentPersonalInfoRemoved",
    "privateContactInfoRemoved",
    "accountIdentifiersRemoved",
    "thirdPartyPersonalInfoRemoved",
    "reviewerConfirmed",
  ] as const) {
    if (checklist[field] !== true) {
      throw new Error(`invalid reviewed evidence attachment ${label}: redactionChecklist ${field}`);
    }
  }
}

function assertValidReviewedEvidenceAttachmentAudit(
  audit: ReviewedEvidenceAttachmentAudit,
  index: number,
): void {
  if (!["valid", "invalid", "not_applicable"].includes(audit.status)) {
    throw new Error(`invalid reviewed evidence record ${index + 1}: attachmentAudit status`);
  }
  if (typeof audit.validAttachmentCount !== "number" || typeof audit.invalidAttachmentCount !== "number") {
    throw new Error(`invalid reviewed evidence record ${index + 1}: attachmentAudit counts`);
  }
  if (!Array.isArray(audit.findings)) {
    throw new Error(`invalid reviewed evidence record ${index + 1}: attachmentAudit findings`);
  }
  audit.findings.forEach((finding, findingIndex) => {
    if (
      typeof finding.attachmentId !== "string"
      || typeof finding.storageRef !== "string"
      || typeof finding.valid !== "boolean"
      || typeof finding.detail !== "string"
    ) {
      throw new Error(`invalid reviewed evidence record ${index + 1}: attachmentAudit finding ${findingIndex + 1}`);
    }
  });
}

function assertValidBackendCoverage(coverage: EvidenceAutopilotBackendCoverage): void {
  if (!coverage || typeof coverage !== "object") {
    throw new Error("backend response evidenceCoverage was not an object");
  }
  if (typeof coverage.totalTasks !== "number") {
    throw new Error("backend response evidenceCoverage totalTasks was not a number");
  }
  if (!Array.isArray(coverage.capturedTaskIds)) {
    throw new Error("backend response evidenceCoverage capturedTaskIds was not an array");
  }
  if (!Array.isArray(coverage.missingP0TaskIds)) {
    throw new Error("backend response evidenceCoverage missingP0TaskIds was not an array");
  }
  if (!Array.isArray(coverage.operatorTaskIds)) {
    throw new Error("backend response evidenceCoverage operatorTaskIds was not an array");
  }
  if (typeof coverage.readyForCounselorReview !== "boolean") {
    throw new Error("backend response evidenceCoverage readyForCounselorReview was not a boolean");
  }
  if (!Array.isArray(coverage.reviewBlockers)) {
    throw new Error("backend response evidenceCoverage reviewBlockers was not an array");
  }
}
