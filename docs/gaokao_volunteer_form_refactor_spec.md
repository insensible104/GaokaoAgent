# 广东高考志愿表生成重构 SPEC v0.1

## 0. 结论先行

下一版项目不应继续描述为“多 Agent 生成专业组推荐列表”，而应重构为“广东院校专业组志愿表生成与风险审计系统”。真实输出不是若干学校建议，而是一张可落到广东志愿填报表的草案：每一行包含院校代码、院校名称、院校专业组代码、1-6 个专业志愿、是否服从专业调剂、投档概率、组内专业风险和人工复核提示。

一句话记忆：

> 项目核心不是推荐一个专业组，而是生成一张能填、能解释、能审计的广东院校专业组志愿表。

## 1. 真实业务对象

广东普通类本科/专科志愿采用院校专业组平行志愿。一个院校专业组是一个独立投档单位，组内再填写最多 6 个专业志愿，并选择是否服从专业调剂。投档到某个院校专业组后，后续志愿不再检索；若进组后因专业录取、身体条件、单科要求、不服从调剂等原因退档，本批次后续志愿也不再补投。

因此系统需要区分两层风险：

| 层级 | 问题 | 当前实现状态 | 下一版目标 |
| --- | --- | --- | --- |
| 专业组投档 | 用户能否被投到该院校专业组 | 已有 `admission_prob`、`rank_diff`、`strategy_tag` | 保留并修正数据来源 |
| 组内专业分配 | 进组后能否录到想要的专业，服从调剂后最差结果是什么 | 只用 `major_list` 和粗糙 `adjustment_risk` | 新增组内 1-6 专业排序、调剂风险和尾部结果解释 |

一句话记忆：

> 专业组决定能不能进门，组内专业排序和调剂决定进门后坐在哪个位置。

## 2. 当前项目的关键问题

当前代码已经有基础，但对象层次还不够准。

| 当前基础 | 问题 | 修改方向 |
| --- | --- | --- |
| `GameAgent` 能召回专业组并计算录取概率 | 输出仍是专业组列表，不是广东志愿表行 | 新增 `VolunteerChoice` 和 `VolunteerPlan` |
| `MajorGroupRow.major_list` 保存组内专业 | 没有专业序号、专业计划数、专业历史位次、组内排序 | 新增 `MajorOption` |
| `adjustment_risk = 0.15 if len(major_list) < 6 else 0.05` | 专业数量不等于调剂风险 | 改成基于低效用专业占比、黑名单、专业差异和是否服从调剂 |
| `quota` 被读取 | 没有写入 `MajorGroupRow`，还把 `major_count <= 3` 当小招生规模 | 使用真实 `quota` 判断招生规模 |
| `quant_engine` 映射旧历史字段 | 2025 招生计划里的 `专业名称`、`专业组代码`、`计划招数`、`2024_最低位次` 没有统一映射 | 拆出招生计划仓库，不把计划数据当普通历史行清洗掉 |
| Report 解释录取概率 | 没解释 6 个专业志愿怎么排、是否服从调剂、最差专业是什么 | 报告改成志愿表草案 + 风险审计 |

一句话记忆：

> 现在缺的不是算法名字，而是把“广东志愿表行”变成系统一等公民。

## 3. 目标数据模型

### 3.1 MajorOption

每个专业组内的一个专业选项。

```python
class MajorOption(BaseModel):
    school_code: str
    school_name: str
    major_group_code: str
    major_code: str
    major_name: str
    subject_requirement: str | None
    plan_quota: int | None
    tuition: float | None
    remarks: str | None

    historical_min_scores: dict[int, float | None]
    historical_min_ranks: dict[int, int | None]

    category: str | None
    user_utility: float
    is_preferred: bool
    is_acceptable: bool
    is_blacklisted: bool
    major_rank_risk: float
    risk_reasons: list[str]
```

关键点：不要只保存专业名，要保存专业序号、计划数、历史专业最低位次和用户效用。

### 3.2 MajorGroupCandidate

一个可被推荐的院校专业组候选。

