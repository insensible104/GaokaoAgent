import { useState, useEffect, useRef, useCallback, lazy, Suspense } from "react";
import { GaokaoAgentForm } from "@/components/GaokaoAgentForm";
import { ErrorBoundary } from "@/components/ErrorBoundary";

// 修复P3-1: 代码分割 - 懒加载非关键组件
const ReportView = lazy(() => import("@/components/ReportView").then(module => ({ default: module.ReportView })));
const LoadingView = lazy(() => import("@/components/LoadingView").then(module => ({ default: module.LoadingView })));
const ProgressTracker = lazy(() => import("@/components/ProgressTracker").then(module => ({ default: module.ProgressTracker })));
const GameMatrixView = lazy(() => import("@/components/GameMatrixView").then(module => ({ default: module.GameMatrixView })));
const InternalDeliveryReview = lazy(() => import("@/components/InternalDeliveryReview").then(module => ({ default: module.InternalDeliveryReview })));
const InvestmentResearchReportPreview = lazy(() => import("@/components/PathFinderReportTemplate").then(module => ({ default: module.InvestmentResearchReportPreview })));

// 导入类型
import type { GameMatrix } from "@/components/GameMatrixView";
import type { AgentStep } from "@/components/ProgressTracker";
import type { PathFinderReportPayload } from "@/components/PathFinderReportTemplate";

interface AnalysisResult {
  success: boolean;
  message: string;
  report: string | null;
  research_report?: string | null;
  intent_type?: string;
  loop_type?: string;
  game_matrix?: GameMatrix | null;
  user_profile?: Record<string, unknown> | null;
  debug_logs: string[];
}

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
  field_provenance?: Record<string, string>;
  career_assessment?: {
    mode: "skip" | "quick" | "complete";
    answers: Record<string, number>;
    mbti_type?: string;
    career_values: string[];
  };
  holland_code?: Record<string, number>;
  riasec_top_codes?: string[];
  career_assessment_mode?: string;
  career_assessment_status?: string;
  mbti_type?: string;
  mbti_source?: string;
  career_values?: string[];
}

interface AnalysisRequest {
  message: string;
  score?: number;
  rank?: number;
  subject_group?: string;
  scores?: {
    chinese?: number;
    math?: number;
    english?: number;
    physics?: number;
    chemistry?: number;
    biology?: number;
    politics?: number;
    history?: number;
    geography?: number;
  };
  delivery_profile?: DeliveryProfile;
}

// 修复：创建fetchWithTimeout工具函数
const fetchWithTimeout = async (
  url: string,
  options: RequestInit,
  timeout = 60000
): Promise<Response> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return response;
  } finally {
    clearTimeout(timeoutId);
  }
};

const asStringArray = (value: unknown) =>
  Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];

const asBooleanRecord = (value: unknown): Record<string, boolean> => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return {};
  return Object.fromEntries(
    Object.entries(value).filter((entry): entry is [string, boolean] => typeof entry[1] === "boolean")
  );
};

const asNumberRecord = (value: unknown): Record<string, number> | undefined => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  const entries = Object.entries(value).filter((entry): entry is [string, number] => typeof entry[1] === "number");
  return entries.length > 0 ? Object.fromEntries(entries) : undefined;
};

const asStringRecord = (value: unknown): Record<string, string> | undefined => {
  if (!value || typeof value !== "object" || Array.isArray(value)) return undefined;
  const entries = Object.entries(value).filter(
    (entry): entry is [string, string] => typeof entry[1] === "string"
  );
  return entries.length > 0 ? Object.fromEntries(entries) : undefined;
};

