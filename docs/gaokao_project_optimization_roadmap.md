# GaokaoAgent 项目优化路线：从多 Agent 流程到高风险决策推荐 Harness

## 0. 2026-05-06 已落地的重写方向

这次修改不再把“博弈、情绪、专业组混搭、分数段选择”停留在文档里，而是接进了推荐链路：

```text
候选专业组
-> 录取概率 / 位次风险
-> 组内专业效用与尾部调剂风险
-> 招生计划稳定性与小计划波动机会
-> 分数段 tradeoff policy
-> 平行志愿市场拥挤与用户痛点标签
-> 志愿表首命中计算
-> advisor deliberation
-> report / critic
```

核心新增实现：

| 想法 | 代码落点 |
| --- | --- |
| 不同分数段的学校/专业/城市/安全权衡不同 | `backend/src/recommendation/tradeoff_policy.py::ScoreBandPolicy` |
| 别人也会追逐显眼的学校、热门专业、热门城市 | `crowding_risk`、`herding_crowding`、`market_behavior_notes` |
| 小招生计划更容易出现捡漏，也更容易滑档 | `quota_bucket`、`variance_opportunity_score`、`small_quota_lottery` |
| 招生多的专业组更适合做稳定锚点 | `quota_stability_score`、`large_quota_anchor` |
| 专业组可能把计算机和土木等专业混在一起 | `major_utility_dispersion`、`tail_major_regret`、`bait_major_group` |
| 用户真正痛点不是“推荐列表”，而是滑档、浪费分、被调剂到不想学的专业 | `pain_point_flags` |
| 多 agent 不能只是流程节点，要真的看风险信号 | `deliberation_agents.py` 读取 crowding / bait / hidden opportunity 后投票 |
| 报告不能只复述概率 | `report_agent.py` 把 score_band、pain_point、market signal 放入 prompt 和 fallback 输出 |

一句话记忆：
> 现在项目的核心不是“几个 agent”，而是把高考志愿里人的焦虑和市场博弈做成可计算、可传递、可审计的推荐信号。

## 0.1 2025 回测层已开始落地

为了把项目从“能推荐”推进到“能判卷”，现在已经新增 `backend/src/evaluation/` 作为独立评测层。它的原则是：推荐时只允许使用 2021-2024 历史数据、2025 招生计划和 2025 一分一段表；志愿表冻结后，才读取 2025 实际投档和组内专业录取结果做事后评估。

当前落地文件：

| 文件 | 作用 |
| --- | --- |
| `evaluation/schemas.py` | 定义真实专业组 outcome、单行志愿 outcome、整张志愿表 backtest result |
| `evaluation/metrics.py` | 计算是否进组、首命中行、组内专业命中、黑名单命中、尾部调剂、浪费分 |
| `evaluation/backtest_2025.py` | 加载 2025 实际结果 CSV，并对冻结志愿表做判卷 |
| `evaluation/baselines.py` | 构造 probability-only、safe-first、tight-rank、no-tradeoff baseline |
| `test_backtest_2025_smoke.py` | 验证首命中和组内专业分配判卷逻辑 |

第一版重点不是把所有数据源一次性接完，而是先把回测 contract 固定下来：

```text
VolunteerPlan + ActualMajorGroupOutcome + user_rank
-> PlanBacktestResult
-> BacktestAggregateMetrics
```

下一步要做的是把你手头的 2025 实际录取和组内专业数据整理成 `ActualMajorGroupOutcome` 能读取的格式，然后批量跑 full system 和 baseline / ablation。

一句话记忆：
> 2025 真实数据不能进入推荐，只能在志愿表冻结后作为判卷标签，这样项目才有干净的时间切分回测。

## 1. 当前共识

这个项目已经有一定实现基础：FastAPI 接入、LangGraph supervisor、用户画像、专业组候选生成、录取概率估计、冲稳保划分、advisor 审查、report 生成、critic 回退和 trace 记录都已经存在。现在最需要优化的不是继续堆 agent，而是把项目刻画得更清楚：它到底解决什么问题、核心链路是什么、推荐系统范式怎么迁移、LLM 在哪里发挥作用、哪些风险被显式建模。

一句话记忆：

> 现在缺的不是概念数量，而是清晰的问题定义、模块边界和证据链。

## 2. 最准确的项目定位

推荐定位：

> 这是一个面向高考志愿填报的高风险决策推荐 harness。它把院校专业组作为 item，把考生画像作为 user，把省份机制、招生计划、历史位次、专业组结构和热门叙事作为 context，通过多路召回、粗排、精排、组合重排和 LLM 审计解释，生成可解释、可回退、可评估的志愿方案。

不要优先说：

> 我做了一个多 agent 高考志愿系统。

应该说：

> 我把高考志愿建模成一个机制约束下的专业组推荐问题，并用 agent harness 管住推荐、审计、解释和回退。

一句话记忆：

> 专业组推荐是业务核心，agent harness 是工程外壳，LLM 是解释和审计能力。

## 3. 为什么这个问题不是普通推荐

高考志愿和电商/短视频推荐不同：