```python
class MajorGroupCandidate(BaseModel):
    school_code: str
    school_name: str
    major_group_code: str
    batch: str
    subject_group: str

    majors: list[MajorOption]
    group_quota: int
    group_historical_min_ranks: dict[int, int | None]

    group_admission_prob: float
    rank_diff: int
    strategy_tag: str
    quota_bucket: str
    quota_stability_score: float
    variance_opportunity_score: float

    acceptable_major_ratio: float
    blacklist_major_ratio: float
    major_utility_mean: float
    major_utility_min: float
    major_utility_dispersion: float
    tail_assignment_risk: float
    bundle_type: str
    risk_reasons: list[str]
```

关键点：专业组不是一个专业，而是一个 bundle。系统要同时看组级投档概率和组内专业下限。

### 3.3 VolunteerChoice

真实志愿表的一行。

```python
class VolunteerChoice(BaseModel):
    choice_index: int
    school_code: str
    school_name: str
    major_group_code: str

    major_choices: list[MajorOption]  # 1-6 个，按建议填报顺序排序
    obey_adjustment: bool
    adjustment_advice: str  # recommend / cautious / avoid

    group_admission_prob: float
    expected_major_utility: float
    worst_case_major: str | None
    tail_assignment_risk: float
    strategy_tag: str
    recommendation_role: str
    explanation: str
    audit_flags: list[str]
```

关键点：`major_choices` 不是简单展示专业组所有专业，而是系统建议用户填到表里的 1-6 个专业顺序。

### 3.4 VolunteerPlan

完整志愿草案。

```python
class VolunteerPlan(BaseModel):
    province: str = "广东"
    year: int
    subject_group: str
    user_score: int | None
    user_rank: int

    choices: list[VolunteerChoice]
    total_rush: int
    total_target: int
    total_safe: int

    safe_anchor_coverage: float
    average_tail_risk: float
    blacklist_violation_count: int
    adjustment_warning_count: int
    plan_summary: str
    human_review_items: list[str]
```

一句话记忆：

> `MajorOption` 管专业，`MajorGroupCandidate` 管组，`VolunteerChoice` 管一行志愿，`VolunteerPlan` 管整张表。

## 4. 目标算法链路

```text
用户输入
-> ProfileParser
-> DataRepository
-> MajorGroupRecall
-> GroupAdmissionScorer
-> MajorUtilityScorer
-> BundleRiskAnalyzer
-> MajorChoicePlanner
-> VolunteerPortfolioOptimizer
-> Critic
-> ReportGenerator
```

### 4.1 ProfileParser

输入：分数、位次、科类、选科、城市偏好、学校偏好、专业偏好、黑名单专业、风险偏好、是否愿意接受调剂。

输出：

```text
UserProfile
PreferenceVector
BlacklistRules
RiskTolerance
```

实现重点：不要直接相信“我想学计算机”。需要把偏好拆成专业方向、可接受专业、强排斥专业和不确定偏好。

### 4.2 DataRepository

输入：历史录取数据、2025 招生计划、一分一段表。

输出：

```text
HistoricalAdmissionRecord
EnrollmentPlanRecord
MajorGroupCandidate raw rows
```

实现重点：2025 招生计划不能被旧历史字段清洗逻辑误删。它应该单独进入 `EnrollmentPlanRepository`，再与 2021-2024 历史专业/专业组位次 join。

### 4.3 MajorGroupRecall

目标：召回候选院校专业组，而不是直接排序。

召回通道：

| 通道 | 目的 |
| --- | --- |
| 位次窗口召回 | 找到与用户位次相近的专业组 |
| 稳定保底召回 | 找招生计划较大、历史波动小的安全垫 |
| 高波动机会召回 | 找小计划、历史波动大但可能捡漏的候选 |
| 专业偏好召回 | 找含目标专业方向的专业组 |
| 城市偏好召回 | 找满足地域偏好的专业组 |
| 反拥挤召回 | 找未被热门叙事充分追逐的专业组 |

实现重点：召回阶段允许宽一些，真正淘汰放到粗排和 Critic。