const normalizeDeliveryProfile = (
  rawProfile: Record<string, unknown> | null | undefined,
  fallback: DeliveryProfile | null
): DeliveryProfile | null => {
  const raw = rawProfile ?? {};
  const score = Number(raw.score ?? fallback?.score);
  const subjectGroup = String(raw.subject_group ?? fallback?.subject_group ?? "");
  if (!score || !subjectGroup) return fallback;
  const rank = raw.rank ?? fallback?.rank;
  return {
    score,
    rank: rank ? Number(rank) : undefined,
    subject_group: subjectGroup,
    preferred_cities: asStringArray(raw.preferred_cities).length
      ? asStringArray(raw.preferred_cities)
      : fallback?.preferred_cities ?? [],
    excluded_cities: asStringArray(raw.excluded_cities).length
      ? asStringArray(raw.excluded_cities)
      : fallback?.excluded_cities ?? [],
    preferred_majors: asStringArray(raw.preferred_majors).length
      ? asStringArray(raw.preferred_majors)
      : fallback?.preferred_majors ?? [],
    blacklist_majors: asStringArray(raw.blacklist_majors).length
      ? asStringArray(raw.blacklist_majors)
      : fallback?.blacklist_majors ?? [],
    risk_tolerance: typeof raw.risk_tolerance === "string" ? raw.risk_tolerance : fallback?.risk_tolerance ?? "balanced",
    school_major_preference:
      typeof raw.school_major_preference === "string"
        ? raw.school_major_preference
        : fallback?.school_major_preference ?? "unknown",
    stated_misconceptions: asStringArray(raw.stated_misconceptions),
    emotional_concerns: asStringArray(raw.emotional_concerns),
    family_pressure_points: asStringArray(raw.family_pressure_points),
    preference_assumptions: asStringArray(raw.preference_assumptions),
    preference_confidence: typeof raw.preference_confidence === "number" ? raw.preference_confidence : 0.5,
    major_cognition_risk: typeof raw.major_cognition_risk === "number" ? raw.major_cognition_risk : 0,
    regret_sensitivity: typeof raw.regret_sensitivity === "number" ? raw.regret_sensitivity : 0.5,
    medical_restrictions: asBooleanRecord(raw.medical_restrictions),
    subject_scores: asNumberRecord(raw.subject_scores) ?? fallback?.subject_scores,
    field_provenance: asStringRecord(raw.field_provenance) ?? fallback?.field_provenance,
    career_assessment: fallback?.career_assessment,
    holland_code: asNumberRecord(raw.holland_code) ?? fallback?.holland_code,
    riasec_top_codes: asStringArray(raw.riasec_top_codes),
    career_assessment_mode:
      typeof raw.career_assessment_mode === "string"
        ? raw.career_assessment_mode
        : fallback?.career_assessment_mode,
    career_assessment_status:
      typeof raw.career_assessment_status === "string"
        ? raw.career_assessment_status
        : fallback?.career_assessment_status,
    mbti_type: typeof raw.mbti_type === "string" ? raw.mbti_type : fallback?.mbti_type,
    mbti_source: typeof raw.mbti_source === "string" ? raw.mbti_source : fallback?.mbti_source,
    career_values: asStringArray(raw.career_values).length
      ? asStringArray(raw.career_values)
      : fallback?.career_values ?? fallback?.career_assessment?.career_values ?? [],
  };
};