| 维度 | 普通推荐 | 高考志愿 |
| --- | --- | --- |
| 决策频率 | 高频、多次反馈 | 低频、几乎一次性 |
| 目标 | 点击、转化、停留 | 录取、适配、风险、后悔最小化 |
| item | 商品、视频、广告 | 院校专业组 |
| feedback | 点击、购买、观看 | 专家评分、录取结果、约束满足、后悔风险 |
| 错误成本 | 通常较低 | 极高，影响教育路径 |
| 排序结果 | top-k 展示 | 组合方案，必须有冲稳保结构 |
| 解释需求 | 可选 | 必须解释风险和不确定性 |

一句话记忆：

> 普通推荐优化偏好，高考志愿推荐还要优化机制约束和后悔风险。

## 4. 推荐系统范式应该怎么迁移

传统搜广推链路是：

> 多路召回 -> 粗排 -> 精排 -> 重排 -> 展示反馈

高考志愿版本应改成：

> 专业组多路召回 -> 风险粗排 -> 概率与认知精排 -> 组合重排 -> critic 审计 -> 结构化报告

| 阶段 | 高考志愿实现 | 输出 |
| --- | --- | --- |
| Recall | 位次窗口、稳定保底、小计划机会、专业偏好、城市偏好、反热门召回 | candidate pool |
| Coarse Rank | 用便宜特征过滤明显不合适专业组 | top 100 |
| Fine Rank | Monte Carlo 概率、Z-score、quota 波动、调剂风险、拥挤风险 | ranked candidates |
| Portfolio Rerank | 冲稳保约束、多样性、黑名单、调剂风险、机会/安全平衡 | final slate |
| Critic | 检查保底、黑名单、证据、报告完整性 | pass / reroute |
| Report | 输出方案、风险、认知纠偏和人工复核点 | user-facing report |

一句话记忆：

> 不是单点 top-k，而是“召回、排序、组合、审计”的专业组推荐链路。

## 5. 你的项目更像什么

更准确说，它是：

> 场景特征工程 + 粗排精排 + 组合优化 + LLM 审计解释。

其中：

| 部分 | 项目对应 |
| --- | --- |
| 场景特征工程 | 位次差、Z-score、quota、专业组结构、调剂风险、热门拥挤、后悔风险 |
| 粗排精排 | 先便宜筛选，再精算概率和风险 |
| 组合优化 | 不取 top-k，而是形成冲稳保组合 |
| LLM harness | 抽取用户偏好、纠正误解、生成解释、critic 审计 |

一句话记忆：

> 核心竞争力不是模型多大，而是把高考志愿的风险变量工程化。

## 6. 应该刻画清楚的核心概念

### 6.1 专业组是最小 item

院校不是最小决策单元，专业组才是。因为投档、选科、调剂和录取位次都围绕专业组发生。

面试说法：

> 我不按学校推荐，而按院校专业组推荐，因为用户承担的是专业组内录取和调剂风险。

### 6.2 quota 同时表示稳定性和机会性

招生人数多通常更稳定，适合做 safe anchor；招生人数少通常波动更大，可能产生捡漏，也可能滑档。

需要拆成：

```text
quota_stability_score
variance_opportunity_score
```

面试说法：

> 小计划不是坏，而是高波动；大计划不是绝对好，而是更稳定。系统要决定它在组合里扮演机会还是安全垫。

### 6.3 热门拥挤是反身性风险

往年位次、机构推荐、短视频叙事和家长焦虑会推高某些学校/专业组。今年分数线上涨不一定代表真实价值上涨，也可能代表群体预期拥挤。

需要新增：

```text
crowding_risk
acceleration_signal
crowding_adjusted_prob
```

面试说法：

> 我希望系统能区分真实价值提升和报考拥挤推高。

### 6.4 用户偏好不等于真实偏好

用户说想学 AI、金融、法学、医学，可能是基于职业误解、学校 title 焦虑、亲友压力或短视频叙事。

需要新增：

```text
misconception_risk
emotion_regret_risk
preference_confidence
```

面试说法：

> 我不直接相信用户表层偏好，而是识别偏好背后的假设和风险。

### 6.5 合理妒忌是后悔风险的理论支点

合理妒忌说明用户不只关心自己能否录取，也关心是否被机制、信息或策略导致错配。

需要新增：

```text
regret_proxy
justified_envy_proxy
undermatch_risk
```

面试说法：

> 我把 ex-post 后悔风险作为评估信号，而不是只看录取概率。

## 7. 当前实现基础与缺口

| 已有基础 | 当前问题 | 优化方向 |
| --- | --- | --- |
| `GameAgent` 已生成专业组候选 | 函数过大，推荐链路不够清晰 | 拆成 recall / coarse_rank / fine_rank / portfolio_rerank |
| 已读取 `quota` | 没有作为 row 字段输出 | 加入 `MajorGroupRow.quota` 和 quota_bucket |
| 已有概率估计和 Z-score | 小计划主要被当惩罚 | 同时计算稳定性和机会性 |
| 已有 advisor / critic | 审查点偏流程质量 | 加入专业组结构、热门拥挤、后悔风险审查 |
| 已有 report | 报告解释偏录取概率 | 新增专业组、招生计划、拥挤、误解、情绪风险解释 |
| 已有 trace | 还没成为正式 eval harness | 规范 run event，做离线 replay 和 metrics |

