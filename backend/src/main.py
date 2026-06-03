"""GaokaoAgent FastAPI server."""

import asyncio
import logging
import os
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from langchain_core.messages import HumanMessage
from pydantic import BaseModel, Field, field_validator
from starlette.middleware.base import BaseHTTPMiddleware

from graph.dual_loop_supervisor import supervisor_graph
from models.state import SupervisorState
from utils.audit_logger import audit_logger
from utils.rate_limiter import RateLimiter


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
            "connect-src 'self' http://localhost:*"
        )
        if IS_PRODUCTION:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        return response


app.add_middleware(SecurityHeadersMiddleware)

allowed_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://localhost:3000",
]

if IS_PRODUCTION:
    production_origin = os.getenv("FRONTEND_URL")
    if production_origin:
        allowed_origins.append(production_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


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
            "api": ["/", "/api/status", "/api/analyze", "/api/stats"],
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

        initial_state: SupervisorState = {
            "messages": [HumanMessage(content=user_message)],
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
