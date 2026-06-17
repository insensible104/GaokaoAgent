import { BrainCircuit, Check, Compass } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  isCareerAssessmentComplete,
  requiredCareerQuestionIds,
  type CareerAssessmentMode,
  type CareerAssessmentPayload,
} from "@/lib/careerAssessment";

interface StudentCareerProfileProps {
  value: CareerAssessmentPayload;
  onChange: (value: CareerAssessmentPayload) => void;
  showValidation?: boolean;
}

interface AssessmentQuestion {
  id: string;
  dimension: "R" | "I" | "A" | "S" | "E" | "C";
  text: string;
}

const QUESTIONS: AssessmentQuestion[] = [
  { id: "R1", dimension: "R", text: "喜欢动手组装、维修或操作设备" },
  { id: "R2", dimension: "R", text: "喜欢户外、工程或解决具体实物问题" },
  { id: "R3", dimension: "R", text: "喜欢机械、建筑或实验器材" },
  { id: "R4", dimension: "R", text: "喜欢通过实践而不是纯讨论学习" },
  { id: "R5", dimension: "R", text: "能接受需要现场操作的工作环境" },
  { id: "I1", dimension: "I", text: "喜欢分析复杂问题并寻找规律" },
  { id: "I2", dimension: "I", text: "喜欢科学实验、数据或编程推理" },
  { id: "I3", dimension: "I", text: "遇到问题会追问原因和证据" },
  { id: "I4", dimension: "I", text: "喜欢独立研究陌生主题" },
  { id: "I5", dimension: "I", text: "享受数学、逻辑或模型推演" },
  { id: "A1", dimension: "A", text: "喜欢写作、设计、音乐或视觉表达" },
  { id: "A2", dimension: "A", text: "喜欢开放性问题和原创方案" },
  { id: "A3", dimension: "A", text: "对审美、语言和叙事敏感" },
  { id: "A4", dimension: "A", text: "不喜欢答案唯一的任务" },
  { id: "A5", dimension: "A", text: "希望工作允许表达个人风格" },
  { id: "S1", dimension: "S", text: "喜欢帮助、教学或倾听他人" },
  { id: "S2", dimension: "S", text: "关注人的成长、健康和关系" },
  { id: "S3", dimension: "S", text: "擅长解释复杂内容" },
  { id: "S4", dimension: "S", text: "团队中常承担协调支持角色" },
  { id: "S5", dimension: "S", text: "希望工作能直接改善他人生活" },
  { id: "E1", dimension: "E", text: "喜欢说服、组织或推动事情落地" },
  { id: "E2", dimension: "E", text: "愿意承担竞争、决策和领导责任" },
  { id: "E3", dimension: "E", text: "对商业机会和资源配置感兴趣" },
  { id: "E4", dimension: "E", text: "喜欢公开表达并影响群体" },
  { id: "E5", dimension: "E", text: "享受设定目标并带队完成" },
  { id: "C1", dimension: "C", text: "喜欢清晰规则、计划和准确记录" },
  { id: "C2", dimension: "C", text: "擅长整理数据、流程和细节" },
  { id: "C3", dimension: "C", text: "希望任务标准明确可检查" },
  { id: "C4", dimension: "C", text: "对财务、表格或规范化工作不排斥" },
  { id: "C5", dimension: "C", text: "能长期保持稳定和有序" },
];

const MODE_OPTIONS: Array<{ mode: CareerAssessmentMode; title: string; detail: string }> = [
  { mode: "skip", title: "跳过测评", detail: "不影响生成基础方案" },
  { mode: "quick", title: "12题快速版", detail: "约 2 分钟" },
  { mode: "complete", title: "30题完整版", detail: "约 5 分钟" },
];

const DIMENSION_LABELS: Record<string, string> = {
  R: "R 实用型",
  I: "I 研究型",
  A: "A 艺术型",
  S: "S 社会型",
  E: "E 企业型",
  C: "C 常规型",
};

const MBTI_TYPES = [
  "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP",
  "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ",
];

const CAREER_VALUES = [
  { value: "stability", label: "稳定保障" },
  { value: "income", label: "收入回报" },
  { value: "growth", label: "成长空间" },
  { value: "autonomy", label: "自主选择" },
  { value: "creativity", label: "创造表达" },
  { value: "social_impact", label: "社会价值" },
  { value: "work_life_balance", label: "工作生活平衡" },
  { value: "leadership", label: "影响力与领导" },
];

