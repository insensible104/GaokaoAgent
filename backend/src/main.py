"""GaokaoAgent FastAPI server."""

import asyncio
import json
import logging
import os
import pathlib
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlsplit
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from graph.dual_loop_supervisor import supervisor_graph
from models.state import SupervisorState
from recommendation.student_profile_assessment import (
    CareerAssessmentInput,
    score_career_assessment,
)
from utils.audit_logger import audit_logger
from utils.rate_limiter import RateLimiter
from evidence_autopilot_api import router as evidence_autopilot_router


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
SERVICE_VERSION = "2.0.0-dual-loop"

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

app = FastAPI(title="GaokaoAgent API - Dual Loop Architecture")


def _mount_built_frontend(app_: FastAPI) -> None:
    """Serve the built frontend under `/app` when `frontend/dist` exists."""
    build_path = (
        pathlib.Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
    )
    if (build_path / "index.html").is_file():
        app_.mount("/app", StaticFiles(directory=build_path, html=True), name="frontend")


_mount_built_frontend(app)

rate_limiter = RateLimiter(requests_per_minute=10)
executor = ThreadPoolExecutor(max_workers=4)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach conservative security headers to API responses."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' http://localhost:* http://127.0.0.1:*"
        )
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

if IS_PRODUCTION:
    production_origins = []
    for raw_origin in os.getenv("FRONTEND_URL", "").split(","):
        parsed = urlsplit(raw_origin.strip())
        if parsed.scheme and parsed.netloc:
            production_origins.append(f"{parsed.scheme}://{parsed.netloc}")
    allowed_origins.extend(production_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)
app.include_router(evidence_autopilot_router)


class SubjectScores(BaseModel):
    """Subject-level score fields."""

    chinese: Optional[int] = None
    math: Optional[int] = None
    english: Optional[int] = None
    physics: Optional[int] = None
    chemistry: Optional[int] = None
    biology: Optional[int] = None
    politics: Optional[int] = None
    history: Optional[int] = None
    geography: Optional[int] = None


class RecommendationProfileInput(BaseModel):
    """User-stated recommendation preferences carried as an explicit contract."""

    score: Optional[int] = Field(None, ge=0, le=900)
    rank: Optional[int] = Field(None, ge=1, le=1_000_000)
    subject_group: Optional[str] = Field(None, min_length=1)
    preferred_cities: Optional[list[str]] = None
    excluded_cities: Optional[list[str]] = None
    preferred_majors: Optional[list[str]] = None
    blacklist_majors: Optional[list[str]] = None
    risk_tolerance: Optional[str] = None
    school_major_preference: Optional[str] = None
    stated_misconceptions: Optional[list[str]] = None
    emotional_concerns: Optional[list[str]] = None
    family_pressure_points: Optional[list[str]] = None
    preference_assumptions: Optional[list[str]] = None
    preference_confidence: Optional[float] = Field(None, ge=0, le=1)
    major_cognition_risk: Optional[float] = Field(None, ge=0, le=1)
    regret_sensitivity: Optional[float] = Field(None, ge=0, le=1)
    medical_restrictions: Optional[dict[str, bool]] = None
    subject_scores: Optional[dict[str, int]] = None
    career_assessment: Optional[CareerAssessmentInput] = None

    @field_validator("subject_group", mode="before")
    @classmethod
    def normalize_recommendation_subject_group(cls, value):
        """Normalize recommendation-profile subject groups."""
        return QueryRequest.normalize_subject_group(value)


class QueryRequest(BaseModel):
    """Request payload for Gaokao planning."""

    message: str = Field(..., min_length=1, max_length=5000, description="User request")
    score: Optional[int] = Field(None, ge=0, le=900, description="Gaokao total score")
    rank: Optional[int] = Field(None, ge=1, le=1_000_000, description="Province rank")
    subject_group: Optional[str] = Field(
        None,
        pattern=r"^(物理|历史|physics|history)$",
        description="Subject group",
    )
    scores: Optional[SubjectScores] = None
    delivery_profile: Optional[RecommendationProfileInput] = None

    @field_validator("subject_group", mode="before")
    @classmethod
    def normalize_subject_group(cls, value):
        """Normalize common API subject-group variants to canonical Chinese labels."""
        if value is None:
            return None
        if not isinstance(value, str):
            return value
        normalized = value.strip().lower()
        if normalized in {"物理", "物理类", "物", "physics"}:
            return "物理"
        if normalized in {"历史", "历史类", "历", "史", "history"}:
            return "历史"
        return value.strip()


