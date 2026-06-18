import { useState, memo } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card } from "@/components/ui/card";
import { StudentCareerProfile } from "@/components/StudentCareerProfile";
import {
  isCareerAssessmentComplete,
  type CareerAssessmentPayload,
} from "@/lib/careerAssessment";

interface GaokaoAgentFormProps {
  onSubmit: (data: {
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
    delivery_profile?: {
      score: number;
      rank?: number;
      subject_group: string;
      preferred_cities: string[];
      preferred_majors: string[];
      blacklist_majors: string[];
      risk_tolerance: string;
      school_major_preference: string;
      subject_scores?: Record<string, number>;
      career_assessment?: CareerAssessmentPayload;
    };
  }) => void;
}

const splitList = (value: string) =>
  value
    .split(/[，,、;；\s]+/)
    .map((item) => item.trim())
    .filter(Boolean);

// 修复P2-4: 使用memo优化性能，避免不必要的重渲染
const GaokaoAgentFormComponent = ({ onSubmit }: GaokaoAgentFormProps) => {
  const [totalScore, setTotalScore] = useState("");
  const [rank, setRank] = useState("");
  const [subjectGroup, setSubjectGroup] = useState("物理");

  // 各科分数
  const [chinese, setChinese] = useState("");
  const [math, setMath] = useState("");
  const [english, setEnglish] = useState("");
  const [physics, setPhysics] = useState("");
  const [chemistry, setChemistry] = useState("");
  const [biology, setBiology] = useState("");
  const [politics, setPolitics] = useState("");
  const [history, setHistory] = useState("");
  const [geography, setGeography] = useState("");

  // 偏好信息
  const [preferredCities, setPreferredCities] = useState("");
  const [preferredMajors, setPreferredMajors] = useState("");
  const [blacklistMajors, setBlacklistMajors] = useState("");
  const [riskTolerance, setRiskTolerance] = useState("balanced");
  const [careerAssessment, setCareerAssessment] = useState<CareerAssessmentPayload>({
    mode: "skip",
    answers: {},
    career_values: [],
  });
  const [showCareerValidation, setShowCareerValidation] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!isCareerAssessmentComplete(careerAssessment)) {
      setShowCareerValidation(true);
      return;
    }
    setShowCareerValidation(false);

    // 构建消息
    let message = "我的高考信息如下：\n";

    if (preferredMajors) {
      message += `\n偏好专业：${preferredMajors}`;
    }
    if (blacklistMajors) {
      message += `\n不想学的专业：${blacklistMajors}`;
    }
    if (preferredCities) {
      message += `\n偏好城市：${preferredCities}`;
    }
    message += `\n风险偏好：${riskTolerance === "conservative" ? "保守" : riskTolerance === "balanced" ? "平衡" : "激进"}`;

    const scores: Record<string, number> = {};
    if (chinese) scores.chinese = parseInt(chinese);
    if (math) scores.math = parseInt(math);
    if (english) scores.english = parseInt(english);
    if (physics) scores.physics = parseInt(physics);
    if (chemistry) scores.chemistry = parseInt(chemistry);
    if (biology) scores.biology = parseInt(biology);
    if (politics) scores.politics = parseInt(politics);
    if (history) scores.history = parseInt(history);
    if (geography) scores.geography = parseInt(geography);

    const scoreValue = totalScore ? parseInt(totalScore) : undefined;
    const rankValue = rank ? parseInt(rank) : undefined;
    const subjectScores = Object.keys(scores).length > 0 ? scores : undefined;

    onSubmit({
      message,
      score: scoreValue,
      rank: rankValue,
      subject_group: subjectGroup,
      scores: subjectScores,
      delivery_profile: scoreValue
        ? {
            score: scoreValue,
            rank: rankValue,
            subject_group: subjectGroup,
            preferred_cities: splitList(preferredCities),
            preferred_majors: splitList(preferredMajors),
            blacklist_majors: splitList(blacklistMajors),
            risk_tolerance: riskTolerance,
            school_major_preference: "unknown",
            subject_scores: subjectScores,
            career_assessment: careerAssessment,
          }
        : undefined,
    });
  };

  return (
    <div className="border border-[#D8D2C2] bg-[#FBFAF6] p-6">
      <h2
        id="form-title"
        className="mb-2 text-3xl font-semibold text-[#1B1B1A]"
      >
        填写您的高考信息
      </h2>
      <p id="form-description" className="mb-6 text-sm leading-6 text-[#3E4A5C]">
        请如实填写，系统会把分数、位次、专业偏好和风险边界转成可审计的志愿分析输入。
      </p>

      <form
        onSubmit={handleSubmit}
        className="space-y-8"
        aria-labelledby="form-title"
        aria-describedby="form-description"
      >
        {/* 基本信息卡片 */}
        <Card
          className="border-[#D8D2C2] bg-white p-5 shadow-none"
          role="group"
          aria-labelledby="basic-info-heading"
        >
          <h3
            id="basic-info-heading"
            className="mb-4 text-xl font-semibold text-[#1B1B1A]"
          >
            基本信息
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="totalScore" className="text-[#3E4A5C]">
                高考总分 <span className="text-red-500" aria-label="必填">*</span>
              </Label>
              <Input
                id="totalScore"
                type="number"
                placeholder="例如: 620"
                value={totalScore}
                onChange={(e) => setTotalScore(e.target.value)}
                required
                aria-required="true"
                aria-label="高考总分"
                aria-describedby="totalScore-hint"
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
              <span id="totalScore-hint" className="sr-only">
                请输入您的高考总分，范围0-900
              </span>
            </div>

            <div className="space-y-2">
              <Label htmlFor="rank" className="text-[#3E4A5C]">
                全省位次 <span className="text-red-500" aria-label="必填">*</span>
              </Label>
              <Input
                id="rank"
                type="number"
                placeholder="例如: 12000"
                value={rank}
                onChange={(e) => setRank(e.target.value)}
                required
                aria-required="true"
                aria-label="全省位次"
                aria-describedby="rank-hint"
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
              <span id="rank-hint" className="sr-only">
                请输入您的全省位次
              </span>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject" className="text-[#3E4A5C]">
                选科组合 <span className="text-red-500">*</span>
              </Label>
              <Select value={subjectGroup} onValueChange={setSubjectGroup}>
                <SelectTrigger className="bg-white border-[#D8D2C2] text-[#1B1B1A]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-[#D8D2C2] text-[#1B1B1A]">
                  <SelectItem value="物理">物理类</SelectItem>
                  <SelectItem value="历史">历史类</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* 各科成绩卡片 */}
        <Card className="border-[#D8D2C2] bg-white p-5 shadow-none">
          <h3 className="mb-4 text-xl font-semibold text-[#1B1B1A]">
            各科成绩（可选）
          </h3>
          <p className="mb-4 text-sm leading-6 text-[#3E4A5C]">
            填写各科分数可帮助系统分析您的学科优势，推荐更匹配的专业
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {/* 必考科目 */}
            <div className="space-y-2">
              <Label htmlFor="chinese" className="text-[#3E4A5C]">语文</Label>
              <Input
                id="chinese"
                type="number"
                max="150"
                placeholder="0-150"
                value={chinese}
                onChange={(e) => setChinese(e.target.value)}
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="math" className="text-[#3E4A5C]">数学</Label>
              <Input
                id="math"
                type="number"
                max="150"
                placeholder="0-150"
                value={math}
                onChange={(e) => setMath(e.target.value)}
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="english" className="text-[#3E4A5C]">英语</Label>
              <Input
                id="english"
                type="number"
                max="150"
                placeholder="0-150"
                value={english}
                onChange={(e) => setEnglish(e.target.value)}
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
            </div>

            {/* 选考科目 */}
            {subjectGroup === "物理" && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="physics" className="text-[#3E4A5C]">物理</Label>
                  <Input
                    id="physics"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={physics}
                    onChange={(e) => setPhysics(e.target.value)}
                    className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="chemistry" className="text-[#3E4A5C]">化学</Label>
                  <Input
                    id="chemistry"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={chemistry}
                    onChange={(e) => setChemistry(e.target.value)}
                    className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="biology" className="text-[#3E4A5C]">生物</Label>
                  <Input
                    id="biology"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={biology}
                    onChange={(e) => setBiology(e.target.value)}
                    className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
                  />
                </div>
              </>
            )}

            {subjectGroup === "历史" && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="history" className="text-[#3E4A5C]">历史</Label>
                  <Input
                    id="history"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={history}
                    onChange={(e) => setHistory(e.target.value)}
                    className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="politics" className="text-[#3E4A5C]">政治</Label>
                  <Input
                    id="politics"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={politics}
                    onChange={(e) => setPolitics(e.target.value)}
                    className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="geography" className="text-[#3E4A5C]">地理</Label>
                  <Input
                    id="geography"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={geography}
                    onChange={(e) => setGeography(e.target.value)}
                    className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
                  />
                </div>
              </>
            )}
          </div>
        </Card>

        {/* 志愿偏好卡片 */}
        <Card className="border-[#D8D2C2] bg-white p-5 shadow-none">
          <h3 className="mb-4 text-xl font-semibold text-[#1B1B1A]">
            志愿偏好
          </h3>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="preferredMajors" className="text-[#3E4A5C]">
                想学的专业方向
              </Label>
              <Input
                id="preferredMajors"
                placeholder="例如：计算机、人工智能、电子信息"
                value={preferredMajors}
                onChange={(e) => setPreferredMajors(e.target.value)}
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="blacklistMajors" className="text-[#3E4A5C]">
                不想学的专业（黑名单）
              </Label>
              <Input
                id="blacklistMajors"
                placeholder="例如：土木、化工、生物制药"
                value={blacklistMajors}
                onChange={(e) => setBlacklistMajors(e.target.value)}
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="preferredCities" className="text-[#3E4A5C]">
                偏好城市/地区
              </Label>
              <Input
                id="preferredCities"
                placeholder="例如：北京、上海、江浙、不排斥中西部"
                value={preferredCities}
                onChange={(e) => setPreferredCities(e.target.value)}
                className="bg-white border-[#D8D2C2] text-[#1B1B1A] placeholder-[#736D5A] focus:border-[#A6300E] focus:ring-[#A6300E]"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="risk" className="text-[#3E4A5C]">
                风险偏好
              </Label>
              <Select value={riskTolerance} onValueChange={setRiskTolerance}>
                <SelectTrigger className="bg-white border-[#D8D2C2] text-[#1B1B1A]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-[#D8D2C2] text-[#1B1B1A]">
                  <SelectItem value="conservative">保守型 - 稳妥优先，避免滑档</SelectItem>
                  <SelectItem value="balanced">平衡型 - 冲稳保均衡</SelectItem>
                  <SelectItem value="aggressive">激进型 - 冲刺名校，可承受风险</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        <StudentCareerProfile
          value={careerAssessment}
          onChange={(nextValue) => {
            setCareerAssessment(nextValue);
            if (isCareerAssessmentComplete(nextValue)) setShowCareerValidation(false);
          }}
          showValidation={showCareerValidation}
        />

        {/* 提交按钮 */}
        <Button
          type="submit"
          className="w-full rounded-none bg-[#1B1B1A] py-6 text-lg font-bold text-white shadow-none transition hover:bg-[#3E4A5C]"
        >
          开始证据化分析
        </Button>
      </form>

      {/* 功能说明 */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="border border-[#D8D2C2] bg-white p-4">
          <h4 className="mb-2 font-semibold text-[#1B1B1A]">核心算法</h4>
          <ul className="space-y-1 text-sm text-[#3E4A5C]">
            <li>• 历史位次区间对照</li>
            <li>• 数据年份透明提示</li>
            <li>• 小样本与波动风险惩罚</li>
          </ul>
        </div>

        <div className="border border-[#D8D2C2] bg-white p-4">
          <h4 className="mb-2 font-semibold text-[#1B1B1A]">风险管控</h4>
          <ul className="space-y-1 text-sm text-[#3E4A5C]">
            <li>• 调剂地狱模拟器</li>
            <li>• 黑名单专业预警</li>
            <li>• 4级审计机制</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

// 修复P2-4: 使用memo包装组件
export const GaokaoAgentForm = memo(GaokaoAgentFormComponent);
