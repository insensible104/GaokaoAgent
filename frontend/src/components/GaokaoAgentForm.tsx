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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

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
          }
        : undefined,
    });
  };

  return (
    <div className="bg-gradient-to-br from-white to-sky-50 rounded-2xl p-8 shadow-lg border-2 border-sky-200">
      <h2
        id="form-title"
        className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-r from-sky-600 to-cyan-600"
      >
        填写您的高考信息
      </h2>
      <p id="form-description" className="text-sky-700 mb-6">
        请如实填写，系统将基于量化算法为您生成个性化志愿方案
      </p>

      <form
        onSubmit={handleSubmit}
        className="space-y-8"
        aria-labelledby="form-title"
        aria-describedby="form-description"
      >
        {/* 基本信息卡片 */}
        <Card
          className="p-6 bg-sky-50/50 border-sky-300"
          role="group"
          aria-labelledby="basic-info-heading"
        >
          <h3
            id="basic-info-heading"
            className="text-xl font-semibold mb-4 text-sky-700 flex items-center"
          >
            <span className="mr-2" aria-hidden="true">📊</span> 基本信息
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <Label htmlFor="totalScore" className="text-sky-800">
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
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
              <span id="totalScore-hint" className="sr-only">
                请输入您的高考总分，范围0-900
              </span>
            </div>

            <div className="space-y-2">
              <Label htmlFor="rank" className="text-sky-800">
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
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
              <span id="rank-hint" className="sr-only">
                请输入您的全省位次
              </span>
            </div>

            <div className="space-y-2">
              <Label htmlFor="subject" className="text-sky-800">
                选科组合 <span className="text-red-500">*</span>
              </Label>
              <Select value={subjectGroup} onValueChange={setSubjectGroup}>
                <SelectTrigger className="bg-white border-sky-300 text-sky-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-sky-300 text-sky-900">
                  <SelectItem value="物理">物理类</SelectItem>
                  <SelectItem value="历史">历史类</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* 各科成绩卡片 */}
        <Card className="p-6 bg-sky-50/50 border-sky-300">
          <h3 className="text-xl font-semibold mb-4 text-cyan-700 flex items-center">
            <span className="mr-2">📝</span> 各科成绩（可选）
          </h3>
          <p className="text-sm text-sky-600 mb-4">
            填写各科分数可帮助系统分析您的学科优势，推荐更匹配的专业
          </p>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {/* 必考科目 */}
            <div className="space-y-2">
              <Label htmlFor="chinese" className="text-sky-800">语文</Label>
              <Input
                id="chinese"
                type="number"
                max="150"
                placeholder="0-150"
                value={chinese}
                onChange={(e) => setChinese(e.target.value)}
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="math" className="text-sky-800">数学</Label>
              <Input
                id="math"
                type="number"
                max="150"
                placeholder="0-150"
                value={math}
                onChange={(e) => setMath(e.target.value)}
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="english" className="text-sky-800">英语</Label>
              <Input
                id="english"
                type="number"
                max="150"
                placeholder="0-150"
                value={english}
                onChange={(e) => setEnglish(e.target.value)}
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
            </div>

            {/* 选考科目 */}
            {subjectGroup === "物理" && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="physics" className="text-sky-800">物理</Label>
                  <Input
                    id="physics"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={physics}
                    onChange={(e) => setPhysics(e.target.value)}
                    className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="chemistry" className="text-sky-800">化学</Label>
                  <Input
                    id="chemistry"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={chemistry}
                    onChange={(e) => setChemistry(e.target.value)}
                    className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="biology" className="text-sky-800">生物</Label>
                  <Input
                    id="biology"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={biology}
                    onChange={(e) => setBiology(e.target.value)}
                    className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
                  />
                </div>
              </>
            )}

            {subjectGroup === "历史" && (
              <>
                <div className="space-y-2">
                  <Label htmlFor="history" className="text-sky-800">历史</Label>
                  <Input
                    id="history"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={history}
                    onChange={(e) => setHistory(e.target.value)}
                    className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="politics" className="text-sky-800">政治</Label>
                  <Input
                    id="politics"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={politics}
                    onChange={(e) => setPolitics(e.target.value)}
                    className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="geography" className="text-sky-800">地理</Label>
                  <Input
                    id="geography"
                    type="number"
                    max="100"
                    placeholder="0-100"
                    value={geography}
                    onChange={(e) => setGeography(e.target.value)}
                    className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
                  />
                </div>
              </>
            )}
          </div>
        </Card>

        {/* 志愿偏好卡片 */}
        <Card className="p-6 bg-sky-50/50 border-sky-300">
          <h3 className="text-xl font-semibold mb-4 text-sky-700 flex items-center">
            <span className="mr-2">🎯</span> 志愿偏好
          </h3>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="preferredMajors" className="text-sky-800">
                想学的专业方向
              </Label>
              <Input
                id="preferredMajors"
                placeholder="例如：计算机、人工智能、电子信息"
                value={preferredMajors}
                onChange={(e) => setPreferredMajors(e.target.value)}
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="blacklistMajors" className="text-sky-800">
                不想学的专业（黑名单）
              </Label>
              <Input
                id="blacklistMajors"
                placeholder="例如：土木、化工、生物制药"
                value={blacklistMajors}
                onChange={(e) => setBlacklistMajors(e.target.value)}
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="preferredCities" className="text-sky-800">
                偏好城市/地区
              </Label>
              <Input
                id="preferredCities"
                placeholder="例如：北京、上海、江浙、不排斥中西部"
                value={preferredCities}
                onChange={(e) => setPreferredCities(e.target.value)}
                className="bg-white border-sky-300 text-sky-900 placeholder-sky-400 focus:border-sky-500 focus:ring-sky-500"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="risk" className="text-sky-800">
                风险偏好
              </Label>
              <Select value={riskTolerance} onValueChange={setRiskTolerance}>
                <SelectTrigger className="bg-white border-sky-300 text-sky-900">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-white border-sky-300 text-sky-900">
                  <SelectItem value="conservative">保守型 - 稳妥优先，避免滑档</SelectItem>
                  <SelectItem value="balanced">平衡型 - 冲稳保均衡</SelectItem>
                  <SelectItem value="aggressive">激进型 - 冲刺名校，可承受风险</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </Card>

        {/* 提交按钮 */}
        <Button
          type="submit"
          className="w-full bg-gradient-to-r from-sky-500 via-cyan-500 to-blue-500 hover:from-sky-600 hover:via-cyan-600 hover:to-blue-600 text-white font-bold py-6 text-lg rounded-xl shadow-lg transform transition hover:scale-105"
        >
          <span className="mr-2">🚀</span>
          开始AI智能分析
        </Button>
      </form>

      {/* 功能说明 */}
      <div className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-4 bg-gradient-to-br from-sky-100 to-sky-50 rounded-lg border-2 border-sky-300">
          <h4 className="font-semibold mb-2 text-sky-700">💎 核心算法</h4>
          <ul className="text-sm text-sky-600 space-y-1">
            <li>• 正态分布概率计算</li>
            <li>• 小样本惩罚系数</li>
            <li>• 恐惧指数识别市场错杀</li>
          </ul>
        </div>

        <div className="p-4 bg-gradient-to-br from-cyan-100 to-cyan-50 rounded-lg border-2 border-cyan-300">
          <h4 className="font-semibold mb-2 text-cyan-700">🛡️ 风险管控</h4>
          <ul className="text-sm text-cyan-600 space-y-1">
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