### 4.4 GroupAdmissionScorer

目标：估计“能不能进这个院校专业组”。

使用特征：

```text
user_rank
historical_group_min_rank
rank_diff
rank_volatility
quota
quota_change
subject_requirement
batch
```

输出：

```text
group_admission_prob
rank_ci_lower
rank_ci_upper
strategy_tag
quota_stability_score
variance_opportunity_score
```

实现重点：保留现有 Monte Carlo / Z-score，但要把 `quota`、`quota_bucket` 写入 row，不再用 `major_count <= 3` 判断小招生规模。

### 4.5 MajorUtilityScorer

目标：给组内每个专业计算用户效用。

使用特征：

```text
major_name
major_category
user_preferred_categories
user_acceptable_categories
blacklist_majors
school_quality
city_fit
tuition
remarks
historical_major_min_rank
plan_quota
```

输出：

```text
user_utility
is_preferred
is_acceptable
is_blacklisted
major_rank_risk
risk_reasons
```

实现重点：同一个专业组对不同用户风险不同。比如“计算机 + 土木 + 环境”的组，对能接受大工科的用户风险较低，对只接受计算机的用户风险很高。

### 4.6 BundleRiskAnalyzer

目标：分析专业组混搭风险。

核心指标：

```text
acceptable_major_ratio
blacklist_major_ratio
major_utility_min
major_utility_dispersion
tail_assignment_risk
bundle_type
```

`bundle_type` 建议：

| 类型 | 含义 |
| --- | --- |
| `clean_fit` | 组内大多数专业都符合偏好 |
| `mild_mixed` | 有少量低偏好专业，但可接受 |
| `highly_mixed` | 好专业和低偏好专业混搭明显 |
| `bait_risk` | 用户冲着热门专业来，但组内尾部专业明显不可接受 |
| `blacklist_blocked` | 组内包含用户明确不能接受的专业 |

实现重点：如果一个组里有计算机类，也有土木、材料、环境，不能把这个组简单标成“计算机推荐”。

### 4.7 MajorChoicePlanner

目标：生成每个专业组内 1-6 个专业志愿排序和服从调剂建议。

规则：

1. 优先放高效用、低专业线风险的专业。
2. 不把黑名单专业放进 1-6 个志愿。
3. 如果组内可接受专业少于 3 个，标记高组内风险。
4. 如果保底组尾部专业不可接受，不应作为保底。
5. 是否服从调剂不是简单二选一：
   - 高风险冲刺组：可以建议“不服从/谨慎服从”，但要提示退档风险。
   - 稳妥组：若尾部可接受，可以建议服从。
   - 保底组：必须选择尾部风险低且建议服从的组，否则不是真保底。

一句话记忆：

> 保底不是录取概率高就行，还要服从调剂后的最差专业能接受。

### 4.8 VolunteerPortfolioOptimizer

目标：生成整张志愿表草案，而不是简单 top-k。

组合约束：

```text
冲刺、稳妥、保底比例合理
保底项尾部风险低
同一学校/城市/专业方向不过度集中
不出现黑名单专业未提示
不把高混搭组放到保底角色
前序志愿不能全是高波动机会
```

输出：

```text
VolunteerPlan
```

实现重点：广东本科普通类最多 45 个院校专业组志愿。第一版可以生成可配置数量，例如 30 或 45；但模型对象必须支持 45 行完整表。

### 4.9 Critic

目标：检查方案是否能解释、可执行、风险充分披露。

Critic 检查项：

| 检查项 | 失败条件 |
| --- | --- |
| 志愿表结构 | 缺院校代码、专业组代码、专业序号、是否服从调剂 |
| 保底可靠性 | 保底组尾部专业不可接受或不建议服从 |
| 黑名单风险 | 组内出现黑名单专业但报告未提示 |
| 混搭误导 | 把含计算机的混搭组说成“计算机稳妥” |
| 调剂风险 | 建议服从但没有解释最差结果 |
| 数据证据 | 没给历史位次、计划数、位次波动依据 |
| 组合风险 | 冲刺过多、保底不足、城市/专业方向过度集中 |