class QueryResponse(BaseModel):
    """Response payload for Gaokao planning."""

    success: bool
    message: str
    report: Optional[str] = None
    research_report: Optional[str] = None
    intent_type: Optional[str] = None
    loop_type: Optional[str] = None
    game_matrix: Optional[dict[str, Any]] = None
    user_profile: Optional[dict[str, Any]] = None
    debug_logs: list = Field(default_factory=list)
    orchestration_trace: Optional[list] = None
    orchestration_reward: Optional[float] = None
    agent_messages: Optional[list] = None
    deliberation_summaries: Optional[list] = None


class DeliveryProfileInput(BaseModel):
    """Minimal student profile required for internal delivery preflight."""

    score: int = Field(..., ge=0, le=900)
    rank: Optional[int] = Field(None, ge=1, le=1_000_000)
    subject_group: str = Field(..., min_length=1)
    preferred_cities: list[str] = Field(default_factory=list)
    excluded_cities: list[str] = Field(default_factory=list)
    preferred_majors: list[str] = Field(default_factory=list)
    blacklist_majors: list[str] = Field(default_factory=list)
    risk_tolerance: str = "balanced"
    school_major_preference: str = "unknown"
    stated_misconceptions: list[str] = Field(default_factory=list)
    emotional_concerns: list[str] = Field(default_factory=list)
    family_pressure_points: list[str] = Field(default_factory=list)
    preference_assumptions: list[str] = Field(default_factory=list)
    preference_confidence: float = Field(0.5, ge=0, le=1)
    major_cognition_risk: float = Field(0.0, ge=0, le=1)
    regret_sensitivity: float = Field(0.5, ge=0, le=1)
    medical_restrictions: dict[str, bool] = Field(default_factory=dict)
    subject_scores: Optional[dict[str, int]] = None
    holland_code: Optional[dict[str, float]] = None
    riasec_top_codes: list[str] = Field(default_factory=list)
    career_assessment_mode: str = "skip"
    career_assessment_status: str = "not_taken"
    mbti_type: Optional[str] = None
    mbti_source: Optional[str] = None
    career_values: list[str] = Field(default_factory=list)
    field_provenance: dict[str, str] = Field(default_factory=dict)

    @field_validator("subject_group", mode="before")
    @classmethod
    def normalize_delivery_subject_group(cls, value):
        """Reuse the public API's subject-group normalization behavior."""
        return QueryRequest.normalize_subject_group(value)


def build_explicit_profile_payload(request: QueryRequest) -> dict[str, Any]:
    """Combine explicit core inputs and form preferences into one authoritative payload."""
    payload: dict[str, Any] = {}
    if request.score is not None:
        payload["score"] = request.score
    if request.rank is not None:
        payload["rank"] = request.rank
    if request.subject_group:
        payload["subject_group"] = request.subject_group
    if request.scores is not None:
        subject_scores = request.scores.model_dump(exclude_none=True)
        if subject_scores:
            payload["subject_scores"] = subject_scores

    if request.delivery_profile is not None:
        profile_payload = request.delivery_profile.model_dump(
            exclude_none=True,
            exclude={"career_assessment"},
        )
        payload.update(profile_payload)

        if request.delivery_profile.career_assessment is not None:
            result = score_career_assessment(request.delivery_profile.career_assessment)
            payload["career_assessment_mode"] = result.mode
            payload["career_assessment_status"] = result.status
            provenance = payload.setdefault("_field_provenance", {})
            provenance["career_assessment_mode"] = "measured_assessment"
            provenance["career_assessment_status"] = "measured_assessment"
            if result.holland_code is not None:
                payload["holland_code"] = result.holland_code.model_dump()
                payload["riasec_top_codes"] = result.top_codes
                provenance["holland_code"] = "measured_assessment"
                provenance["riasec_top_codes"] = "measured_assessment"
            if result.mbti_type:
                payload["mbti_type"] = result.mbti_type
                payload["mbti_source"] = "self_reported"
                provenance["mbti_type"] = "user_explicit"
                provenance["mbti_source"] = "user_explicit"
            if result.career_values:
                payload["career_values"] = result.career_values
                provenance["career_values"] = "user_explicit"
    return payload