export function StudentCareerProfile({ value, onChange, showValidation = false }: StudentCareerProfileProps) {
  const visibleQuestions = QUESTIONS.filter((question) =>
    requiredCareerQuestionIds(value.mode).includes(question.id),
  );
  const answeredCount = visibleQuestions.filter((question) => value.answers[question.id]).length;
  const complete = isCareerAssessmentComplete(value);

  const setMode = (mode: CareerAssessmentMode) => {
    onChange({ ...value, mode, answers: {} });
  };

  const setAnswer = (questionId: string, score: number) => {
    onChange({ ...value, answers: { ...value.answers, [questionId]: score } });
  };

  const toggleCareerValue = (careerValue: string) => {
    const selected = value.career_values.includes(careerValue);
    if (!selected && value.career_values.length >= 3) return;
    onChange({
      ...value,
      career_values: selected
        ? value.career_values.filter((item) => item !== careerValue)
        : [...value.career_values, careerValue],
    });
  };

  return (
    <Card className="p-6 bg-white border-sky-300">
      <div className="flex items-start gap-3">
        <Compass className="mt-0.5 h-5 w-5 shrink-0 text-teal-700" aria-hidden="true" />
        <div>
          <h3 className="text-xl font-semibold text-gray-900">职业兴趣探索</h3>
          <p className="mt-1 text-sm text-gray-600">
            RIASEC 只作为专业方向的辅助排序信号，明确偏好和不接受专业始终优先。
          </p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-3" role="group" aria-label="测评深度">
        {MODE_OPTIONS.map((option) => {
          const selected = value.mode === option.mode;
          return (
            <button
              key={option.mode}
              type="button"
              aria-pressed={selected}
              onClick={() => setMode(option.mode)}
              className={`min-h-16 border px-4 py-3 text-left transition-colors ${
                selected
                  ? "border-teal-600 bg-teal-50 text-teal-950"
                  : "border-gray-200 bg-white text-gray-800 hover:border-teal-300"
              }`}
            >
              <span className="flex items-center justify-between gap-2 font-semibold">
                {option.title}
                {selected && <Check className="h-4 w-4 shrink-0" aria-hidden="true" />}
              </span>
              <span className="mt-1 block text-xs text-gray-600">{option.detail}</span>
            </button>
          );
        })}
      </div>

      {value.mode !== "skip" && (
        <div className="mt-6 border-t border-gray-200 pt-5">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h4 className="font-semibold text-gray-900">RIASEC 兴趣题</h4>
              <p className="text-xs text-gray-600">1 表示很不符合，5 表示很符合</p>
            </div>
            <span className={`text-sm font-medium ${complete ? "text-teal-700" : "text-gray-600"}`}>
              {answeredCount}/{visibleQuestions.length}
            </span>
          </div>

          <div className="mt-4 space-y-3">
            {visibleQuestions.map((question) => (
              <div
                key={question.id}
                className="grid min-h-20 grid-cols-1 gap-3 border-b border-gray-100 pb-3 md:grid-cols-[minmax(0,1fr)_220px] md:items-center"
              >
                <div className="min-w-0">
                  <span className="text-xs font-semibold text-teal-700">{DIMENSION_LABELS[question.dimension]}</span>
                  <p className="mt-1 text-sm text-gray-900">{question.text}</p>
                </div>
                <div className="grid grid-cols-5 gap-1" role="group" aria-label={`${question.text}符合程度`}>
                  {[1, 2, 3, 4, 5].map((score) => (
                    <button
                      key={score}
                      type="button"
                      aria-pressed={value.answers[question.id] === score}
                      onClick={() => setAnswer(question.id, score)}
                      className={`h-10 min-w-0 border text-sm font-semibold transition-colors ${
                        value.answers[question.id] === score
                          ? "border-teal-600 bg-teal-600 text-white"
                          : "border-gray-200 bg-white text-gray-700 hover:border-teal-300"
                      }`}
                    >
                      {score}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {showValidation && !complete && (
            <p className="mt-3 text-sm font-medium text-red-700" role="alert">
              请完成当前版本的全部题目，或选择“跳过测评”。
            </p>
          )}
        </div>
      )}

      <div className="mt-6 grid grid-cols-1 gap-6 border-t border-gray-200 pt-5 lg:grid-cols-2">
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <BrainCircuit className="h-4 w-4 text-gray-600" aria-hidden="true" />
            <Label htmlFor="mbti-type" className="text-gray-900">MBTI（可选自报）</Label>
          </div>
          <Select
            value={value.mbti_type ?? "unknown"}
            onValueChange={(mbtiType) => onChange({
              ...value,
              mbti_type: mbtiType === "unknown" ? undefined : mbtiType,
            })}
          >
            <SelectTrigger id="mbti-type" className="bg-white border-gray-300 text-gray-900">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-white border-gray-300 text-gray-900">
              <SelectItem value="unknown">不清楚 / 不填写</SelectItem>
              {MBTI_TYPES.map((type) => <SelectItem key={type} value={type}>{type}</SelectItem>)}
            </SelectContent>
          </Select>
          <p className="text-xs text-gray-600">仅用于沟通和自我描述，不决定专业。</p>
        </div>

        <div>
          <div className="flex flex-wrap items-center justify-between gap-2">
            <Label className="text-gray-900">职业价值观</Label>
            <span className="text-xs text-gray-600">最多选择 3 项 · {value.career_values.length}/3</span>
          </div>
          <div className="mt-2 flex flex-wrap gap-2">
            {CAREER_VALUES.map((item) => {
              const selected = value.career_values.includes(item.value);
              const disabled = !selected && value.career_values.length >= 3;
              return (
                <button
                  key={item.value}
                  type="button"
                  aria-pressed={selected}
                  disabled={disabled}
                  onClick={() => toggleCareerValue(item.value)}
                  className={`border px-3 py-2 text-sm transition-colors disabled:cursor-not-allowed disabled:opacity-40 ${
                    selected
                      ? "border-amber-600 bg-amber-50 text-amber-950"
                      : "border-gray-200 bg-white text-gray-800 hover:border-amber-300"
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </Card>
  );
}