一句话记忆：

> Critic 的职责不是润色报告，而是防止方案在真实填报规则下误导用户。

## 5. 分阶段实现路线

### P0：先修数据层

目标：让系统可靠读取 2025 招生计划和 2021-2024 历史录取。

修改文件：

```text
backend/src/engines/quant_engine.py
backend/src/engines/enrollment_loader.py
backend/src/models/game_matrix.py
```

具体动作：

1. 不再让 `GaokaoQuantEngine` 把所有 CSV 混在一起用同一套字段清洗。
2. 新增或重构 `EnrollmentPlanRepository`，专门读取：
   - `院校代码`
   - `院校名称`
   - `批次`
   - `科类`
   - `专业组代码`
   - `专业序号`
   - `专业名称`
   - `专业备注`
   - `选科要求`
   - `计划招数`
   - `2021-2024_最低分`
   - `2021-2024_最低位次`
3. 历史录取数据继续读取旧字段：
   - `代码`
   - `院校名称`
   - `专业/类`
   - `专业组`
   - `录取人数`
   - `最低分平均排位`
4. 提供统一查询接口：

```python
get_major_group_candidates(subject_group, batch)
get_group_plan(school_code, major_group_code)
get_group_history(school_name, major_group_code)
get_major_history(school_code, major_group_code, major_code)
```

验收标准：

```text
能查出北京科技大学 214 专业组：
土木类、储能科学与工程、材料科学与工程、机械类、能源动力类、自动化类、计算机类、通信工程
并能给出各专业计划数和历年最低位次。
```

### P1：新增核心 schema

目标：把真实志愿表结构固化到代码。

修改文件：

```text
backend/src/models/game_matrix.py
```

新增模型：

```text
MajorOption
MajorGroupCandidate
VolunteerChoice
VolunteerPlan
AdjustmentAdvice
BundleType
```

兼容策略：

1. 保留 `MajorGroupRow`，避免前端立即崩。
2. 新增 `volunteer_plan` 字段到 `GameMatrix`。
3. 先让旧接口继续返回 `major_group_rows`，同时返回新 `VolunteerPlan`。

验收标准：

```text
一个推荐结果可以同时以旧 GameMatrix 展示，也可以以新 VolunteerPlan 展示。
```

### P2：新增专业效用和混搭风险模块

目标：让系统知道“组内专业是否真的适合这个用户”。

新增文件：

```text
backend/src/recommendation/major_taxonomy.py
backend/src/recommendation/major_utility.py
backend/src/recommendation/bundle_risk.py
```

核心函数：

```python
classify_major(major_name: str) -> str
score_major_utility(major: MajorOption, profile: UserProfile) -> float
analyze_bundle_risk(majors: list[MajorOption], profile: UserProfile) -> BundleRiskResult
```

第一版可以用规则，不要急着上大模型：

```text
计算机/软件/人工智能/数据科学 -> 计算机类
电子/通信/自动化/集成电路 -> 电子信息类
土木/建筑/环境/材料/化工 -> 传统工科或低偏好风险类
医学/师范/法学/财经等单独分类
```

验收标准：

```text
用户说“只想学计算机，不能接受土木材料”时，
北京科技大学 214 专业组应被标记为 highly_mixed 或 bait_risk，而不是普通计算机推荐。
```

### P3：拆分 GameAgent

目标：让推荐链路清楚，不再把所有逻辑塞在一个大函数。

新增目录：

```text
backend/src/recommendation/
  __init__.py
  recall.py
  group_admission.py
  major_choice_planner.py
  portfolio_optimizer.py
  schemas.py
```

重构后职责：

| 文件 | 职责 |
| --- | --- |
| `recall.py` | 候选专业组召回 |
| `group_admission.py` | 投档概率、Z-score、quota 稳定性 |
| `major_choice_planner.py` | 组内 1-6 专业排序、调剂建议 |
| `portfolio_optimizer.py` | 冲稳保组合和 45 行志愿表排序 |
| `game_agent.py` | 只负责调用上述模块并写入 state |