class DeliveryPreviewRequest(BaseModel):
    """Request payload for internal case-delivery preflight."""

    profile: DeliveryProfileInput
    report: str = Field(..., min_length=1, max_length=120_000)
    plan: Optional[dict[str, Any]] = None
    case_id: Optional[str] = Field(None, max_length=80)


class DeliveryPreviewResponse(BaseModel):
    """Internal delivery preflight response for the frontend workspace."""

    success: bool
    message: str
    case_id: str
    output_dir: str
    manifest: dict[str, Any]
    artifacts: dict[str, str]


class AgencyCommandCenterResponse(BaseModel):
    """Agency-level command center built from saved delivery bundles."""

    success: bool
    message: str
    scanned_bundle_count: int


class DeliveryPortfolioAuditRequest(BaseModel):
    """Request payload for batch delivery-quality review."""

    manifests: list[dict[str, Any]] = Field(..., min_length=1, max_length=200)


class DeliveryPortfolioAuditResponse(BaseModel):
    """Batch delivery-quality audit response for the frontend workspace."""

    success: bool
    message: str
    audit: dict[str, Any]
    markdown: str


class DeliveryManifestArchiveResponse(BaseModel):
    """Recent delivery manifests persisted by internal preflight runs."""

    success: bool
    message: str
    manifest_count: int
    manifests: list[dict[str, Any]]


