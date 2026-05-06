import { Button } from "@/components/ui/button";
import ReactMarkdown from "react-markdown";

interface ReportViewProps {
  result: {
    success: boolean;
    message: string;
    report: string | null;
    debug_logs: string[];
  };
  error: string | null;
  onReset: () => void;
}

export function ReportView({ result, error, onReset }: ReportViewProps) {
  if (error || !result.success) {
    return (
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 shadow-2xl border border-red-500">
        <h2 className="text-2xl font-bold mb-4 text-red-400">分析失败</h2>
        <p className="text-gray-300 mb-6">
          {error || result.message || "未知错误"}
        </p>
        <Button
          onClick={onReset}
          className="bg-blue-600 hover:bg-blue-700"
        >
          重新开始
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Success Header */}
      <div className="bg-gradient-to-r from-green-600 to-emerald-600 rounded-2xl p-6 shadow-2xl">
        <h2 className="text-3xl font-bold mb-2">✅ 分析完成</h2>
        <p className="text-green-100">
          GaokaoAgent 已为您生成个性化志愿填报战略建议
        </p>
      </div>

      {/* Report Content */}
      <div className="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 shadow-2xl border border-slate-700">
        <div className="prose prose-invert max-w-none">
          {result.report ? (
            <ReactMarkdown
              components={{
                h1: ({ children }) => (
                  <h1 className="text-3xl font-bold mb-4 text-purple-300">
                    {children}
                  </h1>
                ),
                h2: ({ children }) => (
                  <h2 className="text-2xl font-bold mt-8 mb-4 text-blue-300">
                    {children}
                  </h2>
                ),
                h3: ({ children }) => (
                  <h3 className="text-xl font-semibold mt-6 mb-3 text-gray-200">
                    {children}
                  </h3>
                ),
                p: ({ children }) => (
                  <p className="text-gray-300 mb-4 leading-relaxed">
                    {children}
                  </p>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside space-y-2 mb-4 text-gray-300">
                    {children}
                  </ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside space-y-2 mb-4 text-gray-300">
                    {children}
                  </ol>
                ),
                li: ({ children }) => (
                  <li className="ml-4">{children}</li>
                ),
                strong: ({ children }) => (
                  <strong className="font-bold text-purple-300">
                    {children}
                  </strong>
                ),
                blockquote: ({ children }) => (
                  <blockquote className="border-l-4 border-purple-500 pl-4 italic text-gray-400 my-4">
                    {children}
                  </blockquote>
                ),
              }}
            >
              {result.report}
            </ReactMarkdown>
          ) : (
            <p className="text-gray-400">暂无报告内容</p>
          )}
        </div>
      </div>

      {/* Debug Logs (collapsible) */}
      {result.debug_logs && result.debug_logs.length > 0 && (
        <details className="bg-slate-800/30 rounded-xl p-4 border border-slate-700">
          <summary className="cursor-pointer text-gray-400 hover:text-gray-300">
            调试日志 ({result.debug_logs.length} 条)
          </summary>
          <div className="mt-4 space-y-1 font-mono text-sm">
            {result.debug_logs.map((log, i) => (
              <div key={i} className="text-gray-500">
                {log}
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={onReset}
          className="flex-1 bg-blue-600 hover:bg-blue-700 py-6 text-lg"
        >
          重新分析
        </Button>
        <Button
          onClick={() => {
            if (result.report) {
              // 修复：正确清理Object URL，防止内存泄漏
              const blob = new Blob([result.report], { type: "text/markdown" });
              const url = URL.createObjectURL(blob);
              const a = document.createElement("a");
              a.href = url;
              a.download = "志愿填报建议.md";
              a.click();

              // 修复：延迟清理URL，确保下载完成
              setTimeout(() => {
                URL.revokeObjectURL(url);
              }, 100);
            }
          }}
          className="flex-1 bg-purple-600 hover:bg-purple-700 py-6 text-lg"
        >
          下载报告
        </Button>
      </div>
    </div>
  );
}
