import React from "react";
import { buildAdmissionsOpportunityDemoCase } from "../lib/admissionsOpportunityDemoCase";
import { CareerChoiceSimulator } from "./CareerChoiceSimulator";
import { JobEvidenceWorkbench } from "./JobEvidenceWorkbench";

const admissionsDemoTextMap: Record<string, string> = {
  "Student A": "学生 A",
  "South China Tech": "华南理工示例校",
  "Computer Science": "计算机科学",
  "Civil Engineering": "土木工程",
  "Materials": "材料类",
  Guangdong: "广东",
  qianwen: "通义千问",
  teacher: "教师方案",
  family: "家庭方案",
  "demo-search-provider": "演示搜索源",
  "demo-gap-search-provider": "演示补证搜索源",
  yes: "是",
  no: "否",
  allowed: "允许",
  blocked: "已阻断",
  required: "需要",
  "not required": "不需要",
  none: "无",
  unknown: "未知",
  authoritative: "权威来源",
  specialized: "专业来源",
  context: "背景来源",
  weak: "弱证据",
  current_cycle: "当前招生周期",
  recent: "近期",
  stale: "已过期",
  undated: "未标注日期",
  completed: "已完成",
  ready: "就绪",
  covered: "已覆盖",
  review: "待复核",
  review_ready: "可复核",
  collecting_evidence: "正在采集证据",
  ready_to_capture: "可开始采集",
  ready_to_search: "可开始检索",
  ready_to_run: "可执行",
  no_gaps: "暂无证据缺口",
  triangulated: "已完成多源交叉验证",
  ready_for_counselor_review: "可进入顾问复核",
  ready_for_family_review: "可给家庭复核",
  ready_for_family_delivery: "可进入家庭沟通",
  ready_for_family_discussion: "可进入家庭讨论",
  ready_for_plan_discussion: "可进入方案讨论",
  ready_for_row_discussion: "可讨论具体志愿行",
  interpretation_ready: "解读包已就绪",
  counselor_review_ready: "顾问复核材料已就绪",
  needs_evidence_research: "需要继续补证",
  supports_hypothesis: "支持假设表述",
  hypothesis_only: "仅作假设",
  under_attention_candidate: "关注度不足候选",
  under_attention_opportunity: "关注度不足机会",
  under_attention_candidate_only: "只能表述为关注度不足候选",
  candidate_for_counselor_review: "顾问复核候选",
  candidate_cleared: "候选已通过门禁",
  can_explain: "可以解释",
  official_diff: "官方计划变化",
  official_change: "官方计划变化",
  rank_delta: "位次变化",
  rank_direction: "位次方向",
  competitor_missed: "外部方案遗漏",
  external_plan_gap: "外部方案缺口",
  low_attention_signal: "关注度不足信号",
  counter_evidence_clearance: "反证检索通过",
  hype_pressure_clearance: "热度压力检索通过",
  source_diversity: "来源多样性",
  evidence_quality: "证据质量",
  family_readiness: "家庭理解准备度",
  parent_understanding: "家长理解",
  regional_preference: "地域偏好",
  risk_guard: "风险边界",
  search_provenance: "检索来源记录",
  rank_calibration: "位次校准",
  external_plan_omission: "外部方案遗漏",
  family_concept: "家庭概念",
  keep_for_audit: "保留审计",
  official_plan_diff: "官方计划变化",
  quota_expansion: "招生名额增加",
  trend_wording: "趋势表述",
  concept_readiness: "概念理解准备度",
  professional_group: "专业组",
  safe_anchor: "保底锚点",
  interest_tradeoff: "兴趣取舍",
  course_content: "课程内容",
  regret_boundary: "后悔边界",
  public_opinion: "公开讨论",
  public_opinion_scan: "公开讨论扫描",
  public_opinion_trend: "公开讨论趋势",
  official_plan: "官方招生计划",
  historical_data: "历史数据",
  family_concept_clarification: "家庭概念澄清",
  external_plan_comparison: "外部方案对比",
  school_rule_verification: "学校规则核验",
  rank_history_calibration: "历史位次校准",
  counter_evidence: "反证检索",
  hype_pressure: "热度压力检索",
  needs_counter_check: "需要反证检查",
  critical: "关键",
  high: "高",
  medium: "中",
  low: "低",
  target: "冲稳候选",
  promote: "上调关注",
  easier: "录取压力可能降低",
  missed: "已发现遗漏",
  understood: "已理解",
  fit: "适配",
  audited_opportunity_candidate: "已审计机会候选",
  plan_change_ledger: "计划变化台账",
  ledger_ready: "台账已就绪",
  "admissions_opportunity_demo_case_v1": "趋势机会演示案例",
  "public_opinion_trend_language_gate_v1": "公开讨论趋势表述门禁",
  "web_evidence_search_run_v1": "网页证据检索记录",
  "evidence_gap_search_rerun_v1": "证据缺口补跑记录",
  "counselor_review_dossier_v1": "顾问复核材料包",
  "counselor_search_provenance_v1": "检索来源记录",
  "counselor_evidence_quality_v1": "证据质量复核",
  "detailed_volunteer_plan_interpretation_v1": "志愿方案详细解读",
  "web_evidence_research_strategy_v1": "网页证据研究策略",
  "family_decision_clarity_roadmap_v1": "家庭决策澄清路线图",
  "hidden_opportunity_audit_v1": "隐性机会复核",
  "plan_change_opportunity_ledger_v1": "招生计划变化机会台账",
  "volunteer_plan_narrative_package_v1": "志愿方案家庭沟通包",
  "family_decision_brief_v1": "家庭决策简报",
  "family_concept_readiness_v1": "家庭概念理解门禁",
};

