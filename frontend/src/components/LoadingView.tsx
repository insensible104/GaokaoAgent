interface LoadingViewProps {
  currentStep: string;
}

export function LoadingView({ currentStep }: LoadingViewProps) {
  return (
    <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-12 shadow-2xl border border-slate-700 text-center">
      <div className="flex flex-col items-center space-y-8">
        {/* Loading Spinner */}
        <div className="relative">
          <div className="w-24 h-24 border-8 border-purple-600 border-t-transparent rounded-full animate-spin"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-16 h-16 border-8 border-blue-600 border-b-transparent rounded-full animate-spin"></div>
          </div>
        </div>

        {/* Status */}
        <div className="space-y-4">
          <h2 className="text-2xl font-bold text-purple-300">
            AI 正在分析中...
          </h2>
          <p className="text-lg text-gray-300 animate-pulse">
            {currentStep || "初始化..."}
          </p>
        </div>

        {/* Progress Indicators */}
        <div className="w-full max-w-md space-y-2">
          <div className="flex justify-between text-sm text-gray-400">
            <span>Agent 1: 画像构建</span>
            <span>Agent 2: 博弈分析</span>
          </div>
          <div className="flex justify-between text-sm text-gray-400">
            <span>Agent 3: 报告生成</span>
            <span>Agent 4: 风控审计</span>
          </div>
        </div>

        {/* Hint */}
        <p className="text-sm text-gray-400 max-w-md">
          GaokaoAgent 正在运行层级Supervisor架构，
          4个专业Agent协同工作，这可能需要1-2分钟时间...
        </p>
      </div>
    </div>
  );
}