一句话记忆：

> 不是推倒重写，而是把已有 GameAgent 拆清楚，把风险特征显式化。

## 8. 推荐的工程改造路线

### P0：重构推荐核心

把 `game_agent.py` 从大函数拆成：

```text
recommendation/
  recall.py
  coarse_rank.py
  fine_rank.py
  portfolio_rerank.py
  features.py
  schemas.py
```

GameAgent 只负责 orchestrate：

> recall -> coarse rank -> fine rank -> portfolio rerank -> GameMatrix

### P1：补齐专业组和 quota 特征

新增字段：

```text
quota
quota_bucket
quota_stability_score
variance_opportunity_score
major_group_dispersion
adjustment_range_risk
recommendation_role
```

同时修正：

> 当前“小招生规模”不要用 `major_count <= 3` 判断，应该基于 `quota`。

### P2：加入认知与情绪风险层

新增模块：

```text
perception/
  crowding_risk.py
  misconception.py
  emotion_regret.py
```

输出：

```text
CrowdingRisk
MisconceptionRisk
EmotionRisk
```

### P3：做 evaluation harness

新增离线评估：

```bash
python -m evaluation.run_eval --cases data/eval_cases.jsonl
```

指标：

```text
constraint_pass_rate
safe_anchor_coverage
blacklist_warning_recall
quota_explanation_coverage
crowding_risk_detection
report_schema_valid_rate
critic_reroute_rate
avg_latency
```

### P4：报告结构升级

最终报告不只写推荐列表，应该包括：

```text
1. 冲稳保组合总览
2. 专业组与招生计划解释
3. 小计划机会与高波动风险
4. 大计划稳定安全垫
5. 热门拥挤与反身性风险
6. 专业误解纠偏
7. 情绪与后悔风险
8. 人工复核事项
```

一句话记忆：

> 工程上先拆 Game，再补 quota，再加认知风险，最后做 eval harness。

## 9. 新版项目图

建议主图只画：

```text
Input Adapter
-> Recommendation Harness
-> Feature & Risk Layer
-> Ranking Pipeline
-> Portfolio & Evaluation Gate
-> Structured Report
```

展开后：

```text
UserProfile
-> Multi-channel Recall
-> Coarse Rank
-> Fine Rank
-> Portfolio Rerank
-> Advisor / Critic
-> Report
```

其中 `Feature & Risk Layer` 是你的特色：

```text
rank / probability / z-score
quota stability / variance opportunity
major group adjustment risk
crowding / reflexivity risk
misconception / emotion regret risk
```

一句话记忆：

> 新图突出推荐链路和风险特征，不突出 agent 数量。

## 10. 面试最终表述

30 秒版本：

> 我的项目不是单纯用 LLM 生成志愿，而是把高考志愿建模成专业组级推荐系统。用户是考生画像，item 是院校专业组，context 是省份机制、招生计划、历史录取和热门叙事。系统先多路召回候选，再粗排筛掉明显不合适专业组，精排计算录取概率、Z-score、quota 波动、调剂风险和热门拥挤风险，最后做组合重排形成冲稳保方案。LLM 主要负责画像抽取、专业误解纠偏、报告解释和 critic 审计。

1 分钟版本：

> 传统推荐系统一般有召回、粗排、精排和重排。我把这个范式迁移到高考志愿场景，但目标不是点击率，而是录取概率、偏好匹配、风险可控和后悔最小化。实现上，我把院校专业组作为 item，围绕位次差、录取概率、Z-score、招生计划人数、专业组调剂范围、历史波动、热门拥挤和用户情绪风险做特征工程。粗排阶段用便宜特征找出可行候选，精排阶段再做 Monte Carlo 概率和风险计算，最后不是取 top-k，而是做冲稳保组合优化，并用 advisor / critic 检查保底、黑名单、证据和报告完整性。

一句话记忆：

> 我的核心不是“agent 多”，而是把高考志愿做成“场景特征工程 + 粗排精排 + 组合重排 + LLM 审计解释”的高风险决策推荐系统。

## 11. 下一步最值得做的 5 个提交

1. 拆分 `game_agent.py`，建立 `recommendation/recall.py`、`coarse_rank.py`、`fine_rank.py`、`portfolio_rerank.py`。
2. 修改 `MajorGroupRow`，加入 quota、quota_bucket、stability/opportunity/risk 字段。
3. 修正“小招生规模”逻辑，使用 `quota` 而不是 `major_count`。
4. 新增 report section：专业组与招生计划解释、热门拥挤风险、专业误解纠偏。
5. 新增 `evaluation/run_eval.py`，用固定 case 回放并输出核心指标。

一句话记忆：

> 先做能证明工程品味的重构和 eval，不急着继续加模型。