验收标准：

```text
game_agent.py 主流程能读成：
load profile -> recall -> score groups -> plan majors -> optimize portfolio -> build GameMatrix
```

### P4：生成志愿表草案

目标：从专业组推荐升级为志愿表生成。

新增函数：

```python
build_volunteer_choice(candidate, profile, choice_index) -> VolunteerChoice
build_volunteer_plan(candidates, profile, max_choices=45) -> VolunteerPlan
```

输出示例：

```text
志愿 12
院校代码：10008
院校名称：北京科技大学
专业组代码：214
专业1：计算机类
专业2：通信工程
专业3：自动化类
专业4：机械类
专业5：能源动力类
专业6：储能科学与工程
是否服从调剂：谨慎服从
风险：组内含土木类、材料科学与工程；若计算机类竞争失败，存在低偏好调剂结果。
```

验收标准：

```text
接口响应里有结构化 `volunteer_plan.choices[*].major_choices`，
每行最多 6 个专业，并明确 `obey_adjustment` 和 `adjustment_advice`。
```

### P5：升级 Critic 和 Report

目标：报告不只解释录取概率，还要解释志愿表填法。

修改文件：

```text
backend/src/agents/critic_agent.py
backend/src/agents/report_agent.py
backend/src/prompts/critic.py
backend/src/prompts/report.py
```

Report 必须包含：

```text
1. 志愿表总览
2. 冲稳保比例
3. 每行志愿：院校代码、专业组代码、6 个专业顺序、是否服从调剂
4. 专业组投档概率
5. 组内专业混搭风险
6. 最差调剂结果
7. 保底项是否真的安全
8. 人工复核事项
```

Critic 必须新增失败规则：

```text
不能把“含计算机类的专业组”直接表述为“计算机专业稳妥”
不能把尾部专业不可接受的组放入保底
不能缺少是否服从调剂建议
不能缺少专业组代码和专业序号
```

验收标准：

```text
报告能明确回答：
我填哪一行？
每行填哪 6 个专业？
要不要服从调剂？
最差可能去哪个专业？
为什么这个组是冲/稳/保？
```

### P6：补 evaluation harness

目标：让项目从“能跑”变成“可评估”。

新增目录：

```text
backend/evaluation/
  run_eval.py
  eval_cases.jsonl
  metrics.py
```

核心指标：

| 指标 | 含义 |
| --- | --- |
| `schema_valid_rate` | 志愿表结构是否完整 |
| `safe_anchor_coverage` | 是否有足够低风险保底 |
| `blacklist_violation_rate` | 黑名单专业是否被放入推荐 |
| `tail_risk_warning_recall` | 高尾部风险是否被提示 |
| `adjustment_advice_coverage` | 是否每行都有服从调剂建议 |
| `evidence_coverage` | 是否给出计划数、历史位次等证据 |
| `critic_reroute_rate` | Critic 发现问题并要求重跑的比例 |
| `avg_latency` | 平均响应时间 |

测试 case 必须覆盖：

```text
只接受计算机
能接受大工科
明确排斥土木材料
低风险保守型
高分冲刺型
中分段容易后悔型
只看学校 title 型
城市偏好强约束型
```

验收标准：

```bash
python -m backend.evaluation.run_eval --cases backend/evaluation/eval_cases.jsonl
```

能输出每个 case 的结构化指标和失败原因。

### P7：前端展示改造

目标：前端从“卡片推荐”升级为“志愿表草案 + 风险说明”。

修改文件：

```text
frontend/src/components/GameMatrixView.tsx
frontend/src/components/ReportView.tsx
```

新增视图：

```text
VolunteerPlanTable
MajorGroupRiskPanel
AdjustmentAdviceBadge
AuditFlagsPanel
```

展示重点：

```text
志愿序号
院校代码
院校名称
专业组代码
专业1-6
是否服从调剂
冲稳保角色
投档概率
尾部风险
人工复核提示
```

验收标准：

