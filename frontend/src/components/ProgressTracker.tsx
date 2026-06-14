/**
 * Real-time progress tracker component
 * Displays actual agent execution logs from backend
 */
import React from 'react';

export interface AgentStep {
  agent: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  message: string;
  timestamp?: string;
}

interface ProgressTrackerProps {
  steps: AgentStep[];
  currentLoop?: string;
  intentType?: string;
}

const agentDisplayNames: Record<string, string> = {
  'meta_router': '🎯 意图识别路由',
  'profiling_agent': '👤 用户画像分析',
  'game_agent': '🎮 量化匹配引擎',
  'report_agent': '📊 报告生成',
  'critic_agent': '🔍 质量审计',
  'deep_research': '🧠 深度研究',
  'deep_research_plan': '🎯 深度研究 - 规划拆解',
  'deep_research_execute': '🔍 深度研究 - 执行搜索',
  'deep_research_reflect': '🤔 深度研究 - 反思评估',
  'multimodal_parser': '🖼️ 多模态解析',
  'ai_reasoning': '🧠 AI 智能推理',
  'system': '⚙️ 系统'
};

const loopDisplayNames: Record<string, string> = {
  'fast': '快思考循环 (量化分析)',
  'slow': '慢思考循环 (深度研究)',
  'multimodal': '多模态循环 (图文解析)',
  'hybrid': '混合循环'
};

const intentDisplayNames: Record<string, string> = {
  'quant': '量化志愿推荐',
  'research': '政策研究',
  'multimodal': '图像解析'
};

const formatAgentName = (agent: string): string => {
  if (agentDisplayNames[agent]) return agentDisplayNames[agent];
  const normalized = agent.toLowerCase();
  if (normalized.includes('router')) return '🎯 意图识别路由';
  if (normalized.includes('profiling')) return '👤 用户画像分析';
  if (normalized.includes('report')) return '📊 报告生成';
  if (normalized.includes('plan_fell_back')) return '🎯 研究规划';
  if (normalized.includes('reflect_fell_back')) return '🤔 证据评估';
  if (normalized.includes('synthesize_fell_back')) return '📊 研究结论';
  return agent;
};

const formatProgressMessage = (step: AgentStep): string => {
  const message = step.message || '';
  const technicalConnectionFailure =
    /HTTPConnectionPool|NewConnectionError|WinError|localhost:11434|\/api\/chat/i.test(message);
  if (technicalConnectionFailure) {
    if (step.agent.toLowerCase().includes('report')) {
      return '生成式报告服务暂不可用，已使用结构化报告完成本次分析。';
    }
    return '智能分析服务暂不可用，已切换到稳定量化方案。';
  }
  return message.length > 240 ? `${message.slice(0, 237)}...` : message;
};

export const ProgressTracker: React.FC<ProgressTrackerProps> = ({
  steps,
  currentLoop,
  intentType
}) => {
  return (
    <div className="bg-gradient-to-br from-sky-50 to-blue-50 rounded-2xl shadow-lg p-6 mb-6 border border-sky-200">
      {/* Header: Loop and Intent Information */}
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-sky-900">执行进度</h3>
        <div className="flex gap-4 text-sm">
          {intentType && (
            <div className="px-3 py-1 bg-sky-100 text-sky-800 rounded-full border border-sky-300">
              {intentDisplayNames[intentType] || intentType}
            </div>
          )}
          {currentLoop && (
            <div className="px-3 py-1 bg-cyan-100 text-cyan-800 rounded-full border border-cyan-300">
              {loopDisplayNames[currentLoop] || currentLoop}
            </div>
          )}
        </div>
      </div>

      {/* Progress Steps */}
      <div className="space-y-3">
        {steps.map((step, index) => {
          // 特殊样式：AI推理步骤（紫粉色渐变）
          const isReasoning = step.agent === 'ai_reasoning';

          return (
            <div
              key={index}
              className={`flex items-start gap-3 p-4 rounded-xl transition-all shadow-sm border ${
                isReasoning
                  ? 'bg-gradient-to-r from-purple-50 to-pink-50 border-purple-300'
                  : ''
              }`}
              style={!isReasoning ? {
                backgroundColor:
                  step.status === 'completed'
                    ? '#ecfeff'  // cyan-50 - 天蓝完成态
                    : step.status === 'running'
                    ? '#f0f9ff'  // sky-50 - 天蓝执行态
                    : step.status === 'failed'
                    ? '#fef2f2'  // red-50 - 柔和的红色失败态
                    : '#f8fafc',  // slate-50 - 浅灰待定态
                borderColor:
                  step.status === 'completed'
                    ? '#67e8f9'  // cyan-300
                    : step.status === 'running'
                    ? '#7dd3fc'  // sky-300
                    : step.status === 'failed'
                    ? '#fca5a5'  // red-300
                    : '#e2e8f0'   // slate-200
              } : undefined}
            >
            {/* Status Icon */}
            <div className="flex-shrink-0 mt-1">
              {step.status === 'completed' && (
                <svg className="w-5 h-5 text-cyan-600" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {step.status === 'running' && (
                <svg
                  className="w-5 h-5 text-sky-600 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle
                    className="opacity-25"
                    cx="12"
                    cy="12"
                    r="10"
                    stroke="currentColor"
                    strokeWidth="4"
                  />
                  <path
                    className="opacity-75"
                    fill="currentColor"
                    d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                  />
                </svg>
              )}
              {step.status === 'failed' && (
                <svg className="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
              {step.status === 'pending' && (
                <svg className="w-5 h-5 text-slate-400" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>

            {/* Step Content */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="font-semibold text-sky-900">
                  {formatAgentName(step.agent)}
                </span>
                {step.timestamp && (
                  <span className="text-xs text-sky-600">{step.timestamp}</span>
                )}
              </div>
              <p className="text-sm text-sky-800 leading-relaxed">{formatProgressMessage(step)}</p>
            </div>
          </div>
          );
        })}
      </div>

      {/* Empty State */}
      {steps.length === 0 && (
        <div className="text-center py-8 text-sky-600">
          <svg
            className="mx-auto h-12 w-12 text-sky-400 mb-2"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13 10V3L4 14h7v7l9-11h-7z"
            />
          </svg>
          <p>等待开始分析...</p>
        </div>
      )}
    </div>
  );
};