function AppContent() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressSteps, setProgressSteps] = useState<AgentStep[]>([]);
  const [deliveryProfile, setDeliveryProfile] = useState<DeliveryProfile | null>(null);

  // 修复：添加AbortController ref，用于取消请求
  const abortControllerRef = useRef<AbortController | null>(null);

  // 修复：组件卸载时取消请求
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  // 修复P2-4: 使用useCallback避免子组件不必要的重渲染
  const handleSubmit = useCallback(async (data: AnalysisRequest) => {
    // 修复：开发环境可以保留console.log
    const isDev = import.meta.env.DEV;
    if (isDev) console.log("[DEBUG] Form submitted with data:", data);

    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setIsAnalyzing(true);
    setError(null);
    setResult(null);
    setDeliveryProfile(data.delivery_profile || null);

    // 修复：只显示初始状态，等待真实的agent日志
    setProgressSteps([
      { agent: 'system', status: 'running', message: '正在连接 GaokaoAgent AI 引擎...' }
    ]);

    try {
      const apiUrl = import.meta.env.DEV
        ? "http://localhost:8000"
        : import.meta.env.VITE_API_URL || "";

      if (isDev) console.log("[DEBUG] Sending request to:", `${apiUrl}/api/analyze`);

      // 修复：使用fetchWithTimeout添加超时控制
      const response = await fetchWithTimeout(
        `${apiUrl}/api/analyze`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: data.message,
            score: data.score,
            rank: data.rank,
            subject_group: data.subject_group,
            scores: data.scores,
            delivery_profile: data.delivery_profile,
          }),
          signal: abortControllerRef.current.signal,
        },
        180000 // 修复：增加到180秒（3分钟）超时，给后端足够的处理时间
      );

      if (isDev) console.log("[DEBUG] Response status:", response.status);

      if (!response.ok) {
        const errorText = await response.text();
        if (isDev) console.error("[DEBUG] API Error:", errorText);

        // 修复：区分不同的错误类型
        if (response.status === 429) {
          throw new Error("请求过于频繁，请稍后再试");
        } else if (response.status === 400) {
          throw new Error("请求参数错误，请检查输入");
        } else if (response.status === 500) {
          throw new Error("服务器内部错误，请稍后重试");
        } else {
          throw new Error(`请求失败 (${response.status})`);
        }
      }

      const analysisResult: AnalysisResult = await response.json();
      if (isDev) console.log("[DEBUG] Analysis result:", analysisResult);
      if (analysisResult.user_profile) {
        setDeliveryProfile(normalizeDeliveryProfile(analysisResult.user_profile, data.delivery_profile || null));
      }

      // Parse debug logs into progress steps
      const steps = parseDebugLogsToSteps(analysisResult.debug_logs);

      // 新增：流式展示步骤，模拟思考过程
      // 虽然数据是一次性返回的，但逐步显示给用户更好的体验
      setProgressSteps([]); // 先清空
      for (let i = 0; i < steps.length; i++) {
        await new Promise(resolve => setTimeout(resolve, 200)); // 每步延迟200ms
        setProgressSteps(prev => [...prev, steps[i]]);
      }

      setResult(analysisResult);

      if (!analysisResult.success) {
        setError(analysisResult.message);
      }
    } catch (err) {
      // 修复：区分错误类型，提供更好的错误提示
      if (isDev) console.error("[DEBUG] Request failed:", err);

      let errorMessage = "未知错误";

      if (err instanceof Error) {
        if (err.name === "AbortError") {
          errorMessage = "请求已取消";
        } else if (err.message.includes("timeout") || err.name === "TimeoutError") {
          errorMessage = "请求超时，请检查网络连接或稍后重试";
        } else if (err.message.includes("NetworkError") || err.message.includes("Failed to fetch")) {
          errorMessage = "网络连接失败，请稍后重试";
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
      setProgressSteps([
        {
          agent: 'system',
          status: 'failed',
          message: `请求失败: ${errorMessage}`
        }
      ]);

      // 修复：错误信息会在UI中显示，用户可以看到完整的错误提示
    } finally {
      setIsAnalyzing(false);
      abortControllerRef.current = null;
    }
  }, []); // setState函数是稳定的，不需要添加依赖

  // Helper function to parse debug logs into agent steps
  const parseDebugLogsToSteps = (logs: string[]): AgentStep[] => {
    const steps: AgentStep[] = [];

    for (const log of logs) {
      // 匹配不同的日志格式

      // 0. [REASONING] - AI思考推理过程（新增，优先级最高）
      const reasoningMatch = log.match(/\[REASONING\]\s*(.+)/);
      if (reasoningMatch) {
        steps.push({
          agent: 'ai_reasoning',
          status: 'completed',
          message: reasoningMatch[1].trim()
        });
        continue;
      }

      // 1. [OK/WARN/ERROR] Agent: message
      const standardMatch = log.match(/\[(OK|WARN|ERROR)\]\s*([^:]+):\s*(.+)/);
      if (standardMatch) {
        const [, status, agent, message] = standardMatch;
        const agentName = agent.trim().toLowerCase().replace(/\s+/g, '_');

        steps.push({
          agent: agentName,
          status: status === 'OK' ? 'completed' : status === 'ERROR' ? 'failed' : 'running',
          message: message.trim()
        });
        continue;
      }

      // 2. [Router] message - 意图分类
      const routerMatch = log.match(/\[Router\]\s*(.+)/);
      if (routerMatch) {
        steps.push({
          agent: 'meta_router',
          status: 'completed',
          message: routerMatch[1].trim()
        });
        continue;
      }

      // 新增：[Game→Router] - Deep Research触发检测（归类到AI推理）
      const gameRouterMatch = log.match(/\[Game→Router\]\s*(.+)/);
      if (gameRouterMatch) {
        steps.push({
          agent: 'ai_reasoning',
          status: 'completed',
          message: `🔍 ${gameRouterMatch[1].trim()}`
        });
        continue;
      }

      // 新增：[Critic→Router] - Critic触发的路由决策（归类到AI推理）
      const criticRouterMatch = log.match(/\[Critic→Router\]\s*(.+)/);
      if (criticRouterMatch) {
        steps.push({
          agent: 'ai_reasoning',
          status: 'completed',
          message: `⚠️ ${criticRouterMatch[1].trim()}`
        });
        continue;
      }

      // 3. [PLAN/EXECUTE/REFLECT] - Deep Research流程
      const researchMatch = log.match(/\[(PLAN|EXECUTE|REFLECT)\]\s*(.+)/);
      if (researchMatch) {
        const [, phase, message] = researchMatch;
        const cleanMessage = message.replace(/🎯|🔍|🤔/g, '').trim();

        steps.push({
          agent: `deep_research_${phase.toLowerCase()}`,
          status: 'running',
          message: cleanMessage
        });
        continue;
      }

      // 4. [INFO] - 一般信息
      const infoMatch = log.match(/\[INFO\]\s*(.+)/);
      if (infoMatch) {
        steps.push({
          agent: 'system',
          status: 'running',
          message: infoMatch[1].trim()
        });
        continue;
      }
    }

    // If no parsed steps, create default steps
    if (steps.length === 0) {
      steps.push({
        agent: 'system',
        status: 'completed',
        message: '分析完成'
      });
    }

    return steps;
  };

  const handleReset = () => {
    setResult(null);
    setError(null);
    setProgressSteps([]);
    setDeliveryProfile(null);
  };

  const openReportTemplatePreview = useCallback(() => {
    if (!result?.game_matrix) return;
    const payload: PathFinderReportPayload = {
      gameMatrix: result.game_matrix,
      deliveryProfile,
      report: result.report,
      generatedAt: new Date().toISOString(),
    };
    window.sessionStorage.setItem("pathfinder-report-preview", JSON.stringify(payload));
    window.open("/app/report-template-preview", "_blank", "noopener,noreferrer");
  }, [deliveryProfile, result]);

  if (window.location.pathname.includes("report-template-preview")) {
    return (
      <Suspense fallback={<div className="p-8 text-center text-slate-600">Loading report template...</div>}>
        <InvestmentResearchReportPreview />
      </Suspense>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sky-50 via-blue-50 to-cyan-50">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <header className="text-center mb-12">
          <h1 className="text-5xl font-bold mb-4 bg-clip-text text-transparent bg-gradient-to-r from-sky-600 to-cyan-600">
            GaokaoAgent
          </h1>
          <p className="text-xl text-sky-700 font-medium">
            AI驱动的高考志愿决策系统 · 基于博弈论的量化分析
          </p>
        </header>

        {/* Main Content */}
        <main>
          {!result && !isAnalyzing && !error && (
            <GaokaoAgentForm onSubmit={handleSubmit} />
          )}

          {isAnalyzing && (
            <div className="space-y-6">
              <Suspense fallback={<div className="text-center py-4">加载中...</div>}>
                <LoadingView currentStep="分析进行中..." />
                <ProgressTracker
                  steps={progressSteps}
                  currentLoop={undefined}
                  intentType={undefined}
                />
              </Suspense>
            </div>
          )}

          {/* 修复：显示错误状态 */}
          {error && !isAnalyzing && (
            <div className="space-y-6">
              <Suspense fallback={<div className="text-center py-4">加载中...</div>}>
                <ProgressTracker
                  steps={progressSteps}
                  currentLoop={undefined}
                  intentType={undefined}
                />
                {/* 错误提示卡片 */}
                <div className="bg-red-50 backdrop-blur-sm rounded-2xl p-8 shadow-lg border-2 border-red-300">
                  <h2 className="text-2xl font-bold text-red-600 mb-4">⚠️ 请求失败</h2>
                  <p className="text-red-800 mb-6">{error}</p>
                  <button
                    onClick={handleReset}
                    className="px-6 py-3 bg-sky-600 hover:bg-sky-700 text-white rounded-lg font-semibold transition-colors shadow-md"
                  >
                    返回重试
                  </button>
                </div>
              </Suspense>
            </div>
          )}

          {result && !isAnalyzing && (
            <div className="space-y-6">
              <Suspense fallback={<div className="text-center py-4">加载中...</div>}>
                {/* Progress Summary */}
                <ProgressTracker
                  steps={progressSteps}
                  currentLoop={result.loop_type}
                  intentType={result.intent_type}
                />

                {/* Game Matrix View (if available) */}
                {result.game_matrix && (
                  (result.game_matrix.major_group_rows && result.game_matrix.major_group_rows.length > 0) ||
                  (result.game_matrix.rows && result.game_matrix.rows.length > 0)
                ) && (
                  <>
                    <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
                      <div>
                        <h2 className="text-lg font-bold text-slate-900">PathFinder A4 决策报告</h2>
                        <p className="text-sm text-slate-600">
                          将当前推荐、审计摘要、证据边界和学生画像写入可打印报告模板。
                        </p>
                      </div>
                      <button
                        type="button"
                        onClick={openReportTemplatePreview}
                        className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-700"
                      >
                        打开 A4 报告预览
                      </button>
                    </div>
                    <GameMatrixView gameMatrix={result.game_matrix} userProfile={deliveryProfile} />
                  </>
                )}

                <InternalDeliveryReview
                  profile={deliveryProfile}
                  report={result.report}
                />

                {/* Report View */}
                <ReportView
                  result={result}
                  error={error}
                  onReset={handleReset}
                />
              </Suspense>
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="mt-16 text-center text-sky-600 text-sm">
          <p>
            GaokaoAgent · Powered by LangGraph & Ollama ·{" "}
            <span className="text-cyan-600 font-semibold">混合智能架构</span>
          </p>
        </footer>
      </div>
    </div>
  );
}

// 修复：使用错误边界包装整个应用
export default function App() {
  return (
    <ErrorBoundary>
      <AppContent />
    </ErrorBoundary>
  );
}