const admissionsDemoPhraseMap: Array<[string, string]> = [
  [
    "South China Tech Computer Science can be described only as an under-attention candidate.",
    "华南理工示例校计算机科学只能表述为关注度不足的候选机会。",
  ],
  [
    "This demo case is not a final recommendation. It demonstrates the auditable workflow from official diff, public-opinion hypothesis, capture worksheet, evidence intake, and counselor-review package.",
    "这个演示案例不是最终志愿推荐。它展示的是从官方计划变化、公开讨论假设、采集任务表、证据入库到顾问复核材料包的可审计流程。",
  ],
  [
    "This dossier is not a final filing recommendation. It organizes auditable evidence, claim limits, and counselor-review questions.",
    "这份材料不是最终填报推荐。它整理可审计证据、声称边界和顾问复核问题。",
  ],
  ["Trend language gate: hypothesis_only; score 76.", "趋势话术门禁：仅作假设；评分 76。"],
  ["Official plan diff must be attached before opportunity language is used.", "使用机会话术前，必须先附上官方计划变化证据。"],
  ["Student A: evidence-backed family narrative", "学生 A：有证据支撑的家庭沟通叙事"],
  [
    "Student A: evidence-backed plan interpretation ready for family review",
    "学生 A：有证据支撑的志愿方案解读，可进入家庭复核",
  ],
  ["Software Engineering", "软件工程"],
  ["Primary interest direction:", "主要兴趣方向："],
  ["Student fit for this opportunity is fit:", "学生适配度：适配；"],
  ["The changed major matches the student's stated direction.", "计划变化涉及的专业与学生表述方向匹配。"],
  [
    "Interest brief is ready_for_plan_discussion; risk tolerance is balanced. Discovery student fit is fit; rank impact is easier with medium confidence.",
    "兴趣简报可进入方案讨论；风险偏好为平衡。机会发现阶段显示学生方向适配，位次影响可能降低，置信度为中。",
  ],
  ["Concept readiness supports row-level discussion.", "概念理解已支持讨论具体志愿行。"],
  ["Can the family explain that filing is by school major group?", "家庭能否说明志愿填报单位是院校专业组？"],
  ["Family accepts group-level uncertainty.", "家庭接受专业组层面的不确定性。"],
  ["recommendation_action=promote", "处理动作=上调关注"],
  ["risk_guard=medium", "风险边界=中"],
  [
    "hidden_opportunity_audit=can_enter_ledger:candidate_for_counselor_review",
    "隐性机会复核=可进入台账：顾问复核候选",
  ],
  ["do not use as safety anchor", "不能作为保底锚点"],
  ["verify group code before final signoff", "最终签字前复核专业组代码"],
  [
    "Plan change opportunity ledger is an audit object for official enrollment-plan differences.",
    "计划变化机会台账只用于审计官方招生计划差异。",
  ],
  [
    "It cannot claim hidden opportunity without official source, rank-impact estimate, competitor-miss check, recommendation action, and risk guard.",
    "没有官方来源、位次影响估计、外部方案遗漏检查、处理动作和风险边界时，不能声称隐性机会。",
  ],
  [
    "This dossier can be shown as a counselor-review explanation, with final filing still gated by counselor signoff.",
    "这份材料可以作为顾问复核说明展示，但最终填报仍需顾问签字。",
  ],
  [
    "has a possible under-attention hypothesis, but it still needs official plan, rank, and external-plan evidence before use.",
    "存在关注度不足假设，但使用前仍需补齐官方计划、位次和外部方案证据。",
  ],
  [
    "can be described only as an under-attention candidate: public discussion looks quieter or avoidant, but this remains a hypothesis until official, rank, and external-plan evidence agree.",
    "只能表述为关注度不足候选机会：公开讨论热度偏低或有回避倾向，但在官方计划、位次和外部方案证据一致前，仍然只能作为假设。",
  ],
  ["Attach official plan diff before using public opinion signals in opportunity discovery.", "使用公开讨论信号做机会发现前，必须先补充官方招生计划变化证据。"],
  ["Attach rank history and external-plan comparison before discussing hidden opportunity potential.", "讨论隐性机会潜力前，必须先补充历史位次和外部方案对比证据。"],
  ["Attach official plan diff before using trend language.", "使用趋势话术前，必须先补充官方招生计划变化证据。"],
  ["Keep wording as hypothesis_only until counselor review.", "顾问复核前，措辞必须保持为仅作假设。"],
  ["Do not call this a hidden opportunity when counter-evidence, hype, or insufficient data is present.", "存在反证、热度噪声或数据不足时，不能称为隐性机会。"],
  ["Do not say public opinion proves demand, admission probability, score movement, or guaranteed admission.", "不能说公开讨论证明需求、录取概率、分数波动或录取保证。"],
  ["Do not present trend wording without official plan diff, rank calibration, external-plan comparison, and counselor review.", "没有官方计划变化、位次校准、外部方案对比和顾问复核时，不能展示趋势话术。"],
  ["Attach 5 normalized evidence results to evidence intake.", "将 5 条规范化证据补充到证据入库。"],
  ["Keep final recommendation blocked until evidence intake and triangulation pass.", "证据入库和交叉验证通过前，最终推荐必须保持阻断。"],
  ["Counselor review can start with the attached evidence-backed interpretation package.", "可以基于已附的证据化解读包启动顾问复核。"],
  ["Search official plan rows and confirm school code, group code, major code, quota, and subject requirements.", "检索官方招生计划行，并核对学校代码、专业组代码、专业代码、招生名额和选科要求。"],
  ["Search public opinion trend signals and keep them hypothesis_only.", "检索公开讨论趋势信号，并保持仅作假设。"],
  ["Paste excerpts into capture submissions using the worksheet templates.", "按采集任务模板粘贴证据摘录。"],
  ["Run evidence gap follow-up searches when triangulation asks for second independent sources.", "当交叉验证要求第二个独立来源时，执行证据缺口补充检索。"],
  ["Run evidence intake; do not move to counselor review until blocking official, rank, risk, and external-plan evidence pass.", "执行证据入库；官方计划、位次、风险和外部方案证据通过前，不能进入顾问复核。"],
  ["Use the interpretation package to explain professional group, adjustment, safe anchor, and interest tradeoff to the family.", "使用解读包向家庭解释院校专业组、专业调剂、保底锚点和兴趣取舍。"],
  [
    "Professional group: the application unit is the school major group, not a single major. Adjustment: accepting adjustment protects admission chance but may change the final major. Safe anchor: a safe row must be acceptable after admission, not merely easy to enter. Interest tradeoff: this row should match the student's preferred direction and avoid blacklist majors.",
    "院校专业组：填报单位是院校专业组，不是单一专业。专业调剂：接受调剂可以保护录取机会，但最终专业可能变化。保底锚点：保底行必须是录取后也能接受的结果，而不只是容易进入。兴趣取舍：这一行应匹配学生偏好方向，并避开黑名单专业。",
  ],
  ["Can the family explain that filing is by school major group, not by one favorite major?", "家庭能否说明填报单位是院校专业组，而不是一个最喜欢的专业？"],
  ["Can the family name the worst acceptable adjusted major?", "家庭能否说出最差但仍可接受的调剂专业？"],
  ["Can the family define safety by the worst acceptable outcome, not only by entry probability?", "家庭能否用最差可接受结果定义保底，而不是只看进入概率？"],
  ["Can the student describe interest by courses, industry path, city, work style, and regret tolerance?", "学生能否从课程、行业路径、城市、工作方式和后悔容忍度描述兴趣？"],
  ["Professional group: the unit of filing is a school major group, not a single favorite major.", "院校专业组：填报单位是院校专业组，不是单一最喜欢的专业。"],
  ["Adjustment: accepting adjustment protects admission chance, but the final major may change.", "专业调剂：接受调剂可以保护录取机会，但最终专业可能变化。"],
  ["Safe anchor: a safe row is only safe if the worst acceptable outcome is still acceptable.", "保底锚点：只有最差可接受结果仍然可接受时，这一行才算保底。"],
  ["Interest tradeoff: interest means course content, industry path, city, work style, and regret tolerance, not only a hot major label.", "兴趣取舍：兴趣指课程内容、行业路径、城市、工作方式和后悔容忍度，不只是热门专业标签。"],
  ["Would you still accept the group if the final major is not Computer Science?", "如果最终专业不是计算机科学，你仍然接受这个专业组吗？"],
  ["If this group protects admission chance but includes adjustment risk, what is the worst acceptable major?", "如果这个专业组能保护录取机会但存在调剂风险，最差可接受专业是什么？"],
  ["Which matters more for this row: school platform, major certainty, city, tuition, or low regret risk?", "这一行更看重什么：学校平台、专业确定性、城市、学费，还是低后悔风险？"],
  ["Can this row be used as a safe anchor after considering worst-case major, campus, and fees?", "考虑最差专业、校区和费用后，这一行还能作为保底锚点吗？"],
  ["Which tradeoff would make you remove this row even if the admission probability is attractive?", "即使录取概率有吸引力，哪种取舍会让你删除这一行？"],
  ["Do not recommend majors matching blacklist:", "不要推荐命中黑名单的专业："],
  ["This is not a final recommendation.", "这不是最终志愿推荐。"],
  ["Public-opinion evidence cannot prove admission probability or demand.", "公开讨论证据不能证明录取概率或真实需求。"],
  ["Interest signals cannot override blacklist majors, subject requirements, or official rules.", "兴趣信号不能覆盖黑名单专业、选科要求或官方规则。"],
  ["Official plan diff is attached and can be explained.", "官方计划变化证据已附上，可以解释。"],
  ["Rank direction evidence is attached and can be explained.", "位次方向证据已附上，可以解释。"],
  ["External plan comparison supports the omission/gap hypothesis.", "外部方案对比支持遗漏或缺口假设。"],
  ["Low-attention signal exists and wording gate allows under-attention framing.", "存在关注度不足信号，且措辞门禁允许以关注度不足方式表达。"],
  ["Counter-evidence search has been run without rejected or unreturned rows.", "反证检索已执行，未发现被拒绝或未返回的任务行。"],
  ["Hype-pressure search has been run without rejected or unreturned rows.", "热度压力检索已执行，未发现被拒绝或未返回的任务行。"],
  ["Search plan spans 9 intents across 2 provider(s).", "检索计划覆盖 9 类意图，使用 2 个来源。"],
  ["Family concept readiness allows row-level discussion.", "家庭概念理解已允许进入志愿行讨论。"],
  ["Gate reasons", "门禁原因"],
  ["Audit trail", "审计轨迹"],
  ["Official quota expansion evidence is attached for", "官方扩招证据已附上："],
  ["Rank impact can be discussed directionally as easier, with medium confidence and attached rank history.", "位次影响可以按录取压力可能降低来方向性讨论，置信度为中，并已附历史位次。"],
  ["School rule and adjustment risk guard evidence is attached for counselor review.", "学校规则和调剂风险边界证据已附上，可供顾问复核。"],
  ["External plans appear to omit or underweight the official change, based on attached comparison evidence.", "基于已附对比证据，外部方案似乎遗漏或低估了官方计划变化。"],
  ["Public-opinion wording may say under-attention candidate only as hypothesis_only after official, rank, external-plan, and counter-evidence review.", "公开讨论措辞只能在官方计划、位次、外部方案和反证复核后，以仅作假设方式称为关注度不足候选机会。"],
  ["Concept readiness supports row-level discussion; use the interest axes before final counselor signoff.", "概念理解支持志愿行讨论；最终顾问签字前，需要使用兴趣判断轴再核对。"],
  ["Do not claim admission guarantee.", "不要声称录取保证。"],
  ["Do not claim final recommendation.", "不要声称最终推荐。"],
  ["Do not claim public opinion proves demand.", "不要声称公开讨论证明需求。"],
  ["This is not an admission guarantee.", "这不是录取保证。"],
  ["Rank history can support direction and calibration, but it cannot replace the current-year official admission result.", "历史位次可以支持方向判断和校准，但不能替代当年官方录取结果。"],
  ["Interest fit cannot override blacklist majors, subject requirements, physical-exam restrictions, tuition, campus, or adjustment rules.", "兴趣适配不能覆盖黑名单专业、选科要求、体检限制、学费、校区或调剂规则。"],
  ["Public-opinion trend language requires low-attention evidence, counter-evidence search, hype-pressure search, and source diversity; it remains hypothesis_only.", "公开讨论趋势话术需要关注度不足证据、反证检索、热度压力检索和来源多样性；它仍然只能作为假设。"],
  ["Final recommendation remains forbidden until counselor signoff.", "顾问签字前，最终推荐仍然禁止输出。"],
  ["is a counselor-review gate only.", "只是顾问复核门禁。"],
  ["1 official plan-change opportunity object(s), top audit score 100.", "1 个官方计划变化机会对象，最高审计分 100。"],
  ["Official change suggests a candidate opportunity; public opinion remains a hypothesis, not demand proof.", "官方计划变化提示存在候选机会；公开讨论仍是假设，不是需求证明。"],
  ["Rank direction is easier with medium confidence.", "位次方向显示录取压力可能降低，置信度为中。"],
  ["Use under_attention_candidate_only wording only; this is not a final recommendation.", "只能使用关注度不足候选措辞；这不是最终推荐。"],
  ["Keep public opinion language hypothesis_only and preserve counselor signoff.", "公开讨论话术必须保持仅作假设，并保留顾问签字。"],
  ["Guangdong Education Exam Authority", "广东省教育考试院"],
  ["enrollment plan", "招生计划"],
  ["Quota expands from 20 to 36 seats; demand calibration is still required.", "招生名额从 20 增加到 36 个；真实需求校准仍然需要补证。"],
  ["The official plan change is attached and can be used as the factual starting point.", "官方计划变化已附上，可以作为事实起点。"],
  ["10561 major group 201 Computer Science quota 36; subject requirements physics and chemistry.", "10561 专业组 201 计算机科学招生名额 36；选科要求为物理和化学。"],
  ["Recheck school code, group code, major code, quota, subject requirements, and official URL before filing.", "填报前重新核对学校代码、专业组代码、专业代码、招生名额、选科要求和官方链接。"],
  ["Rank impact can be discussed directionally with current evidence, but it is not a score guarantee.", "当前证据支持方向性讨论位次影响，但这不是分数保证。"],
  ["2025 rank 42000; 2024 rank 43800 for the same school group with quota context retained.", "同一院校专业组 2025 年位次 42000、2024 年位次 43800，并保留招生名额背景。"],
  ["The same school group has 2025 rank 42000 and 2024 rank 43800 with quota context.", "同一院校专业组对应 2025 年位次 42000 和 2024 年位次 43800，并带有招生名额背景。"],
  ["Compare at least two historical-data sources and keep quota context attached.", "至少对比两个历史数据来源，并保留招生名额背景。"],
  ["evidence-backed", "有证据支撑的"],
  ["Hidden opportunity audit", "隐性机会复核"],
  ["Plan change ledger handoff", "计划变化台账交接"],
  ["Evidence-backed plan narrative", "有证据支撑的志愿方案叙事"],
  ["Detailed interpretation", "详细解读"],
  ["Web research strategy", "网页证据研究策略"],
  ["Family clarity roadmap", "家庭决策澄清路线图"],
  ["Counselor review dossier", "顾问复核材料包"],
  ["Search provenance", "检索来源记录"],
  ["Evidence quality", "证据质量"],
  ["Review gate", "复核门禁"],
  ["Hidden opportunity gate", "隐性机会门禁"],
  ["Family decision path", "家庭决策路径"],
  ["Plan position", "方案位置"],
  ["Priority queries", "优先检索问题"],
  ["Interest axes", "兴趣判断轴"],
  ["What we can say", "可以对家庭说明"],
  ["What we cannot say", "不能对家庭声称"],
  ["Counselor checklist", "顾问复核清单"],
  ["Family questions", "家庭讨论问题"],
  ["Evidence trail", "证据链"],
  ["Quality blockers", "证据质量阻断项"],
  ["Evidence basis", "证据依据"],
  ["Sources", "来源"],
  ["Counter checks", "反证检查"],
  ["Required questions", "必须追问"],
  ["Hard stops", "硬边界"],
  ["Not recommendation reasons", "不能作为最终推荐的原因"],
  ["Next actions", "下一步动作"],
  ["Contradiction tests", "反向验证"],
  ["Minimum evidence rules", "最低证据规则"],
  ["Operator brief", "操作员提示"],
  ["Alignment questions", "亲子对齐问题"],
  ["Blocked reasons", "阻断原因"],
  ["Blocked claims", "被阻断的声称"],
  ["Positive signals", "正向信号"],
  ["Negative signals", "负向信号"],
  ["Before family wording", "进入家庭话术前必须补齐"],
  ["Forbidden claims", "禁止声称"],
  ["Search follow-ups", "补充检索"],
  ["Concept prompts", "概念追问"],
  ["Interest prompts", "兴趣追问"],
  ["Risk guard", "风险边界"],
  ["Conversation flow", "沟通顺序"],
  ["score:", "评分："],
  ["status:", "状态："],
  ["gate:", "门禁："],
  ["rows:", "志愿行："],
  ["family:", "家庭沟通："],
  ["hypothesis-only:", "仅作假设："],
  ["can enter ledger:", "可进入机会台账："],
  ["hidden label:", "隐性机会标签："],
  ["must stay hypothesis-only:", "必须保持假设表述："],
  ["counselor signoff:", "顾问签字："],
  ["rank delta:", "位次影响："],
  ["rejects as proof:", "不能作为证明："],
  ["runs:", "检索轮次："],
  ["providers:", "来源提供方："],
  ["accepted:", "采纳："],
  ["rejected:", "拒绝："],
  ["unreturned:", "未返回："],
  ["authoritative:", "权威来源："],
  ["current cycle:", "当前周期："],
  ["stale:", "过期："],
  ["conflicts:", "冲突："],
  ["accepted items", "条已采纳证据"],
  ["evidence", "条证据"],
  ["gaps:", "缺口："],
  ["triangulation:", "交叉验证："],
  ["public opinion:", "公开讨论证据角色："],
  ["no provider", "未记录来源"],
  ["not supplied", "未提供"],
  ["Unknown school", "未知学校"],
  ["Hidden opportunity", "隐性机会"],
  ["hypothesis-only", "仅作假设"],
  ["final recommendation", "最终推荐"],
  ["admission guarantee", "录取保证"],
  ["admission probability", "录取概率"],
  ["counselor review", "顾问复核"],
  ["counselor signoff", "顾问签字"],
  ["family-review explanation", "家庭复核说明"],
  ["under-attention candidate", "关注度不足候选机会"],
  ["public opinion proves demand", "公开讨论证明需求"],
  ["public-opinion", "公开讨论"],
  ["quota_expansion", "招生名额增加"],
  ["school major group", "院校专业组"],
  ["single major", "单一专业"],
  ["adjustment", "专业调剂"],
  ["safe anchor", "保底锚点"],
  ["interest tradeoff", "兴趣取舍"],
  ["Materials", "材料类"],
  ["Attach official plan diff before using 公开讨论 signals in opportunity discovery.", "使用公开讨论信号做机会发现前，必须先补充官方招生计划变化证据。"],
  ["Keep wording as 仅作假设 until 顾问复核.", "顾问复核前，措辞必须保持为仅作假设。"],
  ["Search 公开讨论 trend signals and keep them 仅作假设.", "检索公开讨论趋势信号，并保持仅作假设。"],
  ["Current hypothesis:", "当前假设："],
  ["证据质量 is 待复核-就绪.", "证据质量已达到待复核就绪状态。"],
  ["Review gate", "复核门禁"],
  ["Public-opinion signals remain 仅作假设 even when the row enters the opportunity ledger.", "即使该志愿行进入机会台账，公开讨论信号仍然只能作为假设。"],
  ["Professional group, 专业调剂, 保底锚点, and 兴趣取舍 concepts have been explained before row-level discussion.", "进入志愿行讨论前，已解释院校专业组、专业调剂、保底锚点和兴趣取舍。"],
  ["Public-opinion wording may say 关注度不足候选机会 only as 仅作假设 after official, rank, external-plan, and counter-条证据 待复核.", "公开讨论措辞只能在官方计划、位次、外部方案和反证复核后，以仅作假设方式称为关注度不足候选机会。"],
  ["Public-opinion wording may say 关注度不足候选机会 only as 仅作假设 after 官方, rank, external-plan, and counter-条证据 待复核.", "公开讨论措辞只能在官方计划、位次、外部方案和反证复核后，以仅作假设方式称为关注度不足候选机会。"],
  ["Public-opinion 条证据 cannot prove demand, 录取概率, or score movement.", "公开讨论证据不能证明需求、录取概率或分数波动。"],
  ["Public-opinion trend language requires low-attention 条证据, counter-条证据 search, hype-pressure search, and source diversity; it remains 仅作假设.", "公开讨论趋势话术需要关注度不足证据、反证检索、热度压力检索和来源多样性；它仍然只能作为假设。"],
  ["Public-opinion 条证据 must stay 仅作假设; the audit cannot prove 录取概率, 最终推荐, or demand.", "公开讨论证据必须保持仅作假设；审计不能证明录取概率、最终推荐或真实需求。"],
  ["有证据支撑的 family narrative", "有证据支撑的家庭沟通叙事"],
  ["Keep 公开讨论 language 仅作假设 and preserve 顾问签字.", "公开讨论话术必须保持仅作假设，并保留顾问签字。"],
  ["招生名额增加 is in the plan-change ledger with audit score 100.", "招生名额增加已进入计划变化台账，审计分 100。"],
  ["for 华南理工示例校", "对应华南理工示例校"],
  ["Adjustment, school rules, and worst-case outcomes must be checked before treating this row as safe.", "将这一行视为保底前，必须先核对调剂、学校规则和最差可接受结果。"],
  ["Adjustment stays inside eligible majors in the same group; physical-exam restrictions must be checked.", "调剂范围仍在同一专业组可录专业内；体检限制必须单独核验。"],
  ["Confirm worst-case adjusted major, campus, fee, city, physical-exam, and transfer constraints.", "确认最差调剂专业、校区、费用、城市、体检和转专业限制。"],
  ["External plans appear to miss or underweight the official change, subject to 顾问复核.", "外部方案似乎遗漏或低估了官方计划变化，仍需顾问复核。"],
  ["External plans keep the 2025 quota assumption and omit the 2026 expansion.", "外部方案仍沿用 2025 年招生名额假设，遗漏 2026 年扩招。"],
  ["A second external plan still keeps the 2025 quota assumption and omits the 2026 expansion.", "第二份外部方案仍沿用 2025 年招生名额假设，遗漏 2026 年扩招。"],
  ["Look for external plans that already incorporated the 2026 change before calling it underweighted.", "在判断外部方案低估前，先检索是否已有方案纳入 2026 年变化。"],
  ["The family has concept-clarification 条证据 attached before row-level discussion.", "进入志愿行讨论前，家庭概念澄清证据已附上。"],
  ["Professional group, 专业调剂, 保底锚点, and 兴趣取舍 explained before final rows.", "最终志愿行前，已解释院校专业组、专业调剂、保底锚点和兴趣取舍。"],
  ["counter-条证据: What 条证据 would disprove the low-attention hypothesis or show broad recognition?", "反证检索：什么证据可以推翻关注度不足假设，或显示它已被广泛识别？"],
  ["rank-history-calibration: Does rank history support only a directional interpretation with quota context retained?", "历史位次校准：历史位次是否只支持方向性解释，并保留招生名额背景？"],
  ["hype-pressure: Is the topic crowded or hyped enough to block hidden-opportunity wording?", "热度压力：该方向是否已经足够拥挤或过热，以至于应阻断隐性机会措辞？"],
  ["Search for official-row mismatch before discussing any opportunity.", "讨论任何机会前，先检索官方招生计划行是否存在不匹配。"],
  ["Search for rank-history conflict before using directional rank impact.", "使用方向性位次影响前，先检索历史位次冲突。"],
  ["Search for external plans that already include the 2026 change before claiming omission.", "声称遗漏前，先检索是否已有外部方案纳入 2026 年变化。"],
  ["Search for broad recognition, hype pressure, or mainstream attention before using under-attention wording.", "使用关注度不足措辞前，先检索是否已被广泛识别、过热或主流关注。"],
  ["Does dated public discussion show low attention or avoidance around this school and major?", "有日期的公开讨论是否显示该校该专业关注度偏低或存在回避？"],
  ["What 条证据 would disprove the low-attention hypothesis or show broad recognition?", "什么证据可以推翻关注度不足假设，或显示它已被广泛识别？"],
  ["Is the topic crowded or hyped enough to block hidden-opportunity wording?", "该方向是否已经足够拥挤或过热，以至于应阻断隐性机会措辞？"],
  ["Do family discussions show regional preference, distance fear, or 专业调剂 avoidance?", "家庭讨论是否显示地域偏好、距离焦虑或调剂回避？"],
  ["Can the same trend be checked across different source kinds instead of one anecdote?", "同一趋势能否跨不同来源类型核验，而不是只依赖单一案例？"],
  ["official plan", "官方计划"],
  ["Which courses would the student willingly study for four years even when they are difficult?", "哪些课程即使很难，学生也愿意持续学习四年？"],
  ["Which industry path sounds acceptable after graduation, and which path is only attractive because it sounds popular?", "哪些毕业后的行业路径真正可接受，哪些只是因为听起来热门？"],
  ["Which city, distance, campus, or living-cost tradeoff would change the choice even if the major looks attractive?", "即使专业看起来有吸引力，哪种城市、距离、校区或生活成本取舍会改变选择？"],
  ["What work style does the student prefer: building, research, operations, communication, service, management, or structured execution?", "学生更偏好的工作方式是什么：建造、研究、运营、沟通、服务、管理，还是结构化执行？"],
  ["Which outcome would make the family regret accepting this row even if admission succeeds?", "即使录取成功，哪种结果会让家庭后悔接受这一行？"],
  ["Start with the official plan change, then show what is verified and what is still bounded.", "先从官方计划变化讲起，再说明哪些已核验、哪些仍有边界。"],
  ["Explain why 公开讨论 条证据 stays 仅作假设 before discussing opportunity wording.", "讨论机会措辞前，先解释为什么公开讨论证据仍只能作为假设。"],
  ["Use the interest axes to test whether the student wants the course content, industry path, city, work style, and regret boundary.", "用兴趣判断轴检验学生是否真正接受课程内容、行业路径、城市、工作方式和后悔边界。"],
  ["Use as a 家庭复核说明 only after 顾问签字; keep 公开讨论 wording 仅作假设.", "仅在顾问签字后作为家庭复核说明使用；公开讨论措辞保持仅作假设。"],
  ["This dossier is not a final filing recommendation. It organizes auditable 条证据, claim limits, and counselor-待复核 questions.", "这份材料不是最终填报推荐。它整理可审计证据、声称边界和顾问复核问题。"],
  ["Use this as a 家庭复核说明 only after 顾问签字.", "仅在顾问签字后作为家庭复核说明使用。"],
  ["Keep 公开讨论 wording 仅作假设 and preserve counter-条证据 checks.", "公开讨论措辞保持仅作假设，并保留反证检查。"],
  ["Verify official plan row before interpreting demand, rank movement, or external-plan omission.", "解释需求、位次变化或外部方案遗漏前，先核验官方招生计划行。"],
  ["Run counter-条证据 and hype-pressure searches before using trend wording.", "使用趋势话术前，先执行反证和热度压力检索。"],
  ["Keep 公开讨论 条证据 as 仅作假设; never use it as 录取概率 or 最终推荐 proof.", "公开讨论证据只能作为假设；绝不能用作录取概率或最终推荐证明。"],
  ["Volunteer plan narrative package organizes 条证据, search follow-ups, and family discussion prompts. It does not make final filing recommendations, estimate 录取概率, or convert 公开讨论 hypotheses into proof.", "志愿方案叙事包整理证据、补充检索和家庭讨论问题；它不生成最终填报推荐，不估算录取概率，也不把公开讨论假设转成证明。"],
  ["Official diff supports that the plan row changed; it does not by itself prove 录取概率.", "官方计划变化只能证明招生计划行发生变化，不能单独证明录取概率。"],
  ["Rank 条证据 supports directional interpretation only and must not replace current-year admission results.", "位次证据只支持方向性解释，不能替代当年录取结果。"],
  ["风险边界 条证据 limits unsafe claims; it does not make the row acceptable for every family.", "风险边界证据用于限制不安全声称，并不代表这一行适合每个家庭。"],
  ["Evidence quality is review-ready.", "证据质量已达到待复核就绪状态。"],
  ["证据质量 is review-ready.", "证据质量已达到待复核就绪状态。"],
  ["Public-opinion wording may say 关注度不足候选机会 only as 仅作假设 after official, rank, external-plan, and counter-条证据 待复核.", "公开讨论措辞只能在官方计划、位次、外部方案和反证复核后，以仅作假设方式称为关注度不足候选机会。"],
  ["Start with the 官方计划 change, then show what is verified and what is still bounded.", "先从官方计划变化讲起，再说明哪些已核验、哪些仍有边界。"],
  ["This dossier is not a final filing recommendation. It organizes auditable 条证据, claim limits, and counselor-待复核 questions.", "这份材料不是最终填报推荐。它整理可审计证据、声称边界和顾问复核问题。"],
  ["Verify 官方计划 row before interpreting demand, rank movement, or external-plan omission.", "解释需求、位次变化或外部方案遗漏前，先核验官方招生计划行。"],
  ["External omission can support a candidate opportunity thesis, not a guarantee that others will miss it.", "外部方案遗漏只能支持候选机会论点，不能保证其他人一定会遗漏。"],
  ["Family concept checklist", "家庭概念检查清单"],
  ["Concept 条证据 supports communication readiness only.", "概念证据只支持沟通准备度。"],
  ["Trend language 门禁：仅作假设; score 76.", "趋势话术门禁：仅作假设；评分 76。"],
  ["Public-opinion 条证据 can frame a low-attention hypothesis only. It cannot prove demand, score movement, 录取概率, or 最终推荐 quality.", "公开讨论证据只能形成关注度不足假设，不能证明需求、分数波动、录取概率或最终推荐质量。"],
  ["The search record shows what was checked, what was accepted, and what was rejected or missing before any family-facing claim is made.", "检索记录展示在对家庭表达前，哪些内容被检查、采纳、拒绝或仍缺失。"],
  ["2 search runs across 演示搜索源, 演示补证搜索源.", "已通过演示搜索源和演示补证搜索源完成 2 轮检索。"],
  ["7 accepted rows, 0 rejected rows, 0 unreturned rows.", "7 条采纳记录，0 条拒绝记录，0 条未返回记录。"],
  ["检索来源记录 is provider provenance only. It shows what was searched and returned, but claim support still depends on 条证据 intake and triangulation.", "检索来源记录只说明来源过程；它展示检索和返回情况，但声称是否成立仍取决于证据入库和交叉验证。"],
  ["Family accepts group-level uncertainty before row-level discussion.", "进入志愿行讨论前，家庭已接受专业组层面的不确定性。"],
  ["Family accepts at least one worst-case adjusted major.", "家庭至少接受一个最差调剂专业。"],
  ["Family checks worst-case major, campus, fee, and city.", "家庭已核对最差专业、校区、费用和城市。"],
  ["Concept readiness is a communication gate for family discussion. It does not prove 录取概率, safety, or 最终推荐 readiness.", "概念理解只是家庭讨论的沟通门禁，不能证明录取概率、安全性或最终推荐就绪。"],
  ["Verify official school code, group code, major code, quota, subject requirements, and source URL.", "核验官方学校代码、专业组代码、专业代码、招生名额、选科要求和来源链接。"],
  ["Compare at least two independent rank-history sources and keep quota context attached.", "至少对比两个独立历史位次来源，并保留招生名额背景。"],
  ["Run low-attention, counter-条证据, hype-pressure, regional-preference, and source-diversity searches; keep all trend language 仅作假设.", "执行关注度不足、反证、热度压力、地域偏好和来源多样性检索；所有趋势话术保持仅作假设。"],
  ["Search whether external plans already incorporated the 2026 official change before calling it omitted.", "声称外部方案遗漏前，先检索其是否已纳入 2026 年官方变化。"],
  ["Confirm the family can explain professional group, 专业调剂, 保底锚点, and 兴趣取舍.", "确认家庭能解释院校专业组、专业调剂、保底锚点和兴趣取舍。"],
  ["If broad recognition appears, block low-attention or hidden-opportunity wording and keep the claim as 仅作假设.", "如果出现广泛识别，应阻断关注度不足或隐性机会措辞，并保持仅作假设。"],
  ["Does rank history support only a directional interpretation with quota context retained?", "历史位次是否只支持方向性解释，并保留招生名额背景？"],
  ["If rank sources conflict, downgrade rank impact to needs 待复核.", "如果位次来源冲突，将位次影响降级为需要复核。"],
  ["Public-opinion wording may say 关注度不足候选机会 only as 仅作假设 after official, rank, external-plan, and counter-条证据 待复核.", "公开讨论措辞只能在官方计划、位次、外部方案和反证复核后，以仅作假设方式称为关注度不足候选机会。"],
  ["for 华南理工示例校 201 计算机科学.", "对应华南理工示例校 201 计算机科学。"],
  ["for 华南理工示例校", "对应华南理工示例校"],
  ["counter_条证据:", "反证检索："],
  ["Forbidden wording test:", "禁用话术测试："],
  ["Guangdong official 2026 招生计划 (official)", "广东官方 2026 招生计划（官方）"],
  ["Guangdong historical admission rank table", "广东历史录取位次表"],
  ["CHSI rank history second source", "学信网历史位次第二来源"],
  ["admission charter", "招生章程"],
  ["Qianwen and teacher plan comparison", "通义千问与教师方案对比"],
  ["Teacher plan comparison second source", "教师方案对比第二来源"],
  ["competitor_plan", "外部方案"],
  ["official", "官方"],
];