def _to_plain_data(value: Any) -> Any:
    """Convert Pydantic objects and nested containers to JSON-safe values."""
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    if isinstance(value, list):
        return [_to_plain_data(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_plain_data(item) for key, item in value.items()}
    return value


def _enum_value(value: Any) -> Any:
    """Return enum values while leaving plain strings untouched."""
    return getattr(value, "value", value)


def _safe_case_id(raw_case_id: str | None) -> str:
    """Build a filesystem-safe, human-readable case id."""
    if raw_case_id:
        cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", raw_case_id.strip()).strip("-")
        if cleaned:
            return cleaned[:80]
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"case-{timestamp}-{uuid4().hex[:8]}"


def _load_delivery_bundle_manifests(logs_dir: Path) -> list[dict[str, Any]]:
    """Read delivery bundle manifests from a delivery-bundles log directory."""
    manifests: list[dict[str, Any]] = []
    if not logs_dir.exists():
        return manifests
    for path in sorted(logs_dir.glob("*/delivery_bundle.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(payload, dict):
                payload.setdefault("case_id", path.parent.name)
                manifests.append(payload)
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Skipping invalid delivery bundle %s: %s", path, exc)
    return manifests


def build_agency_command_center_from_logs(logs_dir: Path | None = None) -> dict[str, Any]:
    """Build an agency command-center response from saved delivery bundles."""
    from evaluation.agency_command_center import (
        build_agency_command_center,
        build_markdown_agency_command_center,
    )

    bundle_dir = logs_dir or (BACKEND_ROOT / "logs" / "delivery_bundles")
    manifests = _load_delivery_bundle_manifests(bundle_dir)
    audit = build_agency_command_center(manifests)
    markdown = build_markdown_agency_command_center(audit)
    return {
        "success": True,
        "message": f"机构全局交付驾驶舱已生成：{len(manifests)} 个案源",
        "scanned_bundle_count": len(manifests),
        "audit": audit,
        "markdown": markdown,
    }


def _load_recent_delivery_manifests(logs_root: Path, limit: int = 50) -> list[dict[str, Any]]:
    """Load recent persisted delivery manifests for internal batch review."""
    archive_root = logs_root / "delivery_bundles"
    if not archive_root.exists():
        return []
    candidates = sorted(
        archive_root.glob("*/delivery_bundle.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )[:limit]
    manifests: list[dict[str, Any]] = []
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("Skipping unreadable delivery manifest %s: %s", path, exc)
            continue
        if isinstance(payload, dict):
            payload.setdefault("case_id", path.parent.name)
            payload.setdefault("_archive_path", str(path.relative_to(logs_root)))
            manifests.append(payload)
    return manifests


def _build_delivery_profile(input_profile: DeliveryProfileInput):
    """Convert API input to the canonical UserProfile model."""
    from models.user_profile import HollandCode, RiskTolerance, SchoolMajorPreference, UserProfile

    try:
        risk_tolerance = RiskTolerance(input_profile.risk_tolerance)
    except ValueError:
        risk_tolerance = RiskTolerance.BALANCED

    try:
        school_major_preference = SchoolMajorPreference(
            input_profile.school_major_preference
        )
    except ValueError:
        school_major_preference = SchoolMajorPreference.UNKNOWN

    return UserProfile(
        score=input_profile.score,
        rank=input_profile.rank,
        subject_group=input_profile.subject_group,
        preferred_cities=input_profile.preferred_cities,
        excluded_cities=input_profile.excluded_cities,
        preferred_majors=input_profile.preferred_majors,
        blacklist_majors=input_profile.blacklist_majors,
        risk_tolerance=risk_tolerance,
        school_major_preference=school_major_preference,
        stated_misconceptions=input_profile.stated_misconceptions,
        emotional_concerns=input_profile.emotional_concerns,
        family_pressure_points=input_profile.family_pressure_points,
        preference_assumptions=input_profile.preference_assumptions,
        preference_confidence=input_profile.preference_confidence,
        major_cognition_risk=input_profile.major_cognition_risk,
        regret_sensitivity=input_profile.regret_sensitivity,
        medical_restrictions=input_profile.medical_restrictions,
        subject_scores=input_profile.subject_scores,
        holland_code=HollandCode(**input_profile.holland_code) if input_profile.holland_code else None,
        riasec_top_codes=input_profile.riasec_top_codes,
        career_assessment_mode=input_profile.career_assessment_mode,
        career_assessment_status=input_profile.career_assessment_status,
        mbti_type=input_profile.mbti_type,
        mbti_source=input_profile.mbti_source,
        career_values=input_profile.career_values,
        field_provenance=input_profile.field_provenance,
    )


def _build_delivery_plan(plan_payload: dict[str, Any] | None):
    """Convert an optional API VolunteerPlan payload into the canonical model."""
    if not plan_payload:
        return None
    from models.game_matrix import VolunteerPlan

    plan = VolunteerPlan.model_validate(plan_payload)
    plan.calculate_statistics()
    return plan


def build_user_message(request: QueryRequest) -> str:
    """Build the structured message passed to the supervisor graph."""
    if request.score is None or request.rank is None or not request.subject_group:
        return request.message
    return f"""我的高考信息如下：
- 总分：{request.score}
- 全省位次：{request.rank}
- 选科组合：{request.subject_group}

{request.message}
"""


def _env_flag(name: str) -> bool:
    return os.getenv(name, "0").lower() in {"1", "true", "yes", "on"}


def get_runtime_status() -> dict[str, Any]:
    """Return a compact backend and agent capability snapshot."""
    frontend_dist = REPO_ROOT / "frontend" / "dist" / "index.html"
    backend_data = BACKEND_ROOT / "data"
    root_data = REPO_ROOT / "data"
    return {
        "service": "GaokaoAgent",
        "version": SERVICE_VERSION,
        "architecture": "Meta-Router + Fast/Slow/Multimodal Loops",
        "status": "running",
        "runtime": {
            "environment": ENVIRONMENT,
            "is_production": IS_PRODUCTION,
            "python": sys.version.split()[0],
        },
        "capabilities": {
            "structured_recommendation": True,
            "multi_agent_deliberation": True,
            "critic_audit": True,
            "deep_research": True,
            "orchestration_alignment": True,
            "llm_advisors_enabled": _env_flag("ENABLE_LLM_ADVISORS"),
            "llm_critic_enabled": _env_flag("ENABLE_LLM_CRITIC"),
            "learned_supervisor_enabled": _env_flag("ENABLE_LEARNED_SUPERVISOR_POLICY"),
            "llm_supervisor_enabled": _env_flag("ENABLE_LLM_SUPERVISOR_POLICY"),
            "reward_model_supervisor_enabled": _env_flag("ENABLE_REWARD_MODEL_SUPERVISOR"),
        },
        "data": {
            "backend_data_exists": backend_data.exists(),
            "root_data_exists": root_data.exists(),
            "frontend_dist_exists": frontend_dist.exists(),
        },
        "entrypoints": {
            "api": [
                "/",
                "/api/status",
                "/api/analyze",
                "/api/delivery/preview",
                "/api/delivery/portfolio",
                "/api/delivery/manifests/recent",
                "/api/evidence-autopilot/research",
                "/api/evidence-autopilot/reviewed-evidence",
                "/api/evidence-autopilot/reviewed-evidence/{case_id}",
                "/api/stats",
            ],
            "cli_commands": [
                "smoke",
                "rollout",
                "build-pairwise",
                "eval-orchestration",
                "backtest-2025",
                "ablate-2025",
            ],
        },
    }


@app.get("/")
def read_root():
    """Health-check endpoint."""
    return get_runtime_status()


@app.get("/api/status")
def get_status():
    """Return backend and agent capability status."""
    return get_runtime_status()


@app.post("/api/analyze", response_model=QueryResponse)
async def analyze_application(request: QueryRequest, req: Request):
    """Run the supervisor graph and return recommendation artifacts."""
    client_ip = req.client.host if req.client else "unknown"
    user_agent = req.headers.get("user-agent", "unknown")
    session_id = req.headers.get("x-session-id", "unknown")

    allowed, remaining = rate_limiter.is_allowed(client_ip)
    audit_logger.log_request(
        method=req.method,
        path=req.url.path,
        ip_address=client_ip,
        user_agent=user_agent,
        session_id=session_id,
    )

    if not allowed:
        audit_logger.log_rate_limit(client_ip, remaining)
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Limit: {rate_limiter.requests_per_minute} per minute.",
        )

    logger.info(f"Request from {client_ip}, remaining quota: {remaining}")
    start_time = time.time()

    try:
        user_message = build_user_message(request)
        explicit_profile = build_explicit_profile_payload(request)

        initial_state: SupervisorState = {
            "messages": [HumanMessage(content=user_message)],
            "explicit_profile": explicit_profile or None,
            "intent_classification": None,
            "active_loop": None,
            "loop_history": [],
            "user_profile": None,
            "game_matrix": None,
            "report_draft": None,
            "research_topic": None,
            "search_queries": [],
            "web_research_results": [],
            "knowledge_gaps": [],
            "research_loop_count": 0,
            "research_report": None,
            "pdf_sources": [],
            "vision_results": [],
            "health_restrictions": [],
            "audit_result": None,
            "step_rewards": [],
            "reflection_history": [],
            "orchestration_trace": [],
            "next_action": None,
            "orchestration_reward": None,
            "orchestration_reward_components": None,
            "agent_messages": [],
            "agent_memories": [],
            "deliberation_summaries": [],
            "protocol_violations": [],
            "recommended_next_action": None,
            "current_agent": "",
            "retry_count": 0,
            "human_approved": False,
            "max_loops": 3,
            "debug_logs": [],
        }

        print("=" * 60)
        print("[INFO] GaokaoAgent Dual-Loop starting...")
        print("=" * 60)
        print(f"[DEBUG] About to invoke supervisor_graph with message: {user_message[:100]}...")
        print("[DEBUG] Calling supervisor_graph.invoke() in thread pool...")

        loop = asyncio.get_event_loop()
        final_state = await loop.run_in_executor(
            executor,
            lambda: supervisor_graph.invoke(initial_state, config={"recursion_limit": 50}),
        )

        intent = final_state.get("intent_classification")
        active_loop = final_state.get("active_loop")
        report_draft = final_state.get("report_draft")
        research_report = final_state.get("research_report")
        audit = final_state.get("audit_result")
        game_matrix = final_state.get("game_matrix")
        user_profile = final_state.get("user_profile")

        success = False
        warning_message = None

        if active_loop and _enum_value(active_loop) == "slow":
            success = research_report is not None
        elif report_draft and game_matrix:
            success = True
            if audit and not audit.is_approved:
                warning_message = f"推荐已生成，但存在以下建议：{'; '.join(audit.issues[:2])}"
        elif report_draft or research_report:
            success = True

        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_analysis(
            session_id=session_id,
            ip_address=client_ip,
            score=request.score,
            rank=request.rank,
            subject_group=request.subject_group,
            success=success,
            duration_ms=duration_ms,
        )

        try:
            from rl.supervisor_policy import persist_trace

            persist_trace(session_id=session_id, state=final_state)
        except Exception as trace_error:
            logger.warning(f"Failed to persist orchestration trace: {trace_error}")

        primary_intent = getattr(intent, "primary_intent", None)
        return QueryResponse(
            success=success,
            message=warning_message if warning_message else ("分析完成" if success else "分析未完成"),
            report=report_draft.full_markdown if report_draft else None,
            research_report=research_report,
            intent_type=_enum_value(primary_intent) if primary_intent else None,
            loop_type=_enum_value(active_loop) if active_loop else None,
            game_matrix=_to_plain_data(game_matrix),
            user_profile=_to_plain_data(user_profile),
            debug_logs=final_state.get("debug_logs", []),
            orchestration_trace=final_state.get("orchestration_trace", []),
            orchestration_reward=final_state.get("orchestration_reward"),
            agent_messages=_to_plain_data(final_state.get("agent_messages", [])),
            deliberation_summaries=_to_plain_data(
                final_state.get("deliberation_summaries", [])
            ),
        )

    except Exception as exc:
        print("=" * 80, file=sys.stderr)
        print(f"EXCEPTION: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        logger.error("Request processing failed", exc_info=True)

        duration_ms = int((time.time() - start_time) * 1000)
        audit_logger.log_exception(
            exception=exc,
            context={
                "score": request.score,
                "rank": request.rank,
                "subject_group": request.subject_group,
                "duration_ms": duration_ms,
            },
            session_id=session_id,
            ip_address=client_ip,
        )

        if IS_PRODUCTION:
            raise HTTPException(
                status_code=500,
                detail="Internal server error. Please try again later.",
            ) from exc
        raise HTTPException(status_code=500, detail=f"Development error: {exc}") from exc


@app.post("/api/delivery/preview", response_model=DeliveryPreviewResponse)
async def preview_delivery_bundle(request: DeliveryPreviewRequest):
    """Generate an internal delivery preflight bundle for one analyzed case."""
    try:
        from evaluation.delivery_bundle import build_delivery_bundle

        case_id = _safe_case_id(request.case_id)
        output_dir = BACKEND_ROOT / "logs" / "delivery_bundles" / case_id
        manifest = build_delivery_bundle(
            profile=_build_delivery_profile(request.profile),
            report_payload=request.report,
            output_dir=output_dir,
            plan=_build_delivery_plan(request.plan),
            case_id=case_id,
        )
        artifact_contents: dict[str, str] = {}
        bundle_index_path = output_dir / "delivery_bundle.md"
        if bundle_index_path.is_file():
            artifact_contents["delivery_bundle"] = bundle_index_path.read_text(
                encoding="utf-8"
            )
        for artifact in manifest.get("artifacts", []) or []:
            path = output_dir / str(artifact.get("path", ""))
            if path.is_file() and path.suffix == ".md":
                artifact_contents[str(artifact.get("id", path.stem))] = path.read_text(
                    encoding="utf-8"
                )

        status = str(manifest.get("status", "unknown"))
        return DeliveryPreviewResponse(
            success=status in {"ready_to_deliver", "pending_signoff", "needs_revision"},
            message=f"交付预检完成：{status}",
            case_id=case_id,
            output_dir=str(output_dir.relative_to(BACKEND_ROOT)),
            manifest=manifest,
            artifacts=artifact_contents,
        )
    except Exception as exc:
        logger.error("Delivery preview failed", exc_info=True)
        if IS_PRODUCTION:
            raise HTTPException(status_code=500, detail="Unable to build delivery preview") from exc
        raise HTTPException(status_code=500, detail=f"Development error: {exc}") from exc


@app.get("/api/delivery/portfolio", response_model=AgencyCommandCenterResponse)
async def get_delivery_portfolio():
    """Return the agency-level command center across saved delivery bundles."""
    try:
        return AgencyCommandCenterResponse(**build_agency_command_center_from_logs())
    except Exception as exc:
        logger.error("Agency command center failed", exc_info=True)
        if IS_PRODUCTION:
            raise HTTPException(status_code=500, detail="Unable to build agency command center") from exc
        raise HTTPException(status_code=500, detail=f"Development error: {exc}") from exc


@app.get("/api/delivery/manifests/recent", response_model=DeliveryManifestArchiveResponse)
async def recent_delivery_manifests(
    limit: int = Query(50, ge=1, le=200),
):
    """Return recent persisted delivery manifests from the local backend archive."""
    try:
        manifests = _load_recent_delivery_manifests(BACKEND_ROOT / "logs", limit=limit)
        return DeliveryManifestArchiveResponse(
            success=True,
            message=f"已载入 {len(manifests)} 个本机交付归档",
            manifest_count=len(manifests),
            manifests=manifests,
        )
    except Exception as exc:
        logger.error("Recent delivery manifest load failed", exc_info=True)
        if IS_PRODUCTION:
            raise HTTPException(status_code=500, detail="Unable to load delivery manifests") from exc
        raise HTTPException(status_code=500, detail=f"Development error: {exc}") from exc


@app.post("/api/delivery/portfolio", response_model=DeliveryPortfolioAuditResponse)
async def audit_delivery_portfolio_api(request: DeliveryPortfolioAuditRequest):
    """Aggregate many delivery manifests into an internal service-quality audit."""
    try:
        from evaluation.delivery_portfolio import (
            audit_delivery_portfolio,
            build_markdown_delivery_portfolio_audit,
        )

        result = audit_delivery_portfolio(request.manifests)
        status = str(result.get("status", "unknown"))
        return DeliveryPortfolioAuditResponse(
            success=status not in {"no_cases"},
            message=f"批量交付复盘完成：{status}",
            audit=result,
            markdown=build_markdown_delivery_portfolio_audit(result),
        )
    except Exception as exc:
        logger.error("Delivery portfolio audit failed", exc_info=True)
        if IS_PRODUCTION:
            raise HTTPException(status_code=500, detail="Unable to audit delivery portfolio") from exc
        raise HTTPException(status_code=500, detail=f"Development error: {exc}") from exc


@app.get("/api/stats")
async def get_stats():
    """Return data statistics for the quant engine."""
    try:
        from engines.quant_engine import GaokaoQuantEngine

        candidate_dirs = [
            BACKEND_ROOT / "data",
            REPO_ROOT / "backend" / "data",
            Path.cwd() / "data",
            REPO_ROOT / "data",
        ]
        data_dir = next(
            (
                path
                for path in candidate_dirs
                if path.exists() and any(path.glob("2024_*.csv"))
            ),
            BACKEND_ROOT / "data",
        )

        engine = GaokaoQuantEngine(data_dir=str(data_dir))
        return engine.get_statistics()
    except Exception as exc:
        logger.error(f"Stats request failed: {exc}", exc_info=True)
        if IS_PRODUCTION:
            raise HTTPException(status_code=500, detail="Unable to load statistics") from exc
        raise HTTPException(status_code=500, detail=f"Development error: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("API_HOST", "127.0.0.1")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run(app, host=host, port=port)