```text
用户能直接看到一张接近广东志愿填报表的草案，而不是只看到推荐卡片。
```

## 6. 第一批提交建议

第一批不要大改 RL，也不要重写所有 Agent。先做能把业务对象校准的提交。

1. `data: add enrollment plan repository for Guangdong volunteer rows`
2. `models: add MajorOption VolunteerChoice VolunteerPlan schemas`
3. `recommendation: add major utility and bundle risk analyzer`
4. `recommendation: build volunteer choices with six major slots`
5. `critic: audit adjustment and mixed major-group risks`
6. `report: render Guangdong volunteer plan table`
7. `evaluation: add volunteer plan schema and tail-risk metrics`

一句话记忆：

> 第一批提交的目标不是模型更炫，而是让系统输出真的像广东志愿表。

## 7. 暂时不要做的事

为了避免项目继续发散，以下内容先不要进入第一轮重构：

| 暂不做 | 原因 |
| --- | --- |
| 复杂 RLVR / GRPO 重新训练 | 当前最大问题是业务建模和数据结构，不是策略学习 |
| 复杂博弈均衡求解 | 可以作为理论解释，但第一版不需要求均衡 |
| 完整预测组内真实录取分配 | 缺少每个考生组内专业志愿和院校专业分配规则，只能做风险 proxy |
| 过度依赖 LLM 生成专业排序 | 专业排序应先由结构化特征和规则完成，LLM 负责解释和审计 |
| 一次性重写 LangGraph | 先把推荐核心拆清楚，Graph 只做编排 |

一句话记忆：

> 先把规则、数据和输出对象做准，再考虑 RL 和更复杂的 Agent。

## 8. 面试表述升级版

30 秒版本：

> 我后来把这个项目重新校准成广东院校专业组志愿表生成系统。广东填报不是简单选学校或专业，而是每行填院校专业组、最多 6 个专业和是否服从调剂。所以我把推荐链路拆成两层：先估计能否投进某个专业组，再评估组内专业排序和调剂后的最差结果。系统最终输出的是志愿表草案，并用 Critic 检查保底、黑名单、混搭专业组和调剂风险。

1 分钟版本：

> 这个项目最核心的业务对象是院校专业组志愿。每个专业组是一个投档单位，但组内可能混合计算机、土木、材料、环境等不同专业，用户真正承担的是“进组后被分到哪个专业”的风险。我的改造思路是把候选生成、投档概率、组内专业效用、调剂风险和冲稳保组合分开建模。算法上先用位次窗口、专业偏好和保底召回生成候选组，再用历史位次、招生计划和 Monte Carlo 估计投档概率，然后对组内每个专业计算用户效用，生成 1-6 个专业志愿顺序和服从调剂建议，最后组合成一张可执行的志愿表，并通过 Critic 审计是否存在尾部专业不可接受、黑名单未提示或保底不安全的问题。

一句话记忆：

> 我解决的不是“推荐哪个学校”，而是“这张广东志愿表每一行怎么填，以及最差结果用户能不能接受”。

## 9. Claim-Evidence 校准

| Claim | Evidence | Status |
| --- | --- | --- |
| 广东志愿填报需要院校专业组、专业代码和是否服从调剂 | 广东省教育考试院志愿填报通知和工作规定 | supported |
| 当前项目已有专业组召回和投档概率基础 | `game_agent.py` 调用 `search_major_groups`、Monte Carlo、`classify_strategy_tag` | supported |
| 当前项目缺少真实志愿表行对象 | `MajorGroupRow` 只有 `major_list`，没有 1-6 专业志愿和调剂建议 | supported |
| 2025 招生计划字段没有被旧 `quant_engine` 完整映射 | 代码只映射 `专业/类`、`最低分平均排位`、`录取人数`、`专业组` 等旧字段 | supported |
| 可以精确预测组内专业录取结果 | 缺少考生组内志愿和院校分专业规则，只能做代理风险估计 | needs caution |

一句话记忆：

> 能支持的就强说，缺证据的就降级成 proxy，不要在面试里夸成精确预测。