export function formatAdmissionsDemoText(value: unknown): string {
  if (value === null || value === undefined) return "";
  let text = String(value);
  const exact = admissionsDemoTextMap[text];
  if (exact) return exact;
  for (const [from, to] of admissionsDemoPhraseMap) {
    text = text.split(from).join(to);
  }
  for (const [from, to] of Object.entries(admissionsDemoTextMap)) {
    if (shouldReplaceAsToken(from)) {
      text = replaceAsciiToken(text, from, to);
    }
  }
  return text.replace(/：\s+/g, "：").replace(/\s+；/g, "；");
}

function shouldReplaceAsToken(token: string): boolean {
  return (
    token.includes("_") ||
    token.includes("-") ||
    token.includes(" ") ||
    token.includes("/") ||
    ["yes", "no", "allowed", "blocked", "required", "ready", "completed", "review", "none", "unknown"].includes(token)
  );
}

function replaceAsciiToken(text: string, token: string, replacement: string): string {
  const escaped = token.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const pattern = new RegExp(`(^|[^A-Za-z])${escaped}(?=$|[^A-Za-z])`, "g");
  return text.replace(pattern, `$1${replacement}`);
}

export function AdmissionsOpportunityDemoCasePanel() {
  const demo = buildAdmissionsOpportunityDemoCase();
  const partialCoverage = demo.partialWorkspace.coverageSummary;
  const readyCoverage = demo.readyWorkspace.coverageSummary;
  const decisionBrief =
    demo.gapSearchRerun.refreshedWorkspace.completion?.interpretationPackage?.opportunityCards[0]?.familyDecisionBrief ??
    demo.readyWorkspace.completion.interpretationPackage?.opportunityCards[0]?.familyDecisionBrief;
  const publicOpinionGuards = demo.workflow.discoveryLedger.insights
    .map((insight) => ({
      id: insight.id,
      opportunityKind: insight.opportunityKind,
      guard: insight.publicOpinionGuard,
    }))
    .filter((item) => item.guard);
  const trendLanguageGate = demo.workflow.trendAnalysis?.trendLanguageGate;
  const demoCareerProfile = {
    preferred_majors: ["计算机科学", "软件工程"],
    blacklist_majors: ["土木工程", "材料"],
    riasec_top_codes: ["I", "R"],
    career_values: ["growth"],
    risk_tolerance: "balanced",
  };
  const demoCareerRows = [
    {
      school_name: "South China Tech",
      major_group_code: "201",
      major_list: ["计算机科学", "软件工程", "人工智能"],
      suggested_major_choices: [{ major_name: "计算机科学" }, { major_name: "软件工程" }],
    },
  ];

  return (
    <section className="space-y-5" data-protocol={demo.protocol}>
      <header className="border border-[#C8D8EA] bg-[#EAF3FF] p-5">
        <p className="font-mono text-xs font-semibold uppercase tracking-[0.18em] text-[#C14E2A]">
          证据工作台 / 趋势机会研究
        </p>
        <div className="mt-4 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <div>
            <h1 className="text-3xl font-semibold leading-tight text-[#102033]">趋势机会研究流</h1>
            <p className="mt-3 max-w-4xl text-sm leading-6 text-[#35506B]">
              从招生计划变化、公开舆情、网页证据到顾问复核，逐层判断一个“趋势机会”能不能进入家庭表达。
              这里的核心不是生成一段漂亮话，而是让每个趋势判断都有证据账本和反证要求。
            </p>
          </div>
          <div className="grid grid-cols-2 border border-[#C8D8EA] bg-[#F8FBFF] text-sm">
            <div className="border-b border-r border-[#C8D8EA] p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">学生</span>
              <b>{formatAdmissionsDemoText(demo.studentName)}</b>
            </div>
            <div className="border-b border-[#C8D8EA] p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">证据任务</span>
              <b>{readyCoverage.completedBlockingTasks} / {readyCoverage.blockingTasks}</b>
            </div>
            <div className="border-r border-[#C8D8EA] p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">趋势门禁</span>
              <b>{formatAdmissionsDemoText(trendLanguageGate?.status ?? "review")}</b>
            </div>
            <div className="p-3">
              <span className="block font-mono text-[11px] uppercase text-[#64748B]">边界</span>
              <b>顾问复核签字</b>
            </div>
          </div>
        </div>
      </header>

      <CareerChoiceSimulator profile={demoCareerProfile} rows={demoCareerRows} />
      <JobEvidenceWorkbench />

      <div className="workbench-grid grid grid-cols-1 gap-5 xl:grid-cols-[280px_minmax(0,1fr)_320px]">
        <aside className="workbench-rail border border-[#C8D8EA] bg-white p-4">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-[#0F766E]">案例输入</p>
          <h2 className="mt-3 text-xl font-semibold text-[#102033]">从“可能有机会”到“能不能说”</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-[#35506B]">
            <li>计划变化先作为信号，不直接写成确定机会。</li>
            <li>公众号和公开讨论只能做舆情线索，必须再找权威或多源证据。</li>
            <li>家庭表达前要经过趋势措辞门禁和顾问复核。</li>
          </ul>
        </aside>

        <main className="workbench-main min-w-0">
      <div className="border border-[#C8D8EA] bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <h3 className="text-xl font-bold text-gray-900">趋势机会研究演示案例</h3>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-gray-600">
              从官方招生计划差异、舆情假设、证据采集到顾问复核，完整展示一条趋势机会如何进入家庭可读解释。
            </p>
          </div>
          <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-2 text-right">
            <div className="text-xs font-semibold uppercase text-gray-500">学生</div>
            <div className="text-lg font-bold text-gray-900">{formatAdmissionsDemoText(demo.studentName)}</div>
          </div>
        </div>

        <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-4">
          <Metric label="初始状态" value={demo.partialWorkspace.status} />
          <Metric label="初始阻塞项" value={`${partialCoverage.completedBlockingTasks} / ${partialCoverage.blockingTasks}`} />
          <Metric label="复核状态" value={demo.readyWorkspace.status} />
          <Metric label="复核阻塞项" value={`${readyCoverage.completedBlockingTasks} / ${readyCoverage.blockingTasks}`} />
        </div>

        <div className="mt-5 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <PanelBlock title="舆情线索门禁">
            <div className="space-y-2">
              {publicOpinionGuards.map(({ id, opportunityKind, guard }) => (
                <div key={id} className="rounded-md border border-cyan-200 bg-cyan-50 px-3 py-2 text-sm text-cyan-950">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold">{formatAdmissionsDemoText(guard.status)}</span>
                    <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">{formatAdmissionsDemoText(guard.opportunitySignal)}</span>
                    <span className="text-xs text-cyan-800">置信度 {formatAdmissionsDemoText(guard.confidence)}</span>
                  </div>
                  <div className="mt-1 text-xs leading-5">{formatAdmissionsDemoText(opportunityKind)}: {formatAdmissionsDemoText(guard.summary)}</div>
                  <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
                    {guard.nextActions.map((action) => (
                      <li key={action}>{formatAdmissionsDemoText(action)}</li>
                    ))}
                  </ul>
                </div>
              ))}
              {trendLanguageGate && (
                <div className="rounded-md border border-teal-200 bg-teal-50 px-3 py-2 text-sm text-teal-950">
                  <div className="font-semibold">趋势措辞门禁</div>
                  <div className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                    <span>{formatAdmissionsDemoText(trendLanguageGate.protocol)}</span>
                    <span className="rounded bg-white px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(trendLanguageGate.status)}</span>
                    <span>评分：{trendLanguageGate.score}</span>
                    <span>隐藏机会标签：{trendLanguageGate.canUseHiddenOpportunityLabel ? "允许" : "阻塞"}</span>
                  </div>
                  <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(trendLanguageGate.familySafeWording)}</p>
                  <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                    <MiniList title="必需证据" items={trendLanguageGate.requiredEvidence} />
                    <MiniList title="禁用措辞" items={trendLanguageGate.forbiddenWording} />
                  </div>
                </div>
              )}
            </div>
          </PanelBlock>

          <PanelBlock title="采集任务表">
            <div className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-950">
              <div className="font-semibold">{formatAdmissionsDemoText(demo.captureWorksheet.status)}</div>
              <div className="mt-1 text-xs leading-5">
                待处理任务：{demo.captureWorksheet.pendingRows.map((row) => formatAdmissionsDemoText(row.taskType)).join("、")}
              </div>
            </div>
          </PanelBlock>

          <PanelBlock title="搜索执行记录">
            <div className="rounded-md border border-blue-200 bg-blue-50 px-3 py-2 text-sm text-blue-950">
              <div className="font-semibold">{formatAdmissionsDemoText(demo.operatorSearchRun.protocol)}</div>
              <div className="mt-1 text-xs leading-5">
                {formatAdmissionsDemoText(demo.operatorSearchRun.status)}；来源响应：{demo.operatorSearchRun.providerResponseCount}；
                采纳：{demo.operatorSearchRun.acceptedEvidenceResults.length}；
                拒绝：{demo.operatorSearchRun.rejectedAdapterResults.length + demo.operatorSearchRun.rejectedCaptureSubmissions.length}；
                未返回：{demo.operatorSearchRun.unreturnedTaskIds.length}
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
                {demo.operatorSearchRun.nextActions.map((action) => (
                  <li key={action}>{formatAdmissionsDemoText(action)}</li>
                ))}
              </ul>
            </div>
          </PanelBlock>

          <PanelBlock title="缺口补采复跑">
            <div className="rounded-md border border-violet-200 bg-violet-50 px-3 py-2 text-sm text-violet-950">
              <div className="font-semibold">{formatAdmissionsDemoText(demo.gapSearchRerun.protocol)}</div>
              <div className="mt-1 text-xs leading-5">
                {formatAdmissionsDemoText(demo.gapSearchRerun.searchRun.status)};
                采纳补充证据：{demo.gapSearchRerun.searchRun.acceptedEvidenceResults.length}；
                合并证据：{demo.gapSearchRerun.mergedEvidenceResults.length}；
                刷新状态：{formatAdmissionsDemoText(demo.gapSearchRerun.refreshedWorkspace.status)}；
                缺口状态：{formatAdmissionsDemoText(demo.gapSearchRerun.refreshedWorkspace.evidenceGapSearchPlan.status)}
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs leading-5">
                {demo.gapSearchRerun.nextActions.map((action) => (
                  <li key={action}>{formatAdmissionsDemoText(action)}</li>
                ))}
              </ul>
              <div className="mt-2 text-xs leading-5 text-violet-800">
                已合并 {demo.gapSearchRerun.mergedEvidenceResults.length} 条证据结果
              </div>
            </div>
          </PanelBlock>

          <PanelBlock title="人工采集归一化">
            <div className="rounded-md border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-950">
              <div className="font-semibold">{demo.operatorCaptureNormalization.evidenceResults.length} 条归一化证据结果</div>
              <div className="mt-1 text-xs leading-5">
                被拒绝提交：{demo.operatorCaptureNormalization.rejectedSubmissions.length}
              </div>
            </div>
          </PanelBlock>
        </div>

        <PanelBlock title="操作员执行手册">
          <ol className="space-y-2 text-sm leading-6 text-gray-700">
            {demo.operatorRunbook.map((step) => (
              <li key={formatAdmissionsDemoText(step)} className="rounded-md bg-gray-50 px-3 py-2">
                {formatAdmissionsDemoText(step)}
              </li>
            ))}
          </ol>
        </PanelBlock>

        <PanelBlock title="家庭解释预览">
          <p className="text-sm leading-6 text-gray-700">{formatAdmissionsDemoText(demo.familyExplanationPreview)}</p>
        </PanelBlock>

        {decisionBrief && (
          <PanelBlock title="决策简报">
            <div className="rounded-md border border-slate-200 bg-slate-50 px-3 py-3 text-sm text-slate-900">
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-semibold">{formatAdmissionsDemoText(decisionBrief.protocol)}</span>
                <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">{formatAdmissionsDemoText(decisionBrief.status)}</span>
              </div>
              <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(decisionBrief.interestFitSummary)}</p>
              <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(decisionBrief.riskPosture)}</p>
              <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
                <div className="font-semibold text-slate-900">概念理解准备度</div>
                <div className="mt-1">
                  {formatAdmissionsDemoText(decisionBrief.conceptReadiness.protocol)}；状态：{formatAdmissionsDemoText(decisionBrief.conceptReadiness.status)}
                </div>
                <p className="mt-1">{formatAdmissionsDemoText(decisionBrief.conceptReadiness.nextAction)}</p>
                <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                  {decisionBrief.conceptReadiness.checkpoints.map((checkpoint) => (
                    <div key={formatAdmissionsDemoText(checkpoint.concept)} className="rounded bg-slate-50 px-2 py-1">
                      <span className="font-semibold">{formatAdmissionsDemoText(checkpoint.concept)}</span>: {formatAdmissionsDemoText(checkpoint.status)}
                      <div className="mt-1">{formatAdmissionsDemoText(checkpoint.familyQuestion)}</div>
                      {checkpoint.misconception ? <div className="mt-1">{formatAdmissionsDemoText(checkpoint.misconception)}</div> : null}
                    </div>
                  ))}
                </div>
              </div>
              <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                <MiniList title="概念检查点" items={decisionBrief.conceptCheckpoints} />
                <MiniList title="决策问题" items={decisionBrief.decisionQuestions} />
                <MiniList title="硬边界" items={decisionBrief.hardBoundaries} />
                <MiniList title="不能声称" items={decisionBrief.cannotClaim} />
              </div>
            </div>
          </PanelBlock>
        )}

        <PanelBlock title="隐性机会复核">
          <div className="rounded-md border border-orange-200 bg-orange-50 px-3 py-3 text-sm text-orange-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.hiddenOpportunityAudit.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.hiddenOpportunityAudit.status)}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.hiddenOpportunityAudit.labelPermission)}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                评分：{demo.hiddenOpportunityAudit.score}
              </span>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.hiddenOpportunityAudit.scoreBands.map((band) => (
                <div key={formatAdmissionsDemoText(band.factor)} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-orange-950">{formatAdmissionsDemoText(band.factor)}</span>
                    <span className="rounded bg-orange-50 px-2 py-0.5 font-semibold">
                      {band.points} / {band.maxPoints}
                    </span>
                  </div>
                  <p className="mt-2">{formatAdmissionsDemoText(band.rationale)}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-orange-950">复核门禁</div>
              <div className="mt-1 grid grid-cols-1 gap-1 sm:grid-cols-2">
                <div>可进入机会台账：{formatAdmissionsDemoText(demo.hiddenOpportunityAudit.reviewGate.canEnterLedger ? "yes" : "no")}</div>
                <div>
                  隐性机会标签：{formatAdmissionsDemoText(demo.hiddenOpportunityAudit.reviewGate.canUseHiddenOpportunityLabel ? "allowed" : "blocked")}
                </div>
                <div>
                  必须保持假设表述：{formatAdmissionsDemoText(demo.hiddenOpportunityAudit.reviewGate.mustStayHypothesisOnly ? "yes" : "no")}
                </div>
                <div>
                  顾问签字：{formatAdmissionsDemoText(demo.hiddenOpportunityAudit.reviewGate.counselorSignoffRequired ? "required" : "not required")}
                </div>
              </div>
              <MiniList title="Gate reasons" items={demo.hiddenOpportunityAudit.reviewGate.reasons} />
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Positive signals" items={demo.hiddenOpportunityAudit.positiveSignals} />
              <MiniList title="Negative signals" items={demo.hiddenOpportunityAudit.negativeSignals} />
              <MiniList
                title="Before family wording"
                items={demo.hiddenOpportunityAudit.requiredBeforeFamilyWording}
              />
              <MiniList title="Forbidden claims" items={demo.hiddenOpportunityAudit.forbiddenClaims} />
            </div>
            <p className="mt-3 text-xs leading-5 text-orange-800">{formatAdmissionsDemoText(demo.hiddenOpportunityAudit.claimBoundary)}</p>
          </div>
        </PanelBlock>

        <PanelBlock title="计划变化台账交接">
          <div className="rounded-md border border-fuchsia-200 bg-fuchsia-50 px-3 py-3 text-sm text-fuchsia-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.planChangeOpportunityLedger.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.planChangeOpportunityLedger.status)}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                评分：{demo.planChangeOpportunityLedger.score}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                门禁：{formatAdmissionsDemoText(demo.planChangeOpportunityLedger.hiddenOpportunityGate.status)}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.planChangeOpportunityLedger.summary)}</p>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-fuchsia-950">隐性机会门禁</div>
              <div className="mt-1">
                {formatAdmissionsDemoText(demo.planChangeOpportunityLedger.hiddenOpportunityGate.labelPermission)};
                可进入机会台账：{formatAdmissionsDemoText(demo.planChangeOpportunityLedger.hiddenOpportunityGate.canEnterLedger ? "yes" : "no")}；
                评分：{formatAdmissionsDemoText(demo.planChangeOpportunityLedger.hiddenOpportunityGate.score ?? "not supplied")}
              </div>
              <MiniList title="Gate reasons" items={demo.planChangeOpportunityLedger.hiddenOpportunityGate.reasons} />
            </div>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.planChangeOpportunityLedger.opportunities.map((opportunity) => (
                <div key={opportunity.id} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-fuchsia-950">
                      {formatAdmissionsDemoText(opportunity.affectedRows[0]?.schoolName ?? "Unknown school")}
                    </span>
                    <span className="rounded bg-fuchsia-50 px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(opportunity.diffType)}</span>
                    <span>{formatAdmissionsDemoText(opportunity.status)}</span>
                  </div>
                  <p className="mt-2">
                    位次影响：{formatAdmissionsDemoText(opportunity.rankDeltaEstimate.direction)} {formatAdmissionsDemoText(opportunity.rankDeltaEstimate.rankDelta ?? "unknown")}
                  </p>
                  <p className="mt-1">
                    外部方案遗漏：{formatAdmissionsDemoText(opportunity.competitorMissed.status)}；处理动作：{formatAdmissionsDemoText(opportunity.recommendationAction)}
                  </p>
                  <MiniList title="Risk guard" items={opportunity.riskGuard.checks} />
                  <MiniList title="Audit trail" items={opportunity.auditTrail.slice(-3)} />
                </div>
              ))}
            </div>
            {demo.planChangeOpportunityLedger.blockedClaims.length > 0 ? (
              <MiniList title="被阻断的声称" items={demo.planChangeOpportunityLedger.blockedClaims} />
            ) : null}
            <p className="mt-3 text-xs leading-5 text-fuchsia-800">{formatAdmissionsDemoText(demo.planChangeOpportunityLedger.claimBoundary)}</p>
          </div>
        </PanelBlock>

        <PanelBlock title="有证据支撑的志愿方案叙事">
          <div className="rounded-md border border-cyan-200 bg-cyan-50 px-3 py-3 text-sm text-cyan-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.volunteerPlanNarrativePackage.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.volunteerPlanNarrativePackage.status)}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                家庭沟通：{formatAdmissionsDemoText(demo.volunteerPlanNarrativePackage.deliveryGate.canShowToFamily ? "ready" : "blocked")}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.volunteerPlanNarrativePackage.headline)}</p>
            <div className="mt-3 grid grid-cols-1 gap-2">
              {demo.volunteerPlanNarrativePackage.planRows.map((row) => (
                <div key={row.id} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-cyan-950">{formatAdmissionsDemoText(row.displayName)}</span>
                    <span className="rounded bg-cyan-50 px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(row.position)}</span>
                    <span>{formatAdmissionsDemoText(row.labelPermission)}</span>
                    <span>仅作假设：{formatAdmissionsDemoText(row.mustStayHypothesisOnly ? "yes" : "no")}</span>
                  </div>
                  <p className="mt-2">{formatAdmissionsDemoText(row.familyWording)}</p>
                  <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
                    {row.evidencePillars.slice(0, 6).map((pillar) => (
                      <div key={`${row.id}-${formatAdmissionsDemoText(pillar.claim)}-${formatAdmissionsDemoText(pillar.stance)}`} className="rounded bg-cyan-50 px-2 py-2">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-semibold">{formatAdmissionsDemoText(pillar.claim)}</span>
                          <span className="rounded bg-white px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(pillar.stance)}</span>
                        </div>
                        <p className="mt-1">{formatAdmissionsDemoText(pillar.familyWording)}</p>
                        <MiniList title="Evidence basis" items={pillar.evidenceBasis.slice(0, 2)} />
                        <MiniList title="Counter checks" items={pillar.counterChecks.slice(0, 2)} />
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
                    <MiniList title="Search follow-ups" items={row.searchFollowUps} />
                    <MiniList title="Concept prompts" items={row.conceptPrompts} />
                    <MiniList title="Interest prompts" items={row.interestPrompts} />
                    <MiniList title="Risk guard" items={row.riskGuard} />
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Conversation flow" items={demo.volunteerPlanNarrativePackage.conversationFlow} />
              <MiniList title="Forbidden claims" items={demo.volunteerPlanNarrativePackage.forbiddenClaims} />
              <MiniList title="Next actions" items={demo.volunteerPlanNarrativePackage.nextActions} />
              {demo.volunteerPlanNarrativePackage.deliveryGate.blockedReasons.length > 0 ? (
                <MiniList title="阻断原因" items={demo.volunteerPlanNarrativePackage.deliveryGate.blockedReasons} />
              ) : null}
            </div>
            <p className="mt-3 text-xs leading-5 text-cyan-800">{formatAdmissionsDemoText(demo.volunteerPlanNarrativePackage.claimBoundary)}</p>
          </div>
        </PanelBlock>

        <PanelBlock title="详细解读">
          <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-3 text-sm text-rose-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.detailedInterpretation.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.detailedInterpretation.status)}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.detailedInterpretation.planPosition.rowUse)}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.detailedInterpretation.headline)}</p>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.detailedInterpretation.summary)}</p>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.detailedInterpretation.claimRows.map((row) => (
                <div key={formatAdmissionsDemoText(row.claim)} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-rose-950">{formatAdmissionsDemoText(row.claim)}</span>
                    <span className="rounded bg-rose-50 px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(row.stance)}</span>
                  </div>
                  <p className="mt-2">{formatAdmissionsDemoText(row.familyWording)}</p>
                  <MiniList title="Evidence basis" items={row.evidenceBasis.slice(0, 3)} />
                  <MiniList title="Sources" items={row.sourceRefs.slice(0, 3)} />
                  {row.counterChecks.length > 0 ? (
                    <MiniList title="Counter checks" items={row.counterChecks.slice(0, 3)} />
                  ) : null}
                  <p className="mt-2 text-rose-800">{formatAdmissionsDemoText(row.claimBoundary)}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <div className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                <div className="font-semibold text-rose-950">家庭决策路径</div>
                <div className="mt-1">
                  {formatAdmissionsDemoText(demo.detailedInterpretation.familyDecisionPath.conceptReadinessProtocol)};
                  状态：{formatAdmissionsDemoText(demo.detailedInterpretation.familyDecisionPath.conceptReadinessStatus)}
                </div>
                <MiniList
                  title="Required questions"
                  items={demo.detailedInterpretation.familyDecisionPath.requiredQuestions}
                />
                <MiniList title="Hard stops" items={demo.detailedInterpretation.familyDecisionPath.hardStops} />
              </div>
              <div className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                <div className="font-semibold text-rose-950">方案位置</div>
                <div className="mt-1">{formatAdmissionsDemoText(demo.detailedInterpretation.planPosition.rowUse)}</div>
                <MiniList
                  title="Not recommendation reasons"
                  items={demo.detailedInterpretation.planPosition.notARecommendationReasons}
                />
                <MiniList title="Next actions" items={demo.detailedInterpretation.nextActions} />
              </div>
            </div>
          </div>
        </PanelBlock>

        <PanelBlock title="网页证据研究策略">
          <div className="rounded-md border border-sky-200 bg-sky-50 px-3 py-3 text-sm text-sky-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.researchStrategy.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.researchStrategy.status)}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.researchStrategy.presentationGate)}</p>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.researchStrategy.researchPillars.map((pillar) => (
                <div key={formatAdmissionsDemoText(pillar.pillar)} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-sky-950">{formatAdmissionsDemoText(pillar.pillar)}</span>
                    <span className="rounded bg-sky-50 px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(pillar.status)}</span>
                    <span>{pillar.evidenceCount} 条证据</span>
                  </div>
                  <p className="mt-2">{formatAdmissionsDemoText(pillar.nextCheck)}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-sky-950">优先检索问题</div>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.researchStrategy.priorityQueries.slice(0, 6).map((query) => (
                  <div key={query.id} className="rounded bg-sky-50 px-2 py-2">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-semibold">{formatAdmissionsDemoText(query.searchIntent ?? query.taskType)}</span>
                      <span className="rounded bg-white px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(query.priority)}</span>
                      <span>{formatAdmissionsDemoText(query.status)}</span>
                    </div>
                    <p className="mt-1">{formatAdmissionsDemoText(query.evidenceQuestion)}</p>
                    <p className="mt-1 break-words text-sky-800">{formatAdmissionsDemoText(query.query)}</p>
                    <div className="mt-1">不能作为证明：{formatAdmissionsDemoText(query.rejectsAsProof.join("、") || "none")}</div>
                    <div className="mt-1">{formatAdmissionsDemoText(query.escalationRule)}</div>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Contradiction tests" items={demo.researchStrategy.contradictionTests.slice(0, 6)} />
              <MiniList title="Minimum evidence rules" items={demo.researchStrategy.minimumEvidenceRules} />
              <MiniList title="Operator brief" items={demo.researchStrategy.operatorBrief} />
            </div>
          </div>
        </PanelBlock>

        <PanelBlock title="家庭决策澄清路线图">
          <div className="rounded-md border border-lime-200 bg-lime-50 px-3 py-3 text-sm text-lime-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.familyClarityRoadmap.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.familyClarityRoadmap.status)}
              </span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                志愿行：{formatAdmissionsDemoText(demo.familyClarityRoadmap.rowDiscussionGate.canDiscussRows ? "ready" : "blocked")}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.familyClarityRoadmap.rowDiscussionGate.nextAction)}</p>
            <div className="mt-3 grid grid-cols-1 gap-2 lg:grid-cols-2">
              {demo.familyClarityRoadmap.conceptCards.map((card) => (
                <div key={formatAdmissionsDemoText(card.concept)} className="rounded-md bg-white px-3 py-2 text-xs leading-5">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-semibold text-lime-950">{formatAdmissionsDemoText(card.concept)}</span>
                    <span className="rounded bg-lime-50 px-2 py-0.5 font-semibold">{formatAdmissionsDemoText(card.status)}</span>
                  </div>
                  <p className="mt-2">{formatAdmissionsDemoText(card.plainMeaning)}</p>
                  <p className="mt-2">{formatAdmissionsDemoText(card.familyQuestion)}</p>
                  <p className="mt-2 text-lime-800">{formatAdmissionsDemoText(card.decisionImpact)}</p>
                  {card.misconception ? <p className="mt-2">{formatAdmissionsDemoText(card.misconception)}</p> : null}
                  <p className="mt-2">{formatAdmissionsDemoText(card.repairAction)}</p>
                </div>
              ))}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-lime-950">兴趣判断轴</div>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.familyClarityRoadmap.interestAxes.map((axis) => (
                  <div key={formatAdmissionsDemoText(axis.axis)} className="rounded bg-lime-50 px-2 py-2">
                    <div className="font-semibold">{formatAdmissionsDemoText(axis.axis)}</div>
                    <p className="mt-1">{formatAdmissionsDemoText(axis.prompt)}</p>
                    <p className="mt-1 text-lime-800">{formatAdmissionsDemoText(axis.whyItMatters)}</p>
                    <p className="mt-1">{formatAdmissionsDemoText(axis.evidenceToCollect)}</p>
                  </div>
                ))}
              </div>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="Alignment questions" items={demo.familyClarityRoadmap.parentStudentAlignment.questions} />
              <MiniList title="Hard stops" items={demo.familyClarityRoadmap.parentStudentAlignment.hardStops} />
              {demo.familyClarityRoadmap.rowDiscussionGate.blockedReasons.length > 0 ? (
                <MiniList title="阻断原因" items={demo.familyClarityRoadmap.rowDiscussionGate.blockedReasons} />
              ) : null}
            </div>
          </div>
        </PanelBlock>

        <PanelBlock title="顾问复核材料包">
          <div className="rounded-md border border-indigo-200 bg-indigo-50 px-3 py-3 text-sm text-indigo-950">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-semibold">{formatAdmissionsDemoText(demo.counselorReviewDossier.protocol)}</span>
              <span className="rounded bg-white px-2 py-0.5 text-xs font-semibold">
                {formatAdmissionsDemoText(demo.counselorReviewDossier.status)}
              </span>
            </div>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.counselorReviewDossier.caseSummary.summary)}</p>
            <p className="mt-2 text-xs leading-5">{formatAdmissionsDemoText(demo.counselorReviewDossier.opportunityThesis)}</p>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-indigo-950">趋势表述边界</div>
              <div className="mt-1">
                状态：{formatAdmissionsDemoText(demo.counselorReviewDossier.publicOpinionPosition.wordingGateStatus)}；
                评分：{demo.counselorReviewDossier.publicOpinionPosition.wordingGateScore}；
                隐性机会标签：{formatAdmissionsDemoText(demo.counselorReviewDossier.publicOpinionPosition.canUseHiddenOpportunityLabel ? "allowed" : "blocked")}
              </div>
              <p className="mt-2">{formatAdmissionsDemoText(demo.counselorReviewDossier.publicOpinionPosition.familySafeWording)}</p>
            </div>
            <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-2">
              <MiniList title="What we can say" items={demo.counselorReviewDossier.whatWeCanSay} />
              <MiniList title="不能对家庭声称" items={demo.counselorReviewDossier.whatWeCannotSay} />
              <MiniList title="Counselor checklist" items={demo.counselorReviewDossier.counselorReviewChecklist} />
              <MiniList title="Family questions" items={demo.counselorReviewDossier.familyQuestions} />
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              证据链：{demo.counselorReviewDossier.evidenceTrail.length} 条已采纳证据；
              缺口：{formatAdmissionsDemoText(demo.counselorReviewDossier.gapPosition.status)}；
              交叉验证：{formatAdmissionsDemoText(demo.counselorReviewDossier.gapPosition.triangulationStatus)}；
              公开讨论证据角色：{formatAdmissionsDemoText(demo.counselorReviewDossier.publicOpinionPosition.evidenceRole)}
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-indigo-950">检索来源记录</div>
              <div className="mt-1">
                {formatAdmissionsDemoText(demo.counselorReviewDossier.searchProvenance.protocol)};
                检索轮次：{demo.counselorReviewDossier.searchProvenance.runCount}；
                来源提供方：{formatAdmissionsDemoText(demo.counselorReviewDossier.searchProvenance.providerIds.join("、") || "none")}；
                采纳：{demo.counselorReviewDossier.searchProvenance.summary.acceptedRows}；
                拒绝：{demo.counselorReviewDossier.searchProvenance.summary.rejectedRows}；
                未返回：{demo.counselorReviewDossier.searchProvenance.summary.unreturnedRows}
              </div>
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.counselorReviewDossier.searchProvenance.queryRows.slice(0, 8).map((row) => (
                  <div key={`${row.requestId}-${formatAdmissionsDemoText(row.query)}`} className="rounded bg-indigo-50 px-2 py-1">
                    <span className="font-semibold">{formatAdmissionsDemoText(row.searchIntent ?? row.taskType)}</span>: {formatAdmissionsDemoText(row.query)}
                    {row.evidenceQuestion ? <div className="mt-1">{formatAdmissionsDemoText(row.evidenceQuestion)}</div> : null}
                    {row.rejectsAsProof && row.rejectsAsProof.length > 0 ? (
                      <div className="mt-1">不能作为证明：{formatAdmissionsDemoText(row.rejectsAsProof.join("、"))}</div>
                    ) : null}
                  </div>
                ))}
              </div>
              <ul className="mt-2 list-disc space-y-1 pl-4">
                {demo.counselorReviewDossier.searchProvenance.resultRows.slice(0, 4).map((row, index) => (
                  <li key={`${row.taskId}-${row.sourceTitle ?? row.outcome}-${index}`}>
                    {formatAdmissionsDemoText(row.provider ?? "no provider")} {formatAdmissionsDemoText(row.outcome)}：{formatAdmissionsDemoText(row.sourceTitle ?? row.taskType)}
                    {row.rejectionReason ? ` (${formatAdmissionsDemoText(row.rejectionReason)})` : ""}
                  </li>
                ))}
              </ul>
            </div>
            <div className="mt-3 rounded-md bg-white px-3 py-2 text-xs leading-5">
              <div className="font-semibold text-indigo-950">证据质量</div>
              <div className="mt-1">
                {formatAdmissionsDemoText(demo.counselorReviewDossier.evidenceQuality.protocol)};
                状态：{formatAdmissionsDemoText(demo.counselorReviewDossier.evidenceQuality.status)}；
                权威来源：{demo.counselorReviewDossier.evidenceQuality.summary.authoritativeSources}；
                当前周期：{demo.counselorReviewDossier.evidenceQuality.summary.currentCycleSources}；
                过期：{demo.counselorReviewDossier.evidenceQuality.summary.staleSources}；
                冲突：{demo.counselorReviewDossier.evidenceQuality.summary.conflictedClaims}
              </div>
              <p className="mt-2">{formatAdmissionsDemoText(demo.counselorReviewDossier.evidenceQuality.familyPresentationGate)}</p>
              {demo.counselorReviewDossier.evidenceQuality.blockingConcerns.length > 0 && (
                <MiniList
                  title="Quality blockers"
                  items={demo.counselorReviewDossier.evidenceQuality.blockingConcerns}
                />
              )}
              <div className="mt-2 grid grid-cols-1 gap-2 lg:grid-cols-2">
                {demo.counselorReviewDossier.evidenceQuality.sourceRows.slice(0, 4).map((row) => (
                  <div key={`${row.taskId}-${formatAdmissionsDemoText(row.claim)}-${row.sourceTitle}`} className="rounded bg-indigo-50 px-2 py-1">
                    <span className="font-semibold">{formatAdmissionsDemoText(row.claim)}</span>: {formatAdmissionsDemoText(row.authorityLevel)}, {formatAdmissionsDemoText(row.freshness)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </PanelBlock>

        <div className="rounded-md border border-gray-200 bg-gray-50 px-4 py-3 text-xs leading-5 text-gray-600">
          {formatAdmissionsDemoText(demo.claimBoundary)}
        </div>
      </div>

        </main>

        <aside className="workbench-decision border border-[#C8D8EA] bg-[#1F5E99] p-4 text-[#F8FBFF]">
          <p className="font-mono text-xs font-semibold uppercase tracking-[0.16em] text-[#FFA02F]">判断输出</p>
          <h2 className="mt-3 text-xl font-semibold">趋势机会必须带反证条件</h2>
          <ul className="mt-4 space-y-3 text-sm leading-6 text-[#EAF3FF]">
            <li>隐性机会只能在门禁允许后进入家庭话术。</li>
            <li>就业、考研保研、考公方向需要真实证据，不允许泛泛而谈。</li>
            <li>未完成证据缺口时，只能写成 hypothesis-only。</li>
          </ul>
          <div className="mt-5 border border-[#78A7D8] p-3 font-mono text-xs text-[#FFA02F]">
            趋势分析必须包含证据账本、反证检查和顾问复核签字。
          </div>
        </aside>
      </div>

    </section>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
      <div className="text-xs font-semibold uppercase text-gray-500">{formatAdmissionsDemoText(label)}</div>
      <div className="mt-1 break-words text-base font-bold text-gray-900">{formatAdmissionsDemoText(value)}</div>
    </div>
  );
}

function PanelBlock({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="mt-5 rounded-md border border-gray-200 bg-white px-4 py-4">
      <h4 className="text-sm font-bold text-gray-900">{formatAdmissionsDemoText(title)}</h4>
      <div className="mt-3">{children}</div>
    </section>
  );
}

function MiniList({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="rounded-md bg-white px-3 py-2 text-xs leading-5">
      <div className="font-semibold text-slate-900">{formatAdmissionsDemoText(title)}</div>
      <ul className="mt-1 list-disc space-y-1 pl-4 text-slate-700">
        {items.map((item) => (
          <li key={item}>{formatAdmissionsDemoText(item)}</li>
        ))}
      </ul>
    </div>
  );
}
