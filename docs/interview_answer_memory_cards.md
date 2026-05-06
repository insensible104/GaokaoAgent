# GaokaoAgent 面试最终复习包

这是面试准备的唯一主文件。它合并了项目介绍、回答记忆卡、代码证据、推荐算法迁移、RL/GRPO 追问和高风险边界。

核心原则：

> 先承认边界，再展示迁移能力。不要把项目硬说成传统推荐、完整生成式推荐或稳定 RL 系统；要讲成“高约束决策推荐 + graph-orchestrated multi-agent + supervisor 调度优化”。

## 0. 临场总线：先把项目放到可信位置

| 面试官可能听到的标签 | 你的稳妥说法 | 证据锚点 | 主动边界 |
| --- | --- | --- | --- |
| 生成式推荐 | 高约束决策推荐里的生成式解释和调度增强 | 候选来自结构化数据，报告和反思由 LLM 生成 | 不说端到端生成 item 或 next-item prediction |
| Multi-Agent | centralized supervisor 下的角色化协作系统 | supervisor、advisor、critic、coordinator、message bus | 不说完全自治或去中心化协商 |
| RL / GRPO | orchestration-level policy optimization 探索 | rollout trace、pairwise preference、reward model、runtime hook | 不说稳定线上收益或 RL 直接选学校 |
| 推荐算法岗位迁移 | 候选生成、重排、slate、约束、离线评估的相邻经验 | quant engine、probability、Monte Carlo、critic、rubric | 不装 CTR/CVR 工业经验 |

一句话记忆：

> 先把标签降到可信范围，再用代码链路证明你知道怎么做实。

## 1. 面试前 15 分钟背诵版

1. 这不是 LLM 出名单，而是结构化推荐加 supervisor 决策闭环。
2. 不装传统推荐，讲候选、重排、约束、评估的迁移能力。
3. 不是生成 item，而是生成可解释、可审查的决策方案。
4. 骨架是 workflow，决策是 supervisor，协作有 advisor 和 critic。
5. RL 不选学校，RL 选下一步动作。
6. GRPO 链路打通了，但收益还没被大规模证明。
7. proxy reward 能做比较，不能当真实满意度。
8. 学校来自数据，解释来自 LLM。
9. 100 例是离线 rubric，不是线上结论。
10. 先评测，再数据，再训练，最后安全接入。

## 2. 90 秒项目介绍

这个项目解决的是高考志愿填报这种高风险、长路径、多约束决策问题。我没有让大模型直接输出学校列表，而是把系统拆成结构化推荐链路和 agent 调度链路。推荐侧先把用户分数、位次、选科、地域、专业和风险偏好结构化，再基于历史录取数据、招生计划和一分一段表生成候选，用录取概率、蒙特卡洛和组合筛选控制冲稳保分布。Agent 侧用 LangGraph 做 centralized supervisor orchestration，包含画像、候选生成、深度调研、报告、critic，以及 game 之后的三路并行顾问评审。我的进一步探索是把 supervisor 的调度抽象成有限状态、有限动作的决策问题，收集 rollout trace，构造 pairwise preference 和 proxy reward，训练 reward model / GRPO，并通过 runtime hook 接回 supervisor。当前主链路和训练接线已经打通，下一步重点是更系统的 benchmark 和 learned policy 稳定收益验证。

一句话记忆：

> 结构化推荐保证 grounding，multi-agent 负责协作审查，RL 探索只优化 supervisor 下一步动作。

## 3. 回答公式

每个回答按四步走：

1. **结论**：先给一句明确判断。
2. **证据**：接一个代码/模块/实验锚点。
3. **边界**：主动说明不能夸大的地方。
4. **迁移**：说明它和目标岗位能力的关系。

一句话记忆：

> 先定性，再给证据，再降边界，最后接岗位。

## 4. 高频问答记忆卡

### Q1：你这个项目到底是什么？

推荐回答：

> GaokaoAgent 是一个面向高考志愿规划的 graph-orchestrated multi-agent decision system。它不是让 LLM 单轮生成学校名单，而是用结构化数据做候选生成和风险评估，再用 supervisor 调度画像、推荐、深度调研、报告和 critic 审查，形成可回退的长路径决策闭环。

一句话记忆：

> 不是 LLM 出名单，而是结构化推荐加 supervisor 决策闭环。

不要说：

> 这是一个完全自动的高考志愿 AI 产品。

### Q2：这个项目最核心的技术亮点是什么？

推荐回答：

> 核心亮点是把高考志愿这种高风险决策拆成结构化推荐链路和多智能体调度链路。推荐链路负责候选和风险 grounding，agent 链路负责偏好理解、证据补全、方案解释和审查回退，RL 探索则落在 supervisor 的下一步动作选择上。

一句话记忆：

> 结构化推荐负责准，agent 调度负责稳，RL 探索负责下一步怎么走。

不要说：

> 核心亮点是我用了很多 agent 和 GRPO。

### Q3：它现在是什么完成度？

推荐回答：

> 主决策链、多智能体协议、并行评审和 orchestration alignment 接线已经成型，可以作为 research prototype 展示。但它还不是生产级系统，仍缺大规模 benchmark、真实用户反馈、线上监控和更强的 source reliability。

一句话记忆：

> 主链路可演示，生产化还差 benchmark、反馈和监控。

不要说：

> 项目已经生产就绪。

### Q4：你没有传统推荐经历，为什么适合推荐算法岗位？

推荐回答：

> 我没有做过完整工业推荐链路，比如召回、粗排、精排、CTR/CVR 和线上 A/B。但这个项目里有推荐系统相邻能力：候选生成、用户偏好建模、slate reranking、约束优化、风险控制和离线评估。我能把这些经验迁移到推荐系统，并且会补齐工业推荐的模型和指标基础。

一句话记忆：

> 不装传统推荐，讲候选、重排、约束、评估的迁移能力。

不要说：

> 我这个项目就是推荐算法项目。

### Q5：这个项目和生成式推荐有什么关系？

推荐回答：

> 它不是主流 LLM4Rec 里直接生成 item ID 或 next item 的生成式推荐。更准确地说，它是高约束决策场景里的生成式推荐相邻实践：LLM/agent 负责偏好理解、证据补全、方案修正和解释生成，最终候选仍由结构化数据和规则 grounding。

一句话记忆：

> 不是生成 item，而是生成可解释、可审查的决策方案。

不要说：

> 我做了完整的生成式推荐模型。

### Q6：如果映射到推荐系统链路，它对应哪几块？

推荐回答：

> 用户画像对应 user modeling，量化引擎对应 candidate generation，风险和偏好打分对应 ranking/reranking，冲稳保组合对应 slate optimization，报告和解释对应 explainable recommendation，critic 对应 safety/rule checking。

一句话记忆：

> 画像是 user，候选是 recall，排序是 rerank，志愿表是 slate，critic 是 safety。

不要说：

> 它和推荐系统一模一样。

### Q7：你怎么看 LLM 在推荐系统里的作用？

推荐回答：

> 我不认为 LLM 应该直接替代排序模型。更合理的位置是做偏好理解、长文本/多源信息理解、候选补充、解释生成和某些重排控制；真正的 item grounding、行为建模和在线收益仍需要可靠的数据、排序模型和 A/B 验证。

一句话记忆：

> LLM 做理解和解释，排序收益仍靠数据和评测。

不要说：

> LLM 可以直接取代传统推荐模型。

### Q8：如果抖音推荐问你 CTR/CVR，你怎么接？

推荐回答：

> 我会先承认这个项目没有做 CTR/CVR 预估，然后把经验迁移到可比问题：我做的是显式偏好和规则约束下的候选重排，工业推荐里的 CTR/CVR 是从用户行为中学习隐式偏好。两者目标不同，但都需要特征建模、负样本、排序目标、离线指标和线上验证。

一句话记忆：

> 我没做 CTR/CVR，但懂偏好建模和排序评估要怎么迁移。

不要说：

> 高考推荐里的录取概率就等价于 CTR。

### Q9：为什么这不是普通 workflow？

推荐回答：

> 执行骨架确实是 LangGraph workflow，但它不是固定串行流程。系统有 centralized supervisor、显式消息协议、局部记忆、并行 advisor 评审和 critic 回退，关键阶段由 supervisor 根据状态和反馈决定下一步。

一句话记忆：

> 骨架是 workflow，决策是 supervisor，协作有 advisor 和 critic。

不要说：

> 它完全不是 workflow。

### Q10：为什么算 multi-agent，而不是多个 prompt？

推荐回答：

> 因为不同 agent 有独立职责和不同判断角度，并通过结构化消息、局部记忆和 deliberation summary 协作。尤其在候选生成后，risk guardian、opportunity advocate 和 evidence guardian 会并行评审，再由 coordinator 汇总给 supervisor。

一句话记忆：

> 多 agent 的证据是角色、消息、记忆、并行评审和汇总裁决。

不要说：

> 因为我有很多 agent 文件。

### Q11：为什么采用 centralized supervisor，而不是完全自治？

推荐回答：

> 因为高考志愿是高风险场景，系统需要可控、可审计、可回放。centralized supervisor 限制动作空间和回退路径，虽然没有完全自治那么灵活，但更适合安全和工程落地。

一句话记忆：

> 高风险场景先要可控，再谈自治。

不要说：

> 去中心化多 agent 一定更高级。

### Q12：RL 到底体现在哪里？

推荐回答：

> RL 不直接优化学校名单，也不是训练所有 agent，而是优化 supervisor 的 next-action selection。比如是否检索、是否深度调研、是否反思、审查失败后回退到哪里、什么时候停止。

一句话记忆：

> RL 不选学校，RL 选下一步动作。

不要说：

> RL 让系统学会自动填报最优志愿。

### Q13：状态、动作、奖励、终止怎么定义？

推荐回答：

> 状态是当前阶段、已有产物、候选数量、冲稳保分布、critic issue、retry 和 advisor 共识；动作是有限节点级动作，如 game、research、report、critic、END；奖励是 critic 通过和可交付结果加分，retry、issue、过长 trace 扣分；终止来自审查通过、预算耗尽或循环上限。

一句话记忆：

> 状态看进展，动作选节点，奖励看质量和成本，终止看通过或预算。

不要说：

> 状态就是完整对话，动作就是让模型自由规划。

### Q14：GRPO 现在做到什么程度？

推荐回答：

> GRPO-compatible 数据、训练脚本、HF Jobs 入口和 runtime hook 已经准备好，但我不会说它稳定替代 heuristic supervisor。当前更成熟的是 rollout、preference、reward model 和 evaluation 链路，GRPO 是进一步策略优化路径。

一句话记忆：

> GRPO 链路打通了，但收益还没被大规模证明。

不要说：

> GRPO 已经稳定提升线上效果。

### Q15：reward model 是不是主策略？

推荐回答：

> 不是。reward model 当前更像 candidate action reranker，只在受控条件下辅助 supervisor 打分。默认主干仍是 heuristic-first，learned policy 是 controlled augmentation。

一句话记忆：

> reward model 是辅助重排，不是接管系统。

不要说：

> reward model 控制了整个 supervisor。

### Q16：reward 靠不靠谱？

推荐回答：

> 当前 reward 是 proxy reward，不是真实业务 reward。它把 critic 通过、可交付结果、retry、issue 和 trace length 这些工程信号组合起来，适合离线比较和保守 rerank，但不能直接代表用户长期满意度。

一句话记忆：

> proxy reward 能做比较，不能当真实满意度。

不要说：

> reward 提升就代表真实业务提升。

### Q17：如何评估 learned policy 是否有效？

推荐回答：

> 当前评估分两层：rollout 级看 avg reward、approval rate、success rate、trace length、retry count；pairwise 级看 ranker 或 reward model 是否能区分 chosen/rejected action。现有日志样本小，只能证明评测链路跑通，不能证明稳定线上收益。

一句话记忆：

> rollout 看流程质量，pairwise 看动作偏好，小样本只证明链路。

不要说：

> 现有评测已经证明 learned policy 稳定更好。

### Q18：候选院校怎么生成？

推荐回答：

> 候选不是 LLM 生成的，而是基于历史录取数据、招生计划、一分一段表和用户约束检索出来的。LLM/agent 主要参与偏好理解、解释生成、调研补证和审查修正。

一句话记忆：

> 学校来自数据，解释来自 LLM。

不要说：

> 模型直接生成候选学校。

### Q19：100 例模拟评审应该怎么讲？

推荐回答：

> 我会把它讲成小规模离线 rubric 评审，用来检查方案完整性、风险覆盖、解释质量和约束一致性。它能说明系统有可交付性，但不能外推成线上稳定收益或真实用户满意度。

一句话记忆：

> 100 例是离线 rubric，不是线上结论。

不要说：

> 100 例专家盲评证明系统已经成熟。

### Q20：deep research fallback 算不算真正 research？

推荐回答：

> 要分模式。有外部检索时，它是 evidence-backed research；没有检索或来源不足时，它只是 graceful degradation 的启发式报告。面试里我会明确区分 source quality，不把 fallback 包装成强证据 research。

一句话记忆：

> 有检索是 research，没证据是 fallback。

不要说：

> fallback 报告也同样可靠。

### Q21：critic 做了什么？

推荐回答：

> critic 是统一质量闸门，检查风险覆盖、报告一致性、规则问题和是否需要 reroute。它很大程度是规则化和结构化审查，不是开放式自治评审，这在高风险场景反而更可审计。

一句话记忆：

> critic 不是炫技 agent，是风险闸门。

不要说：

> critic 像人类专家一样全面判断。

### Q22：这个项目最大不足是什么？

推荐回答：

> 最大不足是 learned policy 的稳定收益验证还不充分，其次是真实分布 preference 数据不足、deep research 来源可信度不够强、跨省规则泛化还需要重构数据和规则层。

一句话记忆：

> 短板是评测、真实偏好、来源可信度和泛化。

不要说：

> 主要不足只是 UI 还可以更好。

### Q23：如果继续做三个月，你会怎么做？

推荐回答：

> 我会先做 benchmark 和 case coverage，再扩充真实或半真实 preference 数据，重训 reward model / ranker，最后增强 source reliability 和 runtime safety guard，让 learned policy 只在高置信场景下逐步承担更多调度权重。

一句话记忆：

> 先评测，再数据，再训练，最后安全接入。

不要说：

> 继续把 agent 数量加多。

### Q24：如果面试官质疑你是在包装项目，怎么回应？

推荐回答：

> 我会承认这个项目不是传统推荐，也不是完整线上 RL 系统。我的价值在于把高约束推荐、agent 协作和调度优化做成了可运行原型，并且清楚知道哪些 claim 已经有证据、哪些还只是探索。

一句话记忆：

> 不硬撑标签，讲清证据和边界。

不要说：

> 这是面试官没理解我的项目。

### Q25：如果你担心这是 KPI 面，应该怎么准备？

推荐回答：

> 不要按 KPI 面准备，也不要自我削弱。按真实面试准备，重点把项目讲清楚、把推荐算法基础补上、把不会的工业细节诚实说成正在补齐。

一句话记忆：

> 按真实面试准备，不按 KPI 面下注。

不要说：

> 反正可能是 KPI 面，我随便讲讲。

## 5. 代码证据速查

| Claim | 推荐表述 | 主要证据 | 风险边界 |
| --- | --- | --- | --- |
| 多智能体架构 | 基于 LangGraph 构建 centralized supervisor 下的 graph-orchestrated multi-agent system。 | `backend/src/graph/dual_loop_supervisor.py`, `backend/src/agents/*` | 不说 fully autonomous / decentralized MAS。 |
| 显式 agent 协作 | 系统具备消息协议、局部记忆、并行 advisor 和 coordinator 汇总。 | `backend/src/models/agent_communication.py`, `backend/src/utils/agent_bus.py`, `backend/src/agents/deliberation_agents.py` | 最强协作主要发生在 game 之后。 |
| 结构化推荐链路 | 推荐主链路基于真实数据、概率建模和组合筛选，LLM 主要负责解释和报告。 | `backend/src/agents/game_agent.py`, `backend/src/engines/quant_engine.py`, `backend/src/engines/probability.py`, `backend/src/engines/monte_carlo_sim.py` | 不说 LLM 端到端生成可靠志愿表。 |
| 深度调研分支 | 支持 Plan-Execute-Reflect 风格的研究子图和 research-only 报告输出。 | `backend/src/subgraphs/deep_research.py`, `backend/src/agents/deep_research_agent.py`, `backend/src/agents/report_agent.py` | fallback 模式证据强度较弱。 |
| Supervisor 调度优化 | 把 supervisor next-action selection 抽象成有限状态、有限动作的决策问题。 | `backend/src/rl/supervisor_policy.py`, `backend/src/models/orchestration.py` | 不说训练了整个 agent system。 |
| Alignment / RL 链路 | 已打通 rollout trace、pairwise preference、reward model、GRPO 数据和训练脚本。 | `backend/src/rl/orchestration_data_pipeline.py`, `backend/src/rl/orchestration_alignment.py`, `backend/src/rl/orchestration_trl_utils.py` | 说链路打通，不说稳定收益已证明。 |
| Runtime learned hook | learned ranker、LLM supervisor 和 reward model reranker 可以接入 supervisor。 | `backend/src/rl/supervisor_policy.py`, `backend/src/rl/reward_model_scorer.py` | 默认主干仍是 heuristic-first。 |
| 评测链路 | 已有策略评测脚本，能比较 reward、approval、trace length、retry 等指标。 | `backend/scripts/evaluate_orchestration_policies.py`, `backend/logs/baseline_compare_eval.md` | 当前日志样本很小，不能外推为线上稳定收益。 |
| 安全与审查 | critic 作为统一质量闸门，负责风险审查、合规检查和回退建议。 | `backend/src/agents/critic_agent_enhanced.py`, `backend/src/utils/reflexion.py` | critic 很大程度是规则化审查。 |

## 6. 高风险追问短答

| 追问 | 稳妥回答 | 一句话记忆 |
| --- | --- | --- |
| 你这是不是 workflow？ | 是图 workflow 骨架，但关键阶段有 supervisor 动态调度、并行评审和审查回退。 | 骨架 workflow，决策 supervisor。 |
| 你是不是做了完整 RLHF？ | 不是大规模通用 RLHF，是 orchestration-level preference learning / reward modeling / policy optimization 探索。 | RLHF 只落在调度层。 |
| GRPO 有稳定收益吗？ | 训练和接线链路已打通，稳定收益还需要更大 benchmark 验证。 | 链路有，收益未证。 |
| reward 是真实业务目标吗？ | 不是，是 proxy reward，只能作为离线比较和保守 rerank 的信号。 | proxy 不是 business。 |
| learned policy 默认在线吗？ | 默认仍是 heuristic-first，learned ranker / reward model 是可选增强位。 | heuristic 主干，learned 增强。 |
| 为什么不直接自由 Agent Planner？ | 高风险场景需要可控、可审计和可回放，所以限制动作空间。 | 高风险先可控。 |
| 最大短板是什么？ | learned policy 评测不足、真实分布 preference 数据不足、deep research 来源可信度还要加强。 | 短板是评测、数据、可信度。 |
| 和推荐算法有什么关系？ | 候选生成、slate reranking、约束优化、风险控制和离线评估相邻，但不是传统 CTR/CVR 推荐链路。 | 讲相邻能力，不装传统推荐。 |

## 7. 推荐算法岗位补课和迁移

### 7.1 今天只记这 6 组词

1. 召回、粗排、精排、重排、混排。
2. CTR/CVR、AUC、logloss、NDCG、Recall@K。
3. 双塔召回、ANN、hard negative、负采样。
4. Wide&Deep、DeepFM、DCN、DIN/DIEN 的基本思想。
5. 位置偏差、曝光偏差、样本选择偏差。
6. A/B test、显著性、长期指标和短期指标冲突。

一句话记忆：

> 推荐补课先补链路、指标、召回、排序、偏差和 A/B。

### 7.2 和本项目的迁移说法

| 推荐系统能力 | 本项目对应经验 | 面试说法 |
| --- | --- | --- |
| User modeling | 用户画像和偏好抽取 | 我做过显式偏好结构化，隐式行为建模还需要补。 |
| Candidate generation | 基于数据和约束生成候选院校 | 我理解候选生成要先保证覆盖和可用性。 |
| Ranking / reranking | 风险、偏好、规则下的方案重排 | 我做过约束重排，但不是 CTR 预估。 |
| Slate optimization | 冲稳保组合和方案平衡 | 我接触过 slate 级别目标，而不是只看单 item。 |
| Offline evaluation | rubric、proxy reward、pairwise eval | 我知道离线评估不能直接等同线上收益。 |
| Explainability | 报告生成和风险说明 | 我做过解释生成，但会区分解释质量和排序质量。 |

一句话记忆：

> 把项目映射到推荐链路，但每一步都主动说明差异。

## 8. Multi-Agent / RL 深挖附录

这一节只在面试官追问“强化学习具体怎么做”“multi-agent 具体怎么协作”时展开。核心策略是：先把问题抽象讲清楚，再讲数据怎么来、模型怎么训、运行时怎么接、为什么不夸大收益。

### D1：你说的 RL 问题，MDP 是怎么定义的？

推荐回答：

> 我把 supervisor 调度抽象成一个受限 MDP。state 不是原始对话，而是结构化 observation，比如当前阶段、是否已有 profile / game matrix / report、候选数量、critic issue 数、retry count、research loop count、advisor 共识等。action 是有限节点级动作，比如进入 game、deep research、report、critic 或 END。reward 是 proxy reward，鼓励短轨迹内产出可通过 critic 的结果，惩罚过多 retry、问题数和无效长轨迹。terminal 是 critic 通过、预算耗尽或循环达到上限。

一句话记忆：

> state 是结构化进展，action 是选下个节点，reward 是质量减成本，terminal 是通过或预算。

别说：

> 我把所有对话直接丢给 RL，让它自由规划。

### D2：为什么 action space 要这么小？

推荐回答：

> 因为这是高风险决策场景，开放式 agent planner 很难评估，也容易不可控。我把 action space 限制成节点级动作，是为了让状态转移可解释、轨迹可回放、reward 可计算，也降低 learned policy 钻 proxy reward 的空间。

一句话记忆：

> 动作小不是弱，是为了可控、可评测、可回放。

别说：

> action space 小只是因为实现简单。

### D3：一次 rollout trace 记录什么？

推荐回答：

> 每次 supervisor 做决策时，我会记录当前 stage、结构化 observation、candidate actions、heuristic 或 learned policy 选择的 action、rationale、后续 agent 执行结果、critic feedback、retry 和最终 reward proxy。这样一个 case 会形成多步 trajectory，后面可以导出 pairwise preference 或 GRPO task。

一句话记忆：

> trace 记录“看到什么、可选什么、选了什么、结果怎样、奖励多少”。

别说：

> trace 只是存了日志。

### D4：pairwise preference 是怎么构造的？

推荐回答：

> 对每个 supervisor 决策点，我会把实际选择或高 reward 轨迹中的 action 作为 chosen，把同一 state 下的其他可行动作或导致更差结果的动作作为 rejected。这个 pairwise 数据可以用于训练 lightweight action ranker 或 reward model，目标是让模型在同一 observation 下更偏向质量更高、成本更低的下一步动作。

一句话记忆：

> 同一状态下，好动作做 chosen，差动作做 rejected。

别说：

> preference 全靠人工主观标注。

### D5：reward proxy 具体有哪些项？

推荐回答：

> reward proxy 主要由正向质量信号和成本惩罚组成。正向包括 critic approve、产出 report / game matrix / research report；负向包括 retry count、critic issue 数、trace length 过长、negative step ratio。最后会裁剪到固定范围，避免极端值主导训练。它是工程代理目标，不是真实用户满意度。

一句话记忆：

> 通过和产出加分，重试、问题和长轨迹扣分。

别说：

> 这个 reward 就是真实业务收益。

### D6：reward model 怎么训练、怎么用？

推荐回答：

> reward model 用 pairwise preference 训练，输入是 observation 加 candidate action 的文本或结构化描述，目标是让 chosen action 的分数高于 rejected action。运行时它不直接控制系统，而是对 supervisor 的 candidate actions 做 rerank；只有在分数 margin 足够明确时才建议 override，默认仍保留 heuristic policy。

一句话记忆：

> reward model 学会给动作打分，运行时只做受控 rerank。

别说：

> reward model 是线上主策略。

### D7：GRPO 在这里怎么用？

推荐回答：

> GRPO 用在 supervisor policy 的动作选择探索上，而不是直接生成学校名单。我把每个任务转成 prompt：给定 observation 和 allowed actions，让 policy 生成一个 action；reward function 根据 proxy reward、critic 结果和轨迹成本打分。GRPO 的作用是用 group-relative 的方式比较多个候选动作/轨迹，更新策略倾向。当前我更强调 GRPO-compatible 数据、训练脚本和接线已经打通，不说它稳定带来收益。

一句话记忆：

> GRPO 选 supervisor action，不生成学校；链路打通，收益不夸大。

别说：

> GRPO 已经学会了最优志愿推荐。

### D8：为什么不用 PPO / DPO，非要 GRPO？

推荐回答：

> 这里不是非要 GRPO，而是把 GRPO 作为一种轻量策略优化范式来探索。相比 PPO，GRPO 不依赖单独 value model，工程上更轻；相比 DPO，它更贴近“给定状态和允许动作，按 reward 比较多个候选输出”的调度场景。但我不会说 GRPO 是唯一正确选择，后续也可以比较 ranker、DPO-style preference learning 和 heuristic baseline。

一句话记忆：

> GRPO 是轻量可试的策略优化路径，不是唯一解。

别说：

> GRPO 一定比 PPO/DPO 更好。

### D9：online policy hook 具体怎么接入？

推荐回答：

> supervisor 在每个关键 stage 先生成 allowed actions，然后默认 heuristic 会给一个 action。learned ranker / LLM supervisor / reward model reranker 可以读取同一份 observation 和 allowed actions，对候选动作重新打分。最终系统可以选择保持 heuristic，或者在 learned policy 置信度和 margin 足够时 override。这样能保证 learned policy 是可控增强，而不是直接放权。

一句话记忆：

> heuristic 先给动作，learned policy 只在候选集里重排。

别说：

> learned policy 可以任意调用任何 agent。

### D10：multi-agent 协作具体发生在哪里？

推荐回答：

> 最明确的协作发生在候选生成之后。game agent 产出候选方案后，risk guardian 看滑档和保底风险，opportunity advocate 看是否过于保守和机会空间，evidence guardian 看证据和规则支撑。三个 advisor 通过结构化消息写入意见，再由 coordinator 汇总成 deliberation summary，交回 supervisor 决定是 report、deep research 还是 reroute。

一句话记忆：

> game 产方案，三个 advisor 分别看风险、机会、证据，coordinator 汇总给 supervisor。

别说：

> 所有 agent 都在自由协商。

### D11：agent message / memory 有什么用？

推荐回答：

> message 用来做 agent 间的显式通信，比如谁在什么 stage 给谁发了什么建议、推荐什么 next action、confidence 多少。memory 用来保存单个 agent 的局部判断或失败经验。这样做比直接共享一段自然语言更可追踪，也方便后续把 trajectory 用于 preference 和 reward modeling。

一句话记忆：

> message 负责通信，memory 负责局部经验，trace 负责后续训练。

别说：

> memory 就是把聊天记录存起来。

### D12：coordinator 怎么汇总 advisor 意见？

推荐回答：

> coordinator 不做复杂自治协商，而是把各 advisor 的 action preference、confidence、risk/evidence/opportunity summary 汇总成结构化 deliberation summary。如果三个 advisor 都倾向 report，supervisor 可以直接进入报告；如果 risk 或 evidence 分歧强，就触发 deep research 或 reroute。

一句话记忆：

> coordinator 汇总偏好和置信度，不神化成自治辩论。

别说：

> coordinator 像人类委员会一样充分讨论。

### D13：你怎么防止 learned policy 学坏？

推荐回答：

> 主要靠四层限制：第一，action space 是有限节点级动作；第二，heuristic policy 仍是默认主干；第三，reward model 只做候选动作 rerank，不直接开放工具调用；第四，critic 是最终质量闸门，可以把不合格结果 reroute 或终止。这样即使 learned policy 不稳定，也不会完全接管系统。

一句话记忆：

> 有限动作、heuristic 主干、rerank 接入、critic 闸门。

别说：

> 模型自己会学会安全策略。

### D14：你现在的 RL 实验结果怎么讲？

推荐回答：

> 我会把现有结果讲成 small-sample sanity check：证明 rollout、pairwise、reward model 接线和 evaluation harness 能跑通。由于样本量小、case 分布不够真实，不能把 avg reward 或 approval rate 的提升外推成稳定线上收益。更严谨的下一步是扩大 case coverage，做 heuristic / ranker / reward reranker / GRPO 的分层对比。

一句话记忆：

> 现有实验证明链路，不证明稳定收益。

别说：

> 现在结果已经证明 RL 有明显提升。

### D15：如果继续做，你会怎么把 RL 做实？

推荐回答：

> 我会先建立 benchmark：覆盖不同分数段、风险偏好、专业偏好和信息缺失程度；然后扩充真实或半真实 preference 数据；再分别训练 action ranker、reward model 和 GRPO policy；最后做 ablation，对比 heuristic、ranker、reward reranker、GRPO 在 approval rate、trace length、retry、issue count 和人工 rubric 上的差异。

一句话记忆：

> 先 benchmark，再 preference 数据，再多策略对比。

别说：

> 直接加大模型和训练轮数。

### D16：如果面试官说“这还是规则系统”，怎么回应？

推荐回答：

> 我会承认它有规则系统成分，而且这是高风险场景里必要的。我的贡献不是去掉规则，而是把规则、结构化数据、agent 协作和可学习的 supervisor 调度接到同一个可回放闭环里。heuristic 提供稳定底线，learned policy 提供可验证的优化空间。

一句话记忆：

> 规则是安全底线，学习是可验证增强。

别说：

> 这不是规则，完全是智能体自主决策。

## 9. 临场深挖：把 RL 和 Multi-Agent 讲到代码级

这一节不是开场主动全讲，而是面试官持续追问时用。目标是给出“能落地、能承认边界、能继续实验”的技术回答。

### 9.1 如果让你白板画 RL，你怎么画？

推荐回答：

> 我会画成 supervisor 上的一层轻量 policy，而不是整个系统端到端 RL。每个决策点先从当前 graph state 抽取 observation，再枚举 allowed actions，例如 game、research、report、critic、END。heuristic policy 先给默认动作，learned ranker 或 reward model 只在 allowed actions 里重排。执行后记录 next state、critic feedback、retry、trace length 和最终 proxy reward，形成 rollout trace。训练侧先用 trace 构造 pairwise preference 和 reward model，再尝试 GRPO-style policy optimization。

一句话记忆：

> 白板只画 supervisor policy，不画端到端自动填报。

### 9.2 如果追问 state 为什么不直接用完整对话？

推荐回答：

> 完整对话可读性差、维度不稳定，也很难做动作归因。我更倾向用结构化 observation：当前 stage、profile 是否完整、候选数、冲稳保分布、critic issue 数、advisor 共识、retry count、research loop count、预算剩余等。这样 reward、ablation 和错误分析都更清楚，后面也可以把自然语言 summary 作为补充特征。

一句话记忆：

> state 要可归因，所以先结构化，再补自然语言。

### 9.3 如果追问 reward model 的训练细节？

推荐回答：

> 我会把同一 observation 下的动作比较转成 pairwise 样本，输入是 observation 加 candidate action，标签是 chosen / rejected。chosen 来自更高 proxy reward 的轨迹、critic approve 的路径，或者人工校准后的更合理动作；rejected 是同状态下导致更多 retry、更多 issue 或无效长路径的动作。训练目标不是预测真实满意度，而是让模型学会在局部调度点上区分更合理的下一步。

一句话记忆：

> reward model 学局部动作偏好，不学真实用户满意度。

### 9.4 如果追问 GRPO 的 objective？

推荐回答：

> 我不会硬背公式，而会讲清楚机制：对同一个 observation 采样多个候选 action 或 action rationale，分别跑 reward function 得到分数，再用 group-relative advantage 更新 policy，让高于组内平均的输出概率上升、低于平均的下降，同时用 KL 或规则约束避免偏离原始策略太远。这里的关键不是 GRPO 名字，而是我把任务转成了“同状态、多候选、按 reward 比较”的形式。

一句话记忆：

> GRPO 的抓手是同状态多候选比较，不是魔法训练。

### 9.5 如果追问 Multi-Agent 不是多个 prompt 的证据？

推荐回答：

> 我会从四个证据讲：第一，角色有不同目标函数，risk guardian 看风险，opportunity advocate 看机会，evidence guardian 看证据；第二，通信是结构化 message，不只是拼接 prompt；第三，coordinator 汇总 action preference、confidence 和理由；第四，supervisor 根据汇总结果决定 report、research 或 reroute。也就是说，多 agent 的价值是分工审查和可回放协作，不是 agent 数量。

一句话记忆：

> 多 agent 证据是角色目标、结构化通信、汇总裁决和可回放轨迹。

### 9.6 如果追问为什么不用完全自治 agent？

推荐回答：

> 高考志愿属于高风险决策，完全自治会让错误路径难以审计，也很难做离线评估。我选择 centralized supervisor，是为了把每一步限制在可解释的 action space 里；advisor 和 critic 可以提出意见，但最终调度权保留在 supervisor。这个选择牺牲了一部分自由度，换来可控、可回放和更容易评测。

一句话记忆：

> 高风险场景先要可控审计，再谈自治程度。

### 9.7 如果追问“你现在到底做成了什么”？

推荐回答：

> 我会分三层说。第一层，业务主链路能跑通：画像、候选、风险评估、报告和 critic。第二层，多智能体协作有明确结构：advisor 并行评审，coordinator 汇总，supervisor 决策。第三层，RL 目前是探索层：trace、preference、reward model、GRPO-compatible 数据和 hook 已经打通，但稳定收益需要更大 benchmark 才能证明。

一句话记忆：

> 主链路成型，协作结构清楚，RL 是接线打通但收益待证。

### 9.8 如果面试官说这和推荐不强相关？

推荐回答：

> 我会承认它不是传统内容推荐，也没有做 CTR/CVR 预估。但它覆盖了推荐系统里非常核心的几个抽象：用户偏好建模、候选生成、约束下重排、slate 级目标、风险控制和离线评估。区别在于这里是显式偏好和高风险决策，工业推荐更多是隐式行为和在线收益。我能迁移的是问题拆解和评估意识，工业模型细节我会继续补齐。

一句话记忆：

> 不争标签，讲抽象迁移和边界差异。

### 9.9 如果被问到下一步实验设计？

推荐回答：

> 我会先固定 benchmark，覆盖不同分数段、风险偏好、专业偏好和信息缺失程度；再固定评价指标，包括 approval rate、issue count、trace length、retry count、人工 rubric 和 source reliability；然后做四组对比：heuristic supervisor、action ranker、reward model reranker、GRPO policy。最后做失败案例归因，检查 learned policy 是真的减少无效路径，还是只是在钻 proxy reward。

一句话记忆：

> benchmark、指标、四组 baseline、失败归因，才算把 RL 做实。

## 10. 实验六问：RL / Multi-Agent 被追问时必须讲清楚

这一节用于回答面试官最可能连问的六个实验问题。核心原则是：先说清楚这是 supervisor 调度层实验，不是端到端训练一个志愿推荐模型。

| 问题 | 稳妥回答 | 一句话记忆 |
| --- | --- | --- |
| 输入是什么？ | RL 层输入是结构化 orchestration observation 加 allowed actions；业务层输入才是考生画像和招生数据。 | 业务输入给推荐链路，RL 输入给 supervisor。 |
| 输出是什么？ | policy 输出下一步动作或动作排序；最终系统输出才是志愿方案和解释报告。 | RL 输出动作，不直接输出学校。 |
| label / reward 是什么？ | pairwise label 是 chosen/rejected action；reward 是 critic 通过、产物质量、成本惩罚组成的 proxy reward。 | label 比动作，reward 评轨迹。 |
| 数据从哪来？ | 业务数据来自历史录取、招生计划、一分一段表和模拟 case；RL 数据来自 rollout trace、proxy reward、rubric / expert 校准。 | 数据一半来自结构化招生数据，一半来自系统轨迹。 |
| baseline 是什么？ | 固定 workflow、heuristic supervisor、random legal action、action ranker / reward reranker 都可以做分层 baseline。 | baseline 先比规则，再比学习策略。 |
| 指标怎么评估？ | 任务级看 approval、issue、risk coverage、source reliability；策略级看 reward、trace length、retry；pairwise 级看 preference accuracy / AUC。 | 任务质量、调度成本、偏好判断三层评估。 |

### 10.1 输入是什么？

推荐回答：

> 要分两层。业务推荐链路的输入是考生分数、位次、选科、地域、专业偏好、风险偏好，以及历史录取数据、招生计划和一分一段表。RL / reward model 层的输入不是原始用户问题，而是 supervisor 的结构化 observation，例如当前 stage、profile 是否完整、候选数、冲稳保分布、critic issue 数、advisor 共识、retry count、research loop count、预算剩余，再加当前允许选择的 actions。

一句话记忆：

> 业务输入是人和数据，RL 输入是状态和可选动作。

别说：

> 输入就是用户一句自然语言问题。

### 10.2 输出是什么？

推荐回答：

> 最终产品输出是志愿方案、风险解释和报告；但 RL 组件的输出不是学校列表，而是 supervisor 下一步动作，或者对 allowed actions 的排序分数。比如当前是否应该进入 deep research、是否生成 report、是否交给 critic、是否 END。这样可以把 learned policy 控制在调度层，避免它直接改动学校候选和录取概率判断。

一句话记忆：

> 产品输出是方案，RL 输出是下一步动作。

别说：

> RL 模型直接输出最优学校。

### 10.3 label / reward 是什么？

推荐回答：

> 如果是 pairwise preference，label 是同一 observation 下 chosen action 和 rejected action 的比较；chosen 通常来自更高 proxy reward、critic 通过路径或人工校准后的合理动作，rejected 来自更多 retry、更多 issue 或无效长路径。reward 则是工程代理目标，包括 critic approve、产出 report / game matrix / research report 加分，retry count、critic issue、trace length 过长、无效步骤扣分。这个 reward 能用于离线比较和保守 rerank，但不能等同真实用户满意度。

一句话记忆：

> label 比较动作优劣，reward 衡量质量减成本。

别说：

> reward 就是真实业务收益或用户满意度。

### 10.4 数据从哪来？

推荐回答：

> 业务侧数据来自历史录取数据、招生计划、一分一段表，以及按不同分数段、风险偏好、专业偏好构造的模拟填报 case。RL 侧数据来自系统运行产生的 rollout trace：每一步 observation、allowed actions、chosen action、agent 执行结果、critic feedback、retry、最终 proxy reward。早期数据可以由 simulator 和 rubric 自动生成，再抽样做人类或专家校准，后续如果有真实使用反馈，再把真实偏好纳入。

一句话记忆：

> 业务数据来自招生结构化表，RL 数据来自系统轨迹和 rubric 校准。

别说：

> 数据全是大模型自己生成的。

### 10.5 baseline 是什么？

推荐回答：

> 我会分层设 baseline。最基础是 fixed workflow，也就是固定顺序跑 profile、game、report、critic；第二层是 heuristic supervisor，用规则决定是否 research、retry、END；第三层是 random legal action，用来排除动作空间本身带来的虚假提升；学习策略再比较 action ranker、reward model reranker 和 GRPO policy。这样能判断收益到底来自流程设计、规则经验，还是 learned policy 本身。

一句话记忆：

> 先比固定流程和规则，再比 ranker、reward model、GRPO。

别说：

> baseline 不重要，只要 RL reward 高就行。

### 10.6 指标怎么评估？

推荐回答：

> 我会分三层评估。任务质量层看 critic approval rate、人工 rubric pass rate、风险覆盖、约束一致性、source reliability、解释质量。调度效率层看 avg reward、trace length、retry count、research loop count、token / time cost。偏好模型层看 pairwise accuracy、AUC 或 chosen action score 是否高于 rejected action。最后还要做失败案例分析，看 learned policy 是真的减少无效路径，还是只是钻了 proxy reward。

一句话记忆：

> 质量看结果，效率看轨迹，模型看 pairwise，最后看失败案例。

别说：

> 只看 reward 一个指标就够了。

## 11. 生成式推荐 / 结构 / 评分 / GRPO 深挖十问

这一节专门处理面试官围绕“生成式推荐是不是牵强”“技术细节怎么落地”的追问。核心口径是：可以讲成生成式推荐相邻或高约束决策推荐，不要硬说成标准 LLM4Rec。

| 追问 | 一句话回答 | 证据锚点 | 风险边界 |
| --- | --- | --- | --- |
| 为什么叫生成式推荐？ | 因为系统生成的是可解释、可审查的推荐方案和决策报告。 | `ReportDraft`, report agent, deep research | 不说生成 item ID |
| 和标准生成式推荐区别？ | 标准 GR 生成 item / slate，本项目生成高约束决策方案。 | `GameMatrix`, `ReportDraft` | 不等同 next-item generation |
| 输入数据结构？ | 业务输入是 `UserProfile + 招生结构化表`，调度输入是 `SupervisorObservation + allowed_actions`。 | `user_profile.py`, `supervisor_policy.py` | 不说只靠自然语言 |
| 输出报告结构？ | 输出是 `ReportDraft`：摘要、策略、推荐、风险、遗憾值。 | `models/report.py` | 不说只是 LLM 文本 |
| 专家评分怎么做？ | 用 blind rubric 评完整性、风险、约束、解释和证据。 | rubric / critic / case review | 不外推线上满意度 |
| reward 怎么设计？ | approved 和有效产物加分，retry、issue、长轨迹和负 step 扣分。 | `compute_episode_summary`, `step_reward.py` | proxy 不是业务收益 |
| 为什么用 GRPO？ | 调度任务天然是同状态多候选动作比较，GRPO 可直接接 reward function。 | `build_grpo_tasks_from_rollouts`, reward funcs | 不说 GRPO 唯一最优 |
| 为什么不是 DPO？ | DPO 适合固定 chosen/rejected 偏好；这里还有 scalar reward 和 rollout 成本。 | `build_preference_examples` | DPO 可做 baseline |
| 多 agent 怎么通信？ | 通过结构化 `AgentMessage`、局部 `AgentMemory` 和 `DeliberationSummary`。 | `agent_communication.py`, `agent_bus.py` | 不说自由聊天自治 |
| 失败 case 是什么？ | 候选不足、保底不足、证据不足或 learned policy 过早 report。 | critic, advisor, supervisor reroute | 不回避失败 |

### 11.1 为什么叫生成式推荐？

推荐回答：

> 我会把它叫成“生成式推荐相邻”或“高约束决策场景里的生成式推荐实践”，而不是标准工业生成式推荐。原因是系统最终不是只输出一个分数或排序，而是生成一个可解释、可审查、可回退的推荐方案：包括候选院校组合、冲稳保策略、风险解释、调研证据和最终报告。这里的“生成式”主要体现在方案解释、报告组织、调研补证和 supervisor 调度决策上，候选学校本身仍由结构化招生数据和概率模型 grounding。

一句话记忆：

> 生成的是决策方案和解释，不是凭空生成学校。

别说：

> 这是标准生成式推荐模型。

### 11.2 它和标准生成式推荐有什么区别？

推荐回答：

> 标准生成式推荐通常关注用户历史、上下文和 item 语义，模型直接生成 next item、item ID、item token 或 slate，评估多用 Recall@K、NDCG、HitRate、CTR/CVR 等。本项目不是这个范式：它先用结构化数据生成候选，再用 LLM / agent 生成解释、补证和报告；目标也不是最大化点击，而是满足分数位次、专业偏好、地域偏好、冲稳保比例和风险可控。所以更准确的说法是 decision recommendation with generative explanation / generative planning。

一句话记忆：

> 标准 GR 生成 item，本项目生成有约束的决策方案。

别说：

> 它和 LLM4Rec 的 next-item generation 一样。

### 11.3 输入数据结构是什么？

推荐回答：

> 输入分三层。第一层是用户画像 `UserProfile`，包括 score、rank、subject_group、preferred_cities、excluded_cities、preferred_majors、blacklist_majors、risk_tolerance、school_major_preference、medical_restrictions 和 subject_scores。第二层是招生与候选数据，核心进入 `GameMatrix / MajorGroupRow`，包括 school_name、school_code、major_group_code、major_list、admission_prob、min_rank_pred、rank_diff、confidence interval、adjustment_risk、strategy_tag 和 comprehensive_score。第三层是 RL 调度 observation，包括 stage、has_profile、has_game_matrix、candidate_count、rush/target/safe_count、requires_search、retry_count、research_loop_count、negative_step_ratio、issue_count 和 allowed_actions。

一句话记忆：

> 输入不是一句话，而是画像、候选矩阵和 supervisor 状态三层结构。

别说：

> 输入就是用户自然语言 query。

### 11.4 输出报告结构是什么？

推荐回答：

> 输出报告用 `ReportDraft` 表达，结构包括 title、executive_summary、strategy_analysis、school_recommendations、risk_warnings、regret_value 和 full_markdown。报告不是单纯让 LLM 自由发挥，它会接收用户画像、GameMatrix 摘要、候选 school / strategy / admission_prob / rank_diff / adjustment_risk / major_list，以及上游 research context，再生成结构化报告。fallback report 也会保留同样结构，避免因为 LLM 输出不稳定导致结果不可审查。

一句话记忆：

> 报告是结构化对象，不是随便一段生成文本。

别说：

> 输出就是一篇大模型作文。

### 11.5 专家评分怎么做？

推荐回答：

> 我会把专家评分讲成 blind rubric review，而不是线上业务实验。每个 case 隐去系统策略来源，只给专家看用户画像、约束、候选方案和报告。评分维度可以包括：约束一致性、冲稳保结构、风险覆盖、专业/地域匹配、解释可理解性、证据可信度和是否存在严重误导。通过标准不是“专家喜欢”，而是没有 critical issue，并且主要维度达到阈值；如果两个专家分歧大，需要仲裁或记录为 uncertain case。这个结果只能说明离线可交付性，不能代表真实用户长期满意度。

一句话记忆：

> 专家评的是约束、风险、解释和证据，不是线上满意度。

别说：

> 专家评分通过就说明产品效果已经被证明。

### 11.6 reward 怎么设计？

推荐回答：

> reward 分两层。episode-level reward 来自 `compute_episode_summary`：critic approved 加分，没有通过扣分；有 report 或 research_report 加分，没有产物扣分；retry_count、issue_count、trace_length 过长和 negative_step_ratio 扣分，最后裁剪到 [-1, 1]。step-level reward 则检查工具调用是否为空、工具是否匹配、结果是否相关、token efficiency 是否合理。GRPO 训练里还会有 format reward、valid action reward、reference match reward 和 proxy reward shaping，确保模型输出合法 JSON、选择 allowed action，并尽量匹配高质量轨迹。

一句话记忆：

> reward = 通过和产物加分，重试、问题、长轨迹、坏工具扣分。

别说：

> reward 就是用户最终满意度。

### 11.7 为什么用 GRPO？

推荐回答：

> 我用 GRPO 是因为 supervisor 调度很适合“同一个 observation 下比较多个候选动作”。每一步都有 allowed_actions，policy 可以生成 next_action 和 rationale，然后 reward function 从格式合法性、动作合法性、是否匹配参考动作、轨迹 proxy reward 来打分。GRPO 不需要额外 value model，工程上比 PPO 更轻，也更贴近“采样多种动作，再用组内相对优势更新”的设定。但我会强调 GRPO 是探索路径，不是证明它一定优于所有方法。

一句话记忆：

> GRPO 适合 allowed actions 下的多候选动作比较。

别说：

> 因为 GRPO 一定比 PPO 和 DPO 高级。

### 11.8 为什么不是 DPO？

推荐回答：

> DPO 适合已经有稳定 chosen / rejected 偏好对的场景，我这里确实可以把 pairwise action preference 导成 DPO-style 数据，所以 DPO 可以作为 baseline。但主问题不只是静态偏好学习，还包含 rollout 成本、critic issue、trace length、valid action、format correctness 这类 scalar reward。GRPO 更方便直接接 reward function 和同状态多候选比较；DPO 更适合作为 reward model / ranker 或 preference baseline。

一句话记忆：

> DPO 学偏好对，GRPO 更方便接轨迹 reward 和多候选动作。

别说：

> DPO 不能用，或者 DPO 一定不如 GRPO。

### 11.9 多 agent 怎么通信？

推荐回答：

> 多 agent 不是自由聊天，而是通过结构化协议通信。`AgentMessage` 里有 sender、recipients、stage、message_type、content、action_preference、confidence、references 和 metadata；`AgentMemoryEntry` 保存局部 memory；`DeliberationSummary` 汇总 recommended_action、vote_scores、dissent_count、consensus_strength 和 requires_research。risk guardian、opportunity advocate、evidence guardian 分别发布 vote，coordinator 聚合后把 recommended_next_action 交给 supervisor。这样每条意见都能回放、统计和进入后续 preference 数据。

一句话记忆：

> 通信靠结构化 message、memory 和 deliberation summary，不靠自由闲聊。

别说：

> 多个 agent 在自然语言里随便讨论。

### 11.10 失败 case 是什么？

推荐回答：

> 一个典型失败 case 是：用户位次在边界附近、又不接受调剂、还偏好热门专业，但候选池里 safe_count 很低。如果 supervisor 过早进入 report，报告可能看起来完整，但保底不足、调剂风险和证据缺口没有被充分暴露。系统里对此有几类防线：risk guardian 会因为 candidate_count 低、safe_count 低或 portfolio risk 高建议 deep_research；critic 会根据 issue reroute；reward 会对 issue、retry 和负 step 扣分。这个 case 的价值是提醒我，learned policy 不能只追求短轨迹，必须把风险覆盖和 evidence quality 放进 reward 和人工 rubric。

一句话记忆：

> 最危险的失败不是没输出，而是过早输出一个看似完整但风险不足的方案。

别说：

> 系统现在没有明显失败 case。

## 12. 项目总纲模板：从 30 秒到 3 分钟

这一节是面试开场和系统性追问时的总纲。不要一开始就讲 GRPO，先把问题、输入输出、模块、评估和边界讲稳。

### 12.1 项目名

项目名：

> GaokaoAgent：面向高考志愿填报的多智能体决策推荐系统。

一句话记忆：

> GaokaoAgent 是高考志愿场景里的高约束决策推荐系统。

### 12.2 一句话定位：这个项目到底解决什么问题？

30 秒回答：

> 这个项目解决的是高考志愿填报里候选空间大、规则复杂、风险高、解释要求强的问题。我没有让 LLM 直接生成学校名单，而是用结构化招生数据生成候选和风险评估，再用 LangGraph supervisor 调度画像、推荐、调研、报告和 critic 审查，最后输出一份可解释、可审查、可回退的志愿决策建议。

一句话记忆：

> 不是 LLM 出学校，而是结构化推荐加多智能体审查闭环。

### 12.3 业务 / 研究问题

为什么重要：

> 高考志愿是一次高风险决策，用户不仅要“能上什么学校”，还要知道冲稳保是否平衡、专业调剂风险是否可接受、证据是否可靠、方案为什么这样排。错误推荐的代价不是一次点击损失，而可能是滑档、专业错配或长期后悔。

传统方法不足：

> 人工填报依赖经验，成本高且难系统覆盖；普通分数线查询工具只给静态候选，缺少偏好、风险和组合层面的解释；单轮 LLM 容易幻觉，无法保证候选来自真实数据；固定 workflow 能跑通流程，但遇到证据不足、风险分歧或 critic 失败时缺少动态调度能力。

一句话记忆：

> 传统工具给信息，项目要给可审查的决策方案。

### 12.4 输入

| 层级 | 输入内容 | 结构示例 | 作用 |
| --- | --- | --- | --- |
| 用户输入 | 自然语言诉求、分数、位次、选科、专业/城市/风险偏好 | “物理类 620 分，位次 12000，想学计算机，希望稳一点” | 触发画像抽取和意图分类 |
| 业务模型输入 | `UserProfile` + 招生计划、历史录取、一分一段表、专业组信息 | score、rank、subject_group、preferred_majors、risk_tolerance | 生成候选和风险评估 |
| 推荐引擎输入 | `GameMatrix / MajorGroupRow` | school、major_group、admission_prob、rank_diff、adjustment_risk、strategy_tag | 形成冲稳保 slate |
| 调度模型输入 | `SupervisorObservation + allowed_actions` | stage、has_game_matrix、candidate_count、safe_count、issue_count、retry_count | 决定下一步走 report、research、critic 还是 END |

一句话记忆：

> 用户输入给画像，结构化数据给推荐，observation 给 supervisor。

### 12.5 输出

| 输出对象 | 是什么 | 不是 |
| --- | --- | --- |
| 志愿决策建议 | 一组冲稳保平衡的院校/专业组候选和排序 | 不是 LLM 凭空生成的学校 |
| 结构化报告 | `ReportDraft`：执行摘要、策略分析、院校推荐、风险警示、遗憾值分析 | 不是不可审查的自由文本 |
| 调度 trajectory | supervisor 每步 observation、allowed actions、selected action、rationale、reward proxy | 不是最终给用户看的主输出 |
| 审查结果 | critic issue、是否 approved、reroute 建议 | 不是唯一真值 label |

一句话记忆：

> 用户看到方案和报告，研究侧记录 trajectory 和 reward。

### 12.6 核心模块

模块 1：结构化推荐与风险评估

> 负责从用户画像和招生数据中生成候选专业组，估计录取概率、位次差、调剂风险、冲稳保标签和组合风险，对应 `quant_engine.py`、`probability.py`、`monte_carlo_sim.py`、`game_agent.py` 和 `GameMatrix`。

模块 2：LangGraph 多智能体调度闭环

> 负责把画像、推荐、深度调研、报告、critic 审查串成可回放流程，并引入 risk guardian、opportunity advocate、evidence guardian 和 coordinator 做并行评审，对应 `dual_loop_supervisor.py`、`deliberation_agents.py`、`agent_communication.py`。

模块 3：调度层 RL / preference learning 探索

> 负责记录 supervisor trajectory，构造 pairwise preference、reward proxy、SFT / reward model / GRPO-compatible 数据，并通过 learned ranker 或 reward reranker 接回 supervisor，对应 `supervisor_policy.py`、`orchestration_data_pipeline.py`、`orchestration_alignment.py`、`orchestration_trl_utils.py`。

一句话记忆：

> 推荐模块给候选，多 agent 给审查，RL 探索给 supervisor 调度优化。

### 12.7 核心数据结构：一条样本长什么样

| 字段 | 示例 | 说明 |
| --- | --- | --- |
| `case_id` | `SYN0042` | 一条模拟或归一化用户请求 |
| `user_profile.score` | `620` | 高考总分 |
| `user_profile.rank` | `12000` | 全省位次 |
| `user_profile.subject_group` | `物理` | 选科组合 |
| `user_profile.preferred_majors` | `["计算机", "人工智能"]` | 专业偏好 |
| `user_profile.risk_tolerance` | `balanced` | 风险偏好 |
| `candidate.school_name` | `A大学` | 候选院校 |
| `candidate.major_group_code` | `A01` | 专业组 |
| `candidate.admission_prob` | `0.72` | 录取概率 |
| `candidate.adjustment_risk` | `0.10` | 调剂风险 |
| `candidate.strategy_tag` | `target` | 冲/稳/保标签 |
| `observation.stage` | `after_game` | supervisor 当前决策阶段 |
| `observation.safe_count` | `8` | 保底数量 |
| `allowed_actions` | `["report_agent", "deep_research"]` | 当前可选动作 |
| `selected_action` | `deep_research` | supervisor 选择 |
| `reward_proxy` | `0.64` | 轨迹代理奖励 |

一句话记忆：

> 一条样本 = 用户画像 + 候选矩阵 + supervisor 决策点 + 结果反馈。

### 12.8 训练 / 优化方式

是否 SFT：

> 不是生产级大规模 SFT。项目里有把 rollout trace 导成 SFT-style prompt/response 的能力，用于让模型学习 supervisor action 输出格式和 rationale，但我不会把它说成已经完成大规模 SFT。

是否 DPO / GRPO / PPO：

> DPO 可以用 pairwise action preference 做 baseline；GRPO 是我更重点探索的路径，因为它能在同一个 observation 下采样多个 allowed action，并直接接 format reward、valid action reward、reference match reward 和 proxy reward。PPO 没作为主路径，因为它工程成本更高，还需要 value model；当前阶段没有必要把问题做得那么重。

如果没有真实训练：

> 我会明确说主链路是 heuristic-first 的可运行 research prototype，RL 部分是 orchestration-level 数据、训练格式、reward function 和 runtime hook 的接入探索。现在能证明链路打通，不能 claim 稳定线上收益。

一句话记忆：

> 主系统靠规则和结构化链路跑通，学习策略是调度层增强探索。

### 12.9 Label / Reward

label 从哪里来：

> pairwise label 来自同一 observation 下的 chosen / rejected action。chosen 可以是实际高质量轨迹动作、critic approved 路径动作、proxy reward 更高的动作，或人工 rubric 校准后的合理动作；rejected 是导致更多 issue、retry、无效长轨迹或证据不足的动作。

reward 怎么定义：

> episode-level reward 由 critic approved、有无 report / research_report、retry_count、issue_count、trace_length 和 negative_step_ratio 组合而成，并裁剪到 [-1, 1]。step-level reward 检查工具调用是否为空、工具是否匹配、结果是否相关和 token efficiency。

有没有 true label：

> 没有唯一 true label。高考志愿不是“唯一正确答案”问题，同一个用户可能存在多个合理方案，所以不能用单一 ground truth school list 来评估。

没有唯一真值如何评估：

> 用约束一致性、风险覆盖、冲稳保结构、证据可信度、解释质量、专家 blind rubric 和 critic issue 来评估；同时比较不同 policy 的 trajectory 成本和失败 case。

一句话记忆：

> 没有唯一真值，就用约束、风险、证据和专家 rubric 评估。

### 12.10 Baseline

| baseline | 为什么合理 | 对比目的 |
| --- | --- | --- |
| 单轮 LLM 直接生成 | 代表最弱但常见的 naive 方案 | 证明 grounding 和审查必要 |
| 固定 workflow | 代表没有动态调度的工程流程 | 看 supervisor 是否减少无效路径 |
| heuristic supervisor | 当前稳定主干 | 看 learned policy 是否有增益 |
| random legal action | 只在 allowed actions 里随机选 | 排除动作空间本身带来的假提升 |
| action ranker / reward reranker | 轻量学习策略 | 和 GRPO 做分层对比 |
| GRPO policy | 调度层策略优化探索 | 看多候选 reward 优化是否有效 |

一句话记忆：

> baseline 从 naive LLM、固定流程、规则 supervisor 到 learned policy 分层比较。

### 12.11 Metric

效果指标：

> critic approval rate、人工 rubric pass rate、risk coverage、constraint consistency、source reliability、解释质量、推荐组合冲稳保合理性。

效率指标：

> trace length、retry count、research loop count、token cost、time cost、无效工具调用比例。

稳定性指标：

> 不同 case category / difficulty 下的 approval variance、失败率、reroute rate、max-loop hit rate、重复运行一致性。

人工评估指标：

> 专家对完整性、风险覆盖、约束一致性、专业/地域匹配、证据可信度、可解释性和严重误导风险进行 blind rubric 打分。

一句话记忆：

> 效果看质量，效率看成本，稳定性看方差，人工看风险和解释。

### 12.12 我的贡献

我具体写了哪些代码：

> 我负责把项目从单链路推荐扩展成 graph-orchestrated multi-agent research prototype，包括 supervisor 调度、agent 通信协议、并行 advisor、critic 审查、orchestration trace、reward proxy、preference 数据导出、GRPO-compatible 数据和 runtime hook。

我负责哪些模块：

> 重点负责 `backend/src/graph/dual_loop_supervisor.py`、`backend/src/agents/deliberation_agents.py`、`backend/src/models/agent_communication.py`、`backend/src/utils/agent_bus.py`、`backend/src/rl/*` 相关设计与接入，以及面向面试和评测的文档整理。

哪些是复现，哪些是原创设计：

> LangGraph、TRL / GRPO 思路和推荐系统里的候选-排序-评估抽象是借鉴成熟范式；原创设计主要在高考志愿场景的结构化状态抽象、advisor 分工、critic 闸门、supervisor action space、proxy reward 和把 trajectory 转成 preference / GRPO task 的链路。

一句话记忆：

> 框架借成熟范式，原创在场景抽象、协作协议和调度层训练数据链路。

### 12.13 失败 Case

失败场景 1：边界位次 + 热门专业 + 不接受调剂

> 系统可能过早生成看似完整的 report，但 safe_count 不足、调剂风险被低估。应通过 risk guardian、critic issue 和 reward penalty 强化保底与调剂风险。

失败场景 2：外部政策或招生章程信息不足

> deep research fallback 可能给出启发式总结，但证据可信度不够。应强化 source reliability、官方来源优先级和引用校验。

失败场景 3：learned policy 钻 proxy reward

> policy 可能偏向短路径、少 research、快速 END，从而提升 trace cost 指标但牺牲风险覆盖。应在 reward 中提高 evidence quality、risk coverage 和 human rubric 权重。

一句话记忆：

> 最危险的失败是看起来完整，但保底、证据或风险覆盖不够。

### 12.14 边界与不足

这个方法不能解决什么：

> 它不能保证唯一最优志愿表，不能替代真实招生政策复核，不能把 proxy reward 等同用户长期满意度，也不能在没有可靠数据源时保证生成内容完全可信。它更适合作为辅助决策系统，而不是自动替人填报的生产级系统。

如果继续做，下一步怎么改：

> 我会先做更系统的 benchmark 和 case taxonomy，再扩充真实或半真实 preference 数据；然后做 fixed workflow、heuristic supervisor、ranker、reward reranker、GRPO 的 ablation；同时加强官方数据源、引用校验、失败 case 回放和人工 rubric，使 learned policy 只在高置信场景逐步接管更多调度权重。

一句话记忆：

> 不能替代人工决策，下一步是 benchmark、真实偏好、可靠来源和安全接入。

### 12.15 30 秒版本

> GaokaoAgent 解决的是高考志愿填报中候选多、约束复杂、风险高、解释要求强的问题。我把它做成结构化推荐加多智能体审查闭环：候选学校来自历史录取、招生计划和一分一段表，LLM / agent 负责偏好理解、调研补证、报告生成和 critic 审查。RL 部分不是直接选学校，而是探索 supervisor 下一步动作选择，比如何时 research、何时 report、何时 reroute。

一句话记忆：

> 学校来自数据，解释来自 LLM，RL 只管 supervisor 下一步。

### 12.16 1 分钟版本

> 这个项目是一个面向高考志愿填报的高约束决策推荐系统。业务上，它要解决候选空间大、政策和偏好约束复杂、滑档和调剂风险难控的问题；技术上，我没有让 LLM 端到端生成学校，而是先用用户画像和结构化招生数据生成候选矩阵，再用 supervisor 调度 profile、game、deep research、report 和 critic。多 agent 部分主要体现在 risk guardian、opportunity advocate、evidence guardian 并行评审，再由 coordinator 汇总给 supervisor。RL / GRPO 探索只落在调度层：把每个决策点抽象成 observation、allowed actions、selected action 和 reward proxy，用 rollout trace 构造 preference 和 GRPO task。当前我会把它定位为 research prototype，主链路和数据接线跑通，但 learned policy 的稳定收益还需要更大 benchmark 验证。

一句话记忆：

> 主链路是结构化推荐，多 agent 做审查，RL 做调度层探索。

### 12.17 3 分钟版本

> GaokaoAgent 是我做的一个高考志愿填报辅助决策系统。我关注的问题不是简单问答，而是高风险、多约束、长路径的决策推荐：用户有分数、位次、选科、城市、专业、风险偏好和调剂底线；系统还要结合历史录取、招生计划、一分一段表和专业组规则，给出冲稳保平衡、风险可解释的方案。
>
> 系统分三层。第一层是结构化推荐层，把用户输入抽成 `UserProfile`，再生成 `GameMatrix / MajorGroupRow`，里面有学校、专业组、录取概率、位次差、调剂风险和冲稳保标签。第二层是 LangGraph 多智能体层，由 centralized supervisor 调度画像、候选生成、deep research、报告和 critic；在候选生成后，risk guardian、opportunity advocate、evidence guardian 会并行给出 vote 和 action_preference，coordinator 汇总成 deliberation summary。第三层是调度优化探索，我把 supervisor 的每一步抽象成 observation 和 allowed actions，记录 selected action、rationale、critic feedback 和 reward proxy，用来构造 SFT、pairwise preference、reward model 和 GRPO-compatible 数据。
>
> 输出上，用户看到的是结构化报告 `ReportDraft`：执行摘要、策略分析、院校推荐、风险警示和遗憾值分析；研究侧还会保留 trajectory、reward 和 critic issue。评估上，因为志愿填报没有唯一真值，我不会说有 true label，而是用 critic approval、人工 rubric、风险覆盖、约束一致性、source reliability、trace length 和 retry count 来评估。baseline 会从单轮 LLM、固定 workflow、heuristic supervisor 到 action ranker、reward reranker 和 GRPO policy 分层比较。边界上，我不会说它已经是生产级或稳定 RL 系统；当前更准确的说法是可运行的 research prototype，贡献在于把结构化推荐、多智能体审查和调度层 preference / GRPO 数据链路接到一个可回放闭环里。

一句话记忆：

> 三分钟版本按“问题重要性、三层架构、输出评估、贡献边界”讲。

## 13. Agent 实现总览：GT、数量、流程和设计理由

这一节专门回答“GT 是什么、到底几个 agent、每个 agent 干什么、为什么要这么多、流程怎么跑”。面试时先给口径，再给代码锚点。

### 13.1 GT 是什么？

推荐回答：

> GT 是 Ground Truth，中文是标准答案或真实标签。但这个项目里不能简单说有唯一 GT。历史录取数据里有事实标签，例如某年某院校专业组最低位次、招生计划和真实录取结果；但“当前用户应该填哪一组志愿”没有唯一 ground truth，因为不同风险偏好、城市偏好和专业偏好会产生多个合理解。所以我把专家评分、critic feedback、chosen/rejected action 和 reward proxy 都叫评估信号或代理标签，不把它们包装成唯一真值。

| 对象 | 是否是 GT | 稳妥说法 |
| --- | --- | --- |
| 历史最低位次 / 招生计划 | 是事实数据 | 可以作为候选和概率估计的 grounding |
| 当前志愿方案 | 没有唯一 GT | 用约束一致性、风险覆盖、rubric 评估 |
| 专家评分 | 不是 GT | 是 blind rubric review |
| critic approve | 不是 GT | 是质量闸门信号 |
| chosen / rejected action | 不是 GT | 是 preference / pseudo label |
| reward proxy | 不是 GT | 是质量和成本的代理奖励 |

一句话记忆：

> 录取历史有事实标签，志愿方案没有唯一 GT。

### 13.2 到底有几个 agent？

推荐回答：

> 如果按 LangGraph 里的业务/协作节点算，是 11 个 agent-like 节点：`router_agent`、`profiling_agent`、`game_agent`、`risk_guardian_agent`、`opportunity_advocate_agent`、`evidence_guardian_agent`、`deliberation_coordinator`、`report_agent`、`deep_research`、`multimodal_parser`、`critic_agent`。此外还有 4 个 `supervisor_after_*` 决策节点，它们不是业务 agent，而是 centralized supervisor policy 的路由决策点。

| 类别 | 数量 | 节点 |
| --- | --- | --- |
| 主链路 agent | 5 | router、profiling、game、report、critic |
| 候选后并行 advisor | 3 | risk guardian、opportunity advocate、evidence guardian |
| 协调节点 | 1 | deliberation coordinator |
| 辅助分支 | 2 | deep research、multimodal parser |
| supervisor 决策节点 | 4 | after_profiling、after_game、after_report、after_critic |

一句话记忆：

> 11 个 agent-like 节点，4 个 supervisor 决策点；不要把 supervisor 节点也说成 agent。

### 13.3 总流程是什么？

主流程：

> `START -> router_agent -> profiling_agent -> supervisor_after_profiling -> game_agent -> 三个 advisor 并行评审 -> deliberation_coordinator -> supervisor_after_game -> report_agent -> supervisor_after_report -> critic_agent -> supervisor_after_critic -> END 或 reroute`

辅助分支：

> 如果 router 或 supervisor 判断需要外部证据，就走 `deep_research -> report_agent -> critic_agent`；如果输入涉及 PDF、招生章程、体检限制或视觉解析，就走 `multimodal_parser -> critic_agent`。

代码锚点：

> 图结构在 `backend/src/graph/dual_loop_supervisor.py`，节点注册集中在 `builder.add_node(...)`，边和条件路由集中在 `builder.add_edge(...)` 和 `builder.add_conditional_edges(...)`。supervisor 选择下一步动作的逻辑在 `backend/src/rl/supervisor_policy.py`。

一句话记忆：

> router 定方向，profile 建画像，game 出候选，advisor 审方案，report 写报告，critic 决定通过或回退。

### 13.4 每个 agent 都干了啥？

| Agent | 实现位置 | 输入 | 输出 | 设计意图 |
| --- | --- | --- | --- | --- |
| `router_agent` | `agents/router_agent.py` | 用户 query | intent、active_loop、next_action | 先判断走量化、调研还是多模态 |
| `profiling_agent` | `agents/profiling_agent.py` | query / messages | `UserProfile` | 把自然语言约束结构化 |
| `game_agent` | `agents/game_agent.py` | `UserProfile` + 招生数据 | `GameMatrix` | 生成候选、概率、冲稳保、风险 |
| `risk_guardian_agent` | `agents/deliberation_agents.py` | `GameMatrix` | vote: report 或 deep_research | 检查保底不足、滑档和组合风险 |
| `opportunity_advocate_agent` | `agents/deliberation_agents.py` | `GameMatrix` | vote: report 或 deep_research | 防止方案过保守，保留机会空间 |
| `evidence_guardian_agent` | `agents/deliberation_agents.py` | intent + research state | vote: report 或 deep_research | 检查是否缺外部证据 |
| `deliberation_coordinator` | `agents/deliberation_agents.py` | 三个 advisor 的 message | `DeliberationSummary` | 聚合 vote、置信度和分歧 |
| `report_agent` | `agents/report_agent.py` | profile + matrix + research context | `ReportDraft` | 生成结构化报告和风险解释 |
| `deep_research` | `agents/deep_research_agent.py` / `subgraphs` | research topic / query | research report | 做 plan-execute-reflect-synthesize 调研 |
| `multimodal_parser` | `agents/multimodal_agent.py` | PDF / 章程 / 视觉结果 | health restrictions / parsed constraints | 处理非纯文本约束 |
| `critic_agent` | `agents/critic_agent_enhanced.py` | report / state / messages | approve、issues、reroute、step_rewards | 做最终质量闸门和回退建议 |

一句话记忆：

> 每个 agent 对应一种失败模式，不是为了堆数量。

### 13.5 各自怎么实现设计的？

Router：

> 设计成元路由节点，先判断用户请求属于快思考量化推荐、慢思考外部调研、多模态解析或混合任务。它不直接产出学校，而是给 supervisor 一个初始方向。

Profiling：

> 设计成信息抽取节点，把自然语言中的分数、位次、选科、城市偏好、专业偏好、黑名单专业、风险偏好等写成 `UserProfile`。这样后续推荐不是直接吃自然语言，而是吃稳定 schema。

Game：

> 设计成结构化推荐核心，基于用户画像和招生数据生成 `GameMatrix / MajorGroupRow`，每行包含 school、major_group、admission_prob、rank_diff、adjustment_risk、strategy_tag、comprehensive_score 等字段。它负责 grounding，不让 LLM 凭空编学校。

三个 Advisor：

> 设计成并行审查而不是串行 prompt。`risk_guardian` 看下行风险，`opportunity_advocate` 看机会空间，`evidence_guardian` 看证据充分性。三者都通过 `publish_agent_message` 发出结构化 vote，包括 `action_preference`、`confidence` 和 `metadata`。

Coordinator：

> 设计成聚合器，不做开放式辩论。它读取同一 stage 的 agent messages，把各 action 的 confidence 加权汇总，输出 `DeliberationSummary`，包括 `recommended_action`、`vote_scores`、`dissent_count`、`consensus_strength`。

Report：

> 设计成结构化生成节点，输出 `ReportDraft`，包括 executive_summary、strategy_analysis、school_recommendations、risk_warnings、regret_value。它可以用 LLM 生成，但输出必须落回结构化 schema。

Critic：

> 设计成质量闸门，负责审查报告和执行步骤。如果发现风险覆盖不足、报告缺失、工具调用质量差或规则问题，就产生 issues 和 reroute 建议；同时记录 step-level reward。

Deep Research：

> 设计成慢思考分支，用于处理需要外部证据的问题。它不是每次都跑，因为调研成本高；只有 requires_search、证据不足、advisor 分歧或 critic 多次失败时才触发。

Multimodal：

> 设计成辅助解析分支，用于处理 PDF、招生章程、体检限制等非结构化或多模态约束。它的输出会进入 state，供后续 critic 或报告使用。

一句话记忆：

> 结构化节点负责 grounding，advisor 负责分角度审查，coordinator 负责汇总，critic 负责兜底。

### 13.6 为什么要那么多？

推荐回答：

> 不是因为 agent 越多越智能，而是高考志愿有多个相互冲突的风险维度：画像可能错、候选可能不全、方案可能太冒险、方案也可能太保守、证据可能不足、报告可能漏风险。如果都塞进一个 agent，很难定位失败原因，也很难把后续 trajectory 转成 preference / reward 数据。拆成多个角色后，每个 agent 的输入、输出和失败责任更清楚，advisor 的 vote 也能被记录进 `AgentMessage` 和 `DeliberationSummary`。

| 失败模式 | 对应设计 |
| --- | --- |
| 用户画像抽错 | profiling agent |
| 学校候选不 grounded | game agent |
| 保底不足 / 滑档风险 | risk guardian |
| 方案过保守 | opportunity advocate |
| 证据不足 / 政策不确定 | evidence guardian / deep research |
| 报告遗漏风险 | critic agent |
| PDF / 章程约束没处理 | multimodal parser |
| 多方意见冲突 | deliberation coordinator |

一句话记忆：

> 拆 agent 是为了拆失败模式和收集可回放证据，不是为了堆复杂度。

### 13.7 Agent 之间怎么通信？

推荐回答：

> 通信不是自然语言随便聊天，而是结构化协议。`AgentMessage` 包含 sender、recipients、stage、message_type、content、action_preference、confidence、references、metadata；`AgentMemoryEntry` 存每个 agent 的局部记忆；`DeliberationSummary` 汇总 recommended_action、vote_scores、dissent_count、consensus_strength 和 requires_research。agent_bus 里的 `publish_agent_message`、`get_messages_for_stage`、`remember`、`publish_deliberation` 负责把这些对象写入和读出 `SupervisorState`。

一句话记忆：

> 通信靠结构化 message 和 summary，不靠开放式群聊。

### 13.8 面试 30 秒回答

> 代码里主图是 11 个 agent-like 节点加 4 个 supervisor 决策点。主链路是 router、profiling、game、report、critic；候选生成后有 risk、opportunity、evidence 三个 advisor 并行评审，再由 coordinator 汇总；另外有 deep research 和 multimodal 两个辅助分支。这样拆不是为了堆 agent，而是为了把画像错误、候选不全、滑档风险、方案过保守、证据不足和报告漏风险这些失败模式分开处理，并用结构化 message 记录下来。

一句话记忆：

> 11 个 agent-like 节点，围绕不同失败模式拆分，supervisor 统一调度。

### 13.9 面试 1 分钟回答

> 我这个项目不是多个 prompt 串起来，而是 LangGraph 里的 centralized supervisor graph。完整图里有 11 个 agent-like 节点：router 做意图路由，profiling 抽 `UserProfile`，game 生成 `GameMatrix`，report 生成 `ReportDraft`，critic 做质量闸门；候选生成后，risk guardian、opportunity advocate、evidence guardian 三个 advisor 分别从风险、机会和证据角度给 vote，coordinator 汇总成 `DeliberationSummary`，再交给 supervisor 决定 report、deep research 或 reroute。deep research 处理外部证据不足，多模态分支处理 PDF / 章程 / 体检限制。GT 上我不会说志愿方案有唯一真值，只有历史录取数据是事实标签；专家评分、critic 和 reward 都是评估信号或 proxy。

一句话记忆：

> 主链路产方案，advisor 审风险，coordinator 汇总，critic 兜底，GT 只存在于历史事实，不存在唯一志愿答案。

## 14. 通用基础版：面试官实现追问地图

这一节的目标不是继续把项目讲得更“高级”，而是把它讲得更“可信”。面试官通常不会先关心你用了 LangGraph、GRPO 或 multi-agent，而是先关心：输入是什么、数据怎么流动、每一步谁负责、错误怎么处理、你具体写了什么、怎么证明有效。

一句话记忆：

> 先讲清数据流和责任边界，再讲 agent 和 RL。

### 14.1 面试官真正关心什么？

| 面试官关心点 | 典型追问 | 稳妥回答方向 | 实现证据 |
| --- | --- | --- | --- |
| 问题定义 | 你到底解决什么问题？ | 高考志愿是高约束、强风险、弱真值的决策推荐问题，不是普通聊天生成。 | `UserProfile`、`GameMatrix`、`ReportDraft` |
| 输入边界 | 用户输入和系统输入分别是什么？ | 用户给分数、位次、偏好和约束；系统读历史录取、招生计划、一分一段、政策材料。 | profiling / game / research modules |
| 数据流 | 请求进来后怎么走？ | query 先路由，再抽画像，再生成候选矩阵，再多角度审查，最后生成报告并由 critic 检查。 | `dual_loop_supervisor.py` |
| 模块责任 | 每个 agent 为什么存在？ | 每个 agent 对应一种失败模式：画像错、候选不全、风险漏掉、证据不足、报告不合规。 | `deliberation_agents.py`、`agent_bus.py` |
| 推荐逻辑 | 学校怎么被推荐出来？ | 先用结构化录取数据和约束生成候选，再按概率、风险、偏好和策略标签重排。 | `game_agent.py`、`quant_engine.py` |
| LLM 边界 | LLM 到底做了什么？ | LLM 负责抽取、解释、报告和部分调度判断，不负责凭空决定学校事实。 | schema output + critic |
| 通信机制 | agent 之间怎么通信？ | 通过结构化 `AgentMessage` 和 `DeliberationSummary`，不是开放式群聊。 | `agent_bus.py` |
| RL 边界 | 强化学习到底做了什么？ | 更准确说是调度策略探索和 GRPO-compatible 接入，不要吹成完整 RLVR 训练闭环。 | `supervisor_policy.py`、`orchestration_trace.py` |
| label / reward | 没有唯一真值怎么办？ | 历史录取是事实标签，方案质量没有唯一 GT，所以用专家 rubric、critic proxy 和约束一致性评估。 | `critic_agent_enhanced.py` |
| baseline | 和谁比？ | 单 LLM、固定流程、无 advisor、无 critic、无 deep research 的消融版本。 | evaluation scripts / ablation design |
| metric | 怎么证明有效？ | 看通过率、风险覆盖、约束违反率、候选多样性、人工评分、token / step 成本和 reroute 次数。 | expert review + trace metrics |
| 失败 case | 什么情况下会失败？ | 数据过期、政策模糊、偏好冲突、分数边界、用户输入缺失、LLM 报告解释过度。 | critic issues / reroute logs |

一句话记忆：

> 面试官问实现，本质是在问数据、边界、证据和失败处理。

### 14.2 五层实现解释

第 1 层：入口层。

> `router_agent` 先判断用户请求类型：是快速量化推荐、需要外部调研、需要多模态解析，还是混合任务。它的输出不是学校，而是下一步动作和 active loop。

第 2 层：数据层。

> `profiling_agent` 把自然语言转成 `UserProfile`，包括分数、位次、科类、省份、城市偏好、专业偏好、风险偏好、黑名单和硬约束；`game_agent` 再结合历史录取、招生计划和一分一段表生成 `GameMatrix`。

第 3 层：决策层。

> supervisor 只在有限动作空间里调度，例如继续 report、触发 deep research、reroute、approve 或 stop。这样做是为了让轨迹可记录、可比较、可训练，而不是让模型自由发挥。

第 4 层：协作层。

> 三个 advisor 并行审查同一个候选矩阵：risk guardian 看下行风险，opportunity advocate 看机会空间，evidence guardian 看证据是否足够；coordinator 把 vote、confidence 和分歧汇总成 `DeliberationSummary`。

第 5 层：评估层。

> `critic_agent` 检查报告是否覆盖风险、是否满足用户约束、是否有证据缺口和格式问题；同时把步骤质量转成 step-level reward proxy，供后续调度策略分析或 GRPO 接入。

一句话记忆：

> 入口分流，数据 grounding，supervisor 调度，advisor 审查，critic 兜底。

### 14.3 最可能被问的基础问题

| 问题 | 建议回答 |
| --- | --- |
| 输入是什么？ | 用户输入是自然语言需求和偏好，系统输入是历史录取、招生计划、一分一段和政策材料，模型输入是结构化后的 `UserProfile` 与候选状态。 |
| 输出是什么？ | 最终输出不是一个 label，而是结构化志愿建议报告，包括候选院校、冲稳保策略、风险解释、证据说明和待确认项。 |
| 学校怎么生成？ | 先用结构化招生数据筛出可行候选，再根据概率、位次差、专业偏好、城市偏好、风险偏好和组合策略做排序。 |
| LLM 做什么、不做什么？ | LLM 做信息抽取、解释生成、审查和调度辅助；不让 LLM 凭空生成录取事实或替代结构化计算。 |
| 为什么要 multi-agent？ | 因为失败模式不同，画像、候选、风险、机会、证据和报告质量需要不同责任模块分别检查。 |
| agent 怎么通信？ | 通过 `AgentMessage`、`AgentMemoryEntry` 和 `DeliberationSummary` 通信，核心字段包括 sender、stage、action_preference、confidence 和 metadata。 |
| GT 是什么？ | 历史录取结果是事实 GT；志愿方案本身没有唯一 GT，所以专家评分和 critic 只能作为质量评估信号。 |
| reward 是什么？ | reward 不是单一正确答案，而是由约束满足、风险覆盖、证据充分、报告质量、调度成本和人工评分组合出来的 proxy。 |
| 有没有真正训练？ | 要保守说：项目重点完成了 trajectory 采集、reward 设计、GRPO-compatible 接入和对比评估框架；不要把它包装成大规模线上 RLVR。 |
| 为什么用 GRPO？ | 因为调度动作可以对同一输入采样多条轨迹，并用组内相对优势比较哪条轨迹更好，适合弱真值、长路径的流程优化。 |
| 为什么不是 DPO？ | DPO 更适合已有成对偏好样本的离线偏好学习；这个项目更关注多步调度轨迹的探索、成本和结果质量。 |
| baseline 是什么？ | 单轮 LLM、固定工作流、去掉 advisor、去掉 critic、去掉 deep research，以及纯规则量化推荐。 |
| 指标怎么评估？ | 效果看专家通过率、风险覆盖和约束违反率；效率看 step、token、latency；稳定性看 reroute、critic fail 和格式错误。 |
| 失败 case 是什么？ | 最容易失败在数据过期、用户偏好冲突、政策材料缺失、边界分数段不稳定和报告解释过度。 |

一句话记忆：

> 答任何基础问题，都回到输入、输出、数据流、责任模块、评估信号。

### 14.4 回答顺序模板

推荐顺序：

> 业务问题 -> 输入数据 -> 系统流程 -> 模块责任 -> 实现证据 -> 评估方式 -> 边界不足。

30 秒版本：

> 我把这个项目定义成高约束决策推荐系统，而不是单轮 LLM 问答。用户输入先被抽成 `UserProfile`，再结合历史录取、招生计划和一分一段表生成 `GameMatrix`；之后 risk、opportunity、evidence 三个 advisor 分别审查风险、机会和证据，coordinator 汇总，report 生成结构化报告，critic 最后检查风险覆盖和约束一致性。RL 部分我会保守描述为调度层的 trajectory 采集、reward proxy 和 GRPO-compatible 接入，不会说成完整线上 RLVR。

1 分钟版本：

> 这个项目的核心不是“让 LLM 推荐学校”，而是把高考志愿拆成可约束、可审查、可回放的推荐决策流程。入口层先用 router 判断任务类型，profiling 把自然语言需求转成 `UserProfile`；数据层用历史录取、招生计划和一分一段表生成候选矩阵；协作层让 risk guardian、opportunity advocate 和 evidence guardian 从不同失败模式审查候选；调度层由 supervisor 在有限动作空间里决定 report、deep research、reroute 或 stop；最后 critic 检查报告质量并生成质量信号。评估上我不会说有唯一正确志愿方案，而是用历史事实、专家 rubric、约束一致性、风险覆盖和轨迹成本共同评估。

一句话记忆：

> 先把项目讲成工程系统，再把 agent 和 RL 放进系统里。

### 14.5 不要说 / 应该说

| 不要说 | 应该说 |
| --- | --- |
| 这是完整的生成式推荐算法。 | 这是面向高约束决策场景的生成式推荐式系统，生成的是结构化方案和解释。 |
| 我们做了完整 RLVR。 | 我们没有专门做严格 RLVR，更准确是 trajectory、reward proxy 和 GRPO-compatible 调度优化框架。 |
| agent 自主协商。 | agent 通过结构化 message、vote 和 summary 协作，由 supervisor 统一调度。 |
| LLM 直接推荐学校。 | LLM 只在 schema、证据和 critic 约束下参与抽取、解释、审查和调度。 |
| 有唯一 GT 证明方案正确。 | 录取事实有 GT，方案质量没有唯一 GT，所以用专家评分和多维指标评估。 |
| GRPO 已经证明大幅提升。 | GRPO 的动机是适合组内轨迹比较，现阶段重点是设计可训练接口和评估闭环。 |

一句话记忆：

> 所有夸张说法都降一级，改成可验证、可解释、可承认边界的表述。

### 14.6 面试官继续深挖时的防守线

如果问“你到底写了什么代码？”：

> 我主要负责 LangGraph 主流程、状态 schema、agent 节点、advisor vote 协议、critic 检查逻辑、trace 记录和 RL 调度接口。可以按 `dual_loop_supervisor.py`、`agent_bus.py`、`supervisor_policy.py`、`critic_agent_enhanced.py` 这几块展开。

如果问“这个和推荐算法有什么关系？”：

> 它不是传统召回排序模型，而是高约束场景下的生成式推荐系统：候选生成和风险排序靠结构化数据，LLM 负责把用户偏好、外部证据和最终解释组织成可审查方案。

如果问“没有真实训练是不是包装？”：

> 我会明确区分：工程系统已经实现，RL 部分更偏研究型探索，重点在把多步决策轨迹、奖励信号和 GRPO 接口搭出来，而不是宣称已经完成大规模训练上线。

如果问“为什么可信？”：

> 因为事实部分尽量来自结构化数据和外部证据，生成部分被 schema、advisor、critic 和 reroute 约束，评估也不是只看主观好坏，而是看约束违反、风险覆盖、人工 rubric 和流程成本。

如果问“最大不足是什么？”：

> 最大不足是没有真实用户线上反馈和严格大规模偏好数据，reward 仍然是专家评分与规则 proxy 的组合；下一步应该补真实案例回放、专家 pairwise preference 和更系统的消融实验。

一句话记忆：

> 被深挖时不要硬撑，承认边界，然后把实现证据和下一步改进讲清楚。

## 15. 核心填报链路：到底怎么从输入选出志愿方案

这一节回答最核心的问题：系统不是“让 LLM 想几个学校”，而是把用户条件转成结构化画像，再用历史录取数据生成专业组候选，计算录取概率和风险，最后按冲稳保结构、用户偏好和组合风险选出一组可解释的填报方案。

一句话记忆：

> 先用数据筛可行候选，再用概率分冲稳保，再用偏好和风险做组合选择，最后用报告和 critic 解释并兜底。

### 15.1 一句话讲清填报逻辑

推荐回答：

> 用户输入分数、位次、选科、城市、专业、风险偏好和黑名单后，系统先抽成 `UserProfile`；然后 `game_agent` 从历史录取数据里检索同选科、同位次附近的院校专业组，计算每个专业组的录取概率、预测最低位次、置信区间、位次优势、综合偏好分和调剂风险；再把候选分成冲、稳、保，经过 Pareto 筛选、运行时策略配比和组合优化，形成一组专业组推荐；最后 `report_agent` 生成结构化志愿报告，`critic_agent` 检查保底概率、黑名单风险和冲稳保比例，不合格就回退重算或补充调研。

一句话记忆：

> 画像 -> 候选池 -> 概率 -> 冲稳保 -> 组合优化 -> 报告 -> critic。

### 15.2 输入到底是什么？

| 输入层 | 内容 | 作用 | 对应实现 |
| --- | --- | --- | --- |
| 用户自然语言 | 分数、位次、选科、省份、城市偏好、专业偏好、风险偏好、黑名单专业、体检限制 | 把用户真实需求转成可计算约束 | `profiling_agent.py` |
| 用户画像 | `score`、`rank`、`subject_group`、`preferred_cities`、`excluded_cities`、`preferred_majors`、`blacklist_majors`、`risk_tolerance`、`school_major_preference` | 后续所有推荐步骤的统一 schema | `models/user_profile.py` |
| 历史录取数据 | 院校、专业组、专业、年份、最低位次、招生人数、选科要求 | 作为候选生成和概率估计的事实 grounding | `engines/quant_engine.py` |
| 外部证据 | 招生章程、政策变化、体检限制、特殊专业说明 | 处理结构化数据覆盖不到的约束 | `deep_research` / `multimodal_parser` |

关键防守点：

> 如果用户没有位次，系统不能强行推荐，`game_agent` 会返回“需要提供全省位次”。因为高考志愿的核心坐标是位次，不是裸分。

一句话记忆：

> 分数用于理解，位次用于计算，偏好用于排序，黑名单用于风险控制。

### 15.3 候选学校和专业组怎么来？

第一步：加载和清洗历史数据。

> `GaokaoQuantEngine` 从 data 目录加载 CSV，把院校名称、院校代码、专业、专业组、最低位次、录取人数、年份、选科要求等字段标准化，并按最近年份组织历史数据。

第二步：根据位次确定搜索范围。

> `RankGradientStrategy` 会按用户位次分层。前 5000 名候选池更小，重点看 C9、华五、顶尖 985；中等位次候选池更大，因为学校和专业组合更多；普通位次会扩大保底范围，避免只推荐看起来好但不稳的学校。

第三步：检索专业组候选。

> `engine.search_major_groups(user_rank, subject_group, target_count)` 会在同选科要求下，围绕用户位次找一批历史最低位次接近的专业组。项目按“专业组”推荐，而不是只按学校推荐，因为新高考里专业组才是填报和调剂的基本单位。

第四步：先剔除明显不可用候选。

> 录取概率低于 20% 的专业组会被过滤；全部专业都命中黑名单的专业组会被跳过；无法计算综合评分的专业组也会被跳过。

一句话记忆：

> 候选不是 LLM 编出来的，而是从同选科、同位次附近的历史专业组里检索出来的。

### 15.4 每个候选怎么打分？

| 指标 | 怎么算 | 为什么重要 |
| --- | --- | --- |
| 录取概率 `admission_prob` | 优先用 Monte Carlo 模拟；失败时回退到加权历史位次、MAD 波动和招生规模惩罚 | 判断能不能录取 |
| 预测最低位次 `min_rank_pred` | 基于历史最低位次，近年权重更高 | 解释这个学校大概在哪个位次档 |
| 置信区间 `rank_ci_lower / upper` | 用波动估计给出上下界 | 反映大小年不确定性 |
| 位次差 `rank_diff` | `min_rank_pred - user_rank` | 解释用户相对学校的优势 |
| Z-score | `(预测最低位次 - 用户位次) / 历史波动` | 用相对位次优势划分冲稳保 |
| 综合偏好分 `comprehensive_score` | 学校/专业综合评分与录取概率加权，代码里是综合评分 60% + 录取概率 40% | 不只看稳不稳，也看值不值得 |
| 调剂风险 `adjustment_risk` | 专业组专业数量少时风险更高；黑名单专业会额外惩罚 | 防止被调剂到不想学的专业 |
| 城市偏好分 | 偏好城市加权，排除城市降权 | 让排序贴近用户真实偏好 |

概率估计口径：

> 录取条件可以理解为：如果用户位次优于学校当年的最低录取位次，就有机会录取。系统把学校最低位次当作有波动的随机变量，估计 `P(学校最低位次 >= 用户位次)`，同时用招生规模和历史波动修正不确定性。

一句话记忆：

> 概率看能不能进，综合分看值不值得，调剂风险看能不能接受。

### 15.5 冲稳保怎么划分？

代码里更稳妥的解释不是只用概率阈值，而是优先用 Z-score：

| 档位 | 规则 | 解释 |
| --- | --- | --- |
| 保 `safe` | `Z-score >= 2.0` | 用户位次比学校预测位次好两个历史波动以上，统计上更稳 |
| 稳 `target` | `1.0 <= Z-score < 2.0` | 用户有一定优势，但仍需关注大小年 |
| 冲 `rush` | `Z-score < 1.0` | 用户优势不足或接近边界，属于机会型选择 |

为什么不用固定概率说死：

> 不同学校历史波动不同，同样 80% 概率在稳定学校和大小年明显学校里的含义不一样。Z-score 能把学校波动纳入考虑，更适合解释“为什么这个算稳，那个算冲”。

一句话记忆：

> 冲稳保不是拍脑袋，是看用户位次比学校历史线强多少个波动单位。

### 15.6 最终怎么从候选里选一组？

第一层：保留保底候选。

> 代码会先把 `safe` 类专业组保留下来，不让 Pareto 过滤误删保底，因为保底是填报安全底线。

第二层：Pareto 过滤非保底候选。

> 对非保底候选做多目标筛选：最大化录取概率、最大化综合评分、最小化调剂风险。这样可以去掉“录取概率低、综合质量低、调剂风险还高”的被支配解。

第三层：运行时策略决定冲稳保配比。

> `RLRuntimePolicy` 会根据风险偏好调整比例。激进用户多给冲刺，保守用户增加保底；同时结合学校/专业偏好调整 prestige weight 和 major satisfaction weight。

第四层：贪心重排与多样性控制。

> `_policy_score` 会综合考虑录取概率适配度、学校/专业综合分、安全性、调剂风险、黑名单惩罚和城市多样性，避免推荐结果集中在同一城市或同一类风险上。

第五层：组合优化。

> `VolunteerCombinationOptimizer` 会在候选中构造多种组合风格，例如更稳、更均衡、更看重专业满意度，再根据用户风险偏好和学校/专业偏好选择最终组合。保守型优先选保底更多、平均录取概率更高的组合；专业优先型更看重专业满意度；学校优先型更看重学校层次。

一句话记忆：

> 先保安全底线，再筛掉被支配候选，最后按用户风险偏好选组合。

### 15.7 输出到底是什么？

| 输出对象 | 内容 | 面试回答方式 |
| --- | --- | --- |
| `GameMatrix` | 一组专业组候选，每个候选含学校、专业组、专业列表、录取概率、预测位次、置信区间、冲稳保标签、调剂风险、综合分 | 这是推荐核心结果，不是自然语言报告 |
| 组合统计 | 冲、稳、保数量，期望效用，组合风险，是否均衡，selection method | 用于解释方案结构和风险 |
| `ReportDraft` | 执行摘要、策略分析、院校推荐、风险警示、遗憾值分析 | 给用户看的最终报告 |
| `AuditResult` | critic 是否通过、问题列表、是否回退到 game/report/profile/deep research | 保证不合格结果不会直接输出 |

报告里应该有什么：

> 不是只列学校名，而是要说明每个推荐的录取概率、策略标签、专业组、调剂风险、为什么适合用户、哪些风险需要人工复核。

一句话记忆：

> 内部输出是 `GameMatrix`，用户看到的是经过解释和审计的 `ReportDraft`。

### 15.8 从输入到输出的完整链路

| 步骤 | 输入 | 处理 | 输出 | 失败时怎么办 |
| --- | --- | --- | --- | --- |
| 1. Router | 用户 query | 判断是量化推荐、深度调研、多模态还是混合任务 | next_action | 不确定则进入 profiling 或 research |
| 2. Profiling | 自然语言需求 | 抽取分数、位次、选科、偏好、黑名单、风险偏好 | `UserProfile` | 缺关键字段则要求补充 |
| 3. Candidate Search | `UserProfile` + 历史 CSV | 按位次层级和选科要求检索专业组 | 候选池 | 找不到则扩大或提示无匹配 |
| 4. Probability | 候选专业组历史数据 | Monte Carlo / fallback 概率估计 | 录取概率、预测位次、CI、Z-score | 失败则跳过或 fallback |
| 5. Filtering | 候选指标 | 过滤低概率、全黑名单、无评分候选 | 可用候选 | 候选不足则触发风险提示 |
| 6. Tagging | 概率 + Z-score | 划分冲、稳、保 | strategy_tag | 用概率阈值兜底 |
| 7. Scoring | 专业、学校、城市、偏好 | 算综合分、城市调整、黑名单惩罚 | comprehensive_score | 评分失败则跳过该专业组 |
| 8. Pareto | 非保底候选 | 多目标筛选 | 非支配候选 | 保底候选单独保留 |
| 9. Mix Policy | 候选 + 风险偏好 | 决定冲稳保数量 | 推荐配比 | checkpoint 不存在则默认策略 |
| 10. Portfolio | 已选候选 | 组合优化和风格选择 | 最终推荐组合 | 优化失败则按综合分 fallback |
| 11. Report | `GameMatrix` | 生成结构化报告 | `ReportDraft` | LLM 失败则 fallback report |
| 12. Critic | 报告 + 矩阵 + 画像 | 检查保底、黑名单、比例和风险说明 | PASS 或 reroute | 回退 game/report/profile/research |

一句话记忆：

> 每一步都有输入、输出和失败处理，所以这不是单次生成，而是一条可审计的推荐流水线。

### 15.9 面试官问“你到底怎么帮用户填志愿”的 30 秒回答

> 我们真正做的是专业组级别的志愿组合推荐。用户先输入分数、位次、选科、城市和专业偏好，系统抽成 `UserProfile`；然后基于历史录取、招生计划和一分一段数据，在同选科和相近位次范围内检索候选专业组；每个候选会计算录取概率、预测最低位次、位次置信区间、Z-score、综合偏好分和调剂风险，再按 Z-score 分成冲稳保。最后系统会保留保底底线，对非保底候选做 Pareto 筛选，再根据用户风险偏好做冲稳保配比和组合优化，生成一组专业组方案和风险解释；critic 会检查保底概率、黑名单调剂风险和报告完整性，不通过就回退重算。

一句话记忆：

> 我不是让模型“想学校”，而是让模型围绕结构化候选、概率和风险生成可解释方案。

### 15.10 面试官继续深挖时怎么回答

如果问“为什么按专业组而不是学校？”：

> 新高考填报和调剂的基本单位是院校专业组，同一学校不同专业组的选科要求、录取位次和调剂风险都不同。按学校推荐会掩盖专业组之间的风险差异。

如果问“怎么防止只推荐名校冷门专业？”：

> 排序不是只看学校层次，而是综合专业满意度、录取概率、调剂风险、黑名单惩罚和用户的学校/专业权衡偏好。专业优先型用户会提高专业满意度权重，学校优先型才提高学校层次权重。

如果问“怎么保证不滑档？”：

> 不能保证绝对不滑档，只能降低风险。系统用 Z-score 和录取概率识别保底，critic 要求保底候选存在且保底概率足够高；如果保底不足，会回退到 `game_agent` 扩大搜索或在报告里给强风险提示。

如果问“录取概率靠谱吗？”：

> 概率不是绝对预测，而是基于历史最低位次、招生规模和波动估计的风险信号。项目里优先用 Monte Carlo 模拟大小年和不确定性，失败时用加权历史位次、MAD 波动和招生规模惩罚兜底。

如果问“RL 在选择学校里起什么作用？”：

> 这里不要说 RL 决定学校事实。学校事实和录取概率来自结构化数据；RL runtime policy 主要影响候选组合的配比和重排，比如冲稳保比例、风险偏好、城市多样性和学校/专业权衡。

如果问“最终用户拿到什么？”：

> 用户拿到的是一份结构化志愿建议书，包括候选专业组、冲稳保结构、每个候选的录取概率和调剂风险、组合风险分析、黑名单或证据不足警告，以及需要人工复核的招生章程信息。

一句话记忆：

> 学校事实靠数据，组合选择靠策略，解释和兜底靠 report + critic。

## 16. 按架构图介绍项目：端到端链路和 Agent 职责

这一节对应你画的架构图。面试时不要一上来讲“我有很多 agent”，而是先讲这是一个从前端请求到后端决策图再到结构化报告的系统：FastAPI 负责接入，Supervisor 负责调度，Router / Profiling / Game 负责主推荐链路，三个 Advisor 负责候选后的并行审查，Coordinator 汇总意见，Report 生成报告，Critic 做质量闸门，Deep Research 处理证据不足或政策不确定的慢路径。

一句话记忆：

> 前端进来，FastAPI 建状态，Supervisor 调度，Game 产候选，Advisor 审方案，Report 写报告，Critic 决定通过或回退。

### 16.1 先用 20 秒讲清这张图

推荐回答：

> 这张图展示的是我的端到端志愿推荐系统。用户从前端提交分数、位次、选科和偏好后，FastAPI 把请求封装成 `SupervisorState`，交给 LangGraph 里的 Supervisor。Supervisor 先让 Router 判断任务类型，再走 Profiling 抽用户画像，Game 基于历史录取数据生成专业组候选和冲稳保组合；候选出来后，Risk / Opportunity / Evidence 三个 Advisor 并行审查风险、机会和证据充分性，Coordinator 汇总投票，再由 Supervisor 决定是生成报告还是进入 Deep Research。Report 生成结构化报告后，Critic 检查保底风险、黑名单调剂和报告完整性，不通过就回退到 Game、Report 或 Research。

一句话记忆：

> 这张图讲的是“可调度、可审查、可回退”的志愿推荐流水线。

### 16.2 分层讲：不要把所有框都叫 agent

| 层级 | 图中组件 | 作用 | 面试说法 |
| --- | --- | --- | --- |
| 交互层 | User / Frontend | 收集用户输入，展示报告、候选矩阵和调试信息 | 不是 agent，是产品入口 |
| API 层 | FastAPI | 参数校验、速率限制、构造 `HumanMessage` 和 `SupervisorState`，调用图执行 | 不是 agent，是服务入口 |
| 调度层 | Supervisor | 根据 state 和上一轮结果选择下一步节点 | 控制器，不是业务 agent |
| 主推荐链 | Router / Profiling / Game | 判断任务、抽画像、生成候选专业组 | 推荐结果的主干 |
| 并行审查层 | Risk / Opportunity / Evidence Advisor | 分别审查风险、机会和证据 | 多 agent 的核心价值 |
| 聚合层 | Coordinator | 汇总 advisor vote，形成下一步建议 | 把分歧变成可执行动作 |
| 慢思考层 | Deep Research | 对政策、章程、证据缺口做外部调研 | 只在需要时触发 |
| 生成层 | Report | 生成结构化志愿建议书 | 面向用户的最终文本 |
| 审计层 | Critic | 检查风险、约束、报告质量，决定通过或回退 | 最终质量闸门 |

一句话记忆：

> FastAPI 是入口，Supervisor 是调度器，agent 是做具体判断和生成的节点。

### 16.3 到底几个 agent？

按你这张图讲，核心业务节点是 10 个：

> Router、Profiling、Game、Risk Advisor、Opportunity Advisor、Evidence Advisor、Coordinator、Deep Research、Report、Critic。

按代码完整版讲，是 11 个 agent-like 节点：

> 上面 10 个之外，还有 `multimodal_parser`，用于处理 PDF、招生章程截图、体检限制等多模态或非结构化材料。

同时还有 4 个 Supervisor 决策点：

> `supervisor_after_profiling`、`supervisor_after_game`、`supervisor_after_report`、`supervisor_after_critic`。它们不算业务 agent，而是调度策略节点。

面试稳妥说法：

> 如果按图讲，我会说 10 个核心业务节点；如果按代码实现讲，是 11 个 agent-like 节点加 4 个 supervisor decision nodes。Supervisor 本身是调度层，不和业务 agent 混在一起数。

一句话记忆：

> 图里 10 个核心节点，代码里 11 个 agent-like 节点，另有 4 个 supervisor 决策点。

### 16.4 从输入到输出按图完整走一遍

| 阶段 | 节点 | 输入 | 具体做什么 | 输出 |
| --- | --- | --- | --- | --- |
| 1 | User / Frontend | 用户自然语言、分数、位次、选科、偏好 | 收集请求并提交给后端 | `QueryRequest` |
| 2 | FastAPI | `QueryRequest` | 校验字段、限流、拼接用户消息、初始化 `SupervisorState` | 初始 state |
| 3 | Supervisor | 初始 state | 调用图的入口节点，记录 trace，准备调度 | next action |
| 4 | Router | 用户 query | 判断是量化推荐、深度调研、多模态解析还是混合任务 | intent / active_loop / next_action |
| 5 | Profiling | query + message history | 抽取分数、位次、选科、城市偏好、专业偏好、黑名单、风险偏好 | `UserProfile` |
| 6 | Game | `UserProfile` + 历史录取数据 | 检索专业组候选，估计录取概率，划分冲稳保，做组合选择 | `GameMatrix` |
| 7 | Risk Advisor | `GameMatrix` | 检查保底数量、组合风险、滑档风险 | vote: report 或 research |
| 8 | Opportunity Advisor | `GameMatrix` | 检查是否过保守、是否缺少冲刺机会、期望效用是否太低 | vote: report 或 research |
| 9 | Evidence Advisor | intent + research state | 检查是否需要外部证据、政策信息是否已补足 | vote: report 或 research |
| 10 | Coordinator | 三个 advisor 的 vote | 加权汇总 action preference、confidence 和分歧 | `DeliberationSummary` |
| 11 | Supervisor | summary + state | 决定走 Report，还是先 Deep Research | next action |
| 12 | Deep Research | research topic / evidence gap | 对招生章程、政策、特殊限制做慢路径调研 | research report |
| 13 | Report | profile + matrix + research context | 生成执行摘要、策略分析、院校推荐、风险警示 | `ReportDraft` |
| 14 | Critic | report + matrix + profile | 检查保底概率、黑名单风险、冲稳保比例、报告完整性 | PASS / reroute |
| 15 | FastAPI Response | final state | 把报告、矩阵、画像、trace、agent messages 返回前端 | `QueryResponse` |

一句话记忆：

> 这条链路每一步都有结构化输入输出，不是 prompt 串联。

### 16.5 每个 agent 具体做什么、怎么实现

| Agent | 实现位置 | 核心输入 | 核心输出 | 实现方式 | 为什么需要 |
| --- | --- | --- | --- | --- | --- |
| Router | `agents/router_agent.py` | 用户 query | intent、active_loop、next_action | LLM / 规则辅助意图分类，判断 fast / slow / multimodal | 先决定走量化、调研还是混合链路 |
| Profiling | `agents/profiling_agent.py` | 用户 query、历史消息 | `UserProfile` | structured output 抽取 schema 字段 | 把自然语言变成可计算约束 |
| Game | `agents/game_agent.py` | `UserProfile`、历史录取 CSV | `GameMatrix` | 数据检索、Monte Carlo 概率、Z-score 冲稳保、Pareto、runtime policy | 这是推荐核心，负责选专业组 |
| Risk Advisor | `agents/deliberation_agents.py` | `GameMatrix` | risk vote | 检查 candidate_count、safe_count、portfolio_risk | 防止滑档、保底不足 |
| Opportunity Advisor | `agents/deliberation_agents.py` | `GameMatrix` | opportunity vote | 检查 rush_count、expected_utility | 防止方案过保守 |
| Evidence Advisor | `agents/deliberation_agents.py` | intent、research state | evidence vote | 检查 requires_search 和 search_done | 防止证据不足就生成报告 |
| Coordinator | `agents/deliberation_agents.py` | advisor messages | `DeliberationSummary` | 汇总 vote_scores、dissent_count、consensus_strength | 把多方意见变成一个可执行建议 |
| Deep Research | `agents/deep_research_agent.py` / `subgraphs` | research topic | research report | plan-execute-reflect-synthesize 慢路径调研 | 补政策、章程、外部证据 |
| Report | `agents/report_agent.py` | profile、matrix、research context | `ReportDraft` | structured LLM 生成，失败时 fallback report | 把矩阵变成用户能读的建议书 |
| Critic | `agents/critic_agent_enhanced.py` | report、matrix、profile | `AuditResult`、step rewards | 规则审计 + reroute 建议 | 质量闸门，避免坏结果直接输出 |
| Multimodal Parser | `agents/multimodal_agent.py` | PDF、章程、视觉结果 | parsed constraints | 解析非结构化或多模态约束 | 处理图里没画出的辅助分支 |

一句话记忆：

> Router 定路线，Profiling 建画像，Game 产方案，Advisor 审风险，Coordinator 汇总，Report 表达，Critic 兜底。

### 16.6 Supervisor 怎么实现？

推荐回答：

> Supervisor 不是一个自由聊天的 agent，而是 LangGraph 的控制层。代码里用 `StateGraph(SupervisorState)` 注册节点和条件边，主入口是 `START -> router_agent`。每个 agent 执行后都会更新 `SupervisorState`，然后 `supervisor_after_*` 节点根据当前 state 选择下一步，比如从 profiling 后去 game 或 deep research，从 game 后去 report 或 deep research，从 critic 后结束或回退到 game / report / profiling / research。

代码锚点：

> 图结构在 `backend/src/graph/dual_loop_supervisor.py`；状态定义在 `models/state.py`；调度策略在 `rl/supervisor_policy.py`；FastAPI 在 `backend/src/main.py` 调用 `supervisor_graph.invoke(initial_state, config={"recursion_limit": 50})`。

一句话记忆：

> Supervisor 的本质是状态机调度，不是让大模型随便决定一切。

### 16.7 Agent 之间怎么通信？

推荐回答：

> 通信不是开放式群聊，而是结构化协议。Game 生成候选后，会通过 `publish_agent_message` 给三个 advisor 发送 proposal；三个 advisor 各自写入 vote，字段包括 sender、stage、message_type、action_preference、confidence 和 metadata；Coordinator 用 `get_messages_for_stage` 读取这些 vote，汇总成 `DeliberationSummary`，再写回 state 给 Supervisor 使用。

核心数据结构：

| 结构 | 字段 | 作用 |
| --- | --- | --- |
| `AgentMessage` | sender、recipients、stage、message_type、content、action_preference、confidence、references、metadata | agent 之间传递结构化意见 |
| `AgentMemoryEntry` | agent_name、stage、note_type、content、importance | 保存每个 agent 的局部记忆 |
| `DeliberationSummary` | recommended_action、vote_scores、dissent_count、consensus_strength、requires_research | 汇总并行 advisor 的最终建议 |

一句话记忆：

> agent 通信用 message，分歧汇总用 summary，调度决策回到 supervisor。

### 16.8 Game Agent 是怎么真正选志愿的？

推荐回答：

> Game Agent 是整个系统里最像推荐算法核心的部分。它先根据用户位次和选科，从历史数据里搜索专业组候选；然后对每个专业组取最近几年最低位次和招生人数，用 Monte Carlo 或 fallback 概率模型估计录取概率、预测最低位次、置信区间和 Z-score；再根据 Z-score 分冲稳保，计算学校专业综合分、城市偏好、黑名单惩罚和调剂风险；之后保留保底候选，对非保底候选做 Pareto 筛选；最后用 runtime policy 根据用户风险偏好选择冲稳保配比，并用组合优化形成最终专业组方案。

核心公式口径：

> 录取概率可以解释为 `P(学校最低录取位次 >= 用户位次)`；Z-score 可以解释为 `(预测最低位次 - 用户位次) / 历史波动`。Z-score 越高，说明用户位次相对学校历史线越安全。

一句话记忆：

> Game Agent 先算“能不能进”，再算“值不值得”，最后算“组合安不安全”。

### 16.9 Deep Research 什么时候触发？

触发条件：

| 触发来源 | 条件 | 目的 |
| --- | --- | --- |
| Router | 用户问题本身需要政策、学校资料、招生章程 | 先调研再报告 |
| Risk Advisor | 候选不足、无保底、组合风险高 | 补充边界情况证据 |
| Opportunity Advisor | 没有冲刺机会且期望效用偏低 | 查找是否有被遗漏机会 |
| Evidence Advisor | intent 要求搜索但还没完成搜索 | 避免证据不足 |
| Critic | 报告或推荐存在逻辑问题 | 回退修正 |

推荐回答：

> Deep Research 不是每次都跑，因为成本高、延迟长。它只在证据不足、政策不确定、候选异常或 critic 回退时触发。这样能把常规推荐保持在 fast loop，把复杂问题交给 slow loop。

一句话记忆：

> 常规问题走 fast loop，证据不足才走 deep research。

### 16.10 Critic 怎么兜底？

Critic 主要查三类问题：

| 检查项 | 规则 | 不通过怎么办 |
| --- | --- | --- |
| 保底风险 | 是否存在 safe 候选，保底概率是否足够高 | 回退 `game_agent` 扩大或重算候选 |
| 黑名单调剂 | 是否有候选可能调剂到用户不想学的专业 | 回退 `report_agent` 补充明确风险警告 |
| 冲稳保比例 | 组合是否明显失衡 | 给出 warning 或建议调整 |

推荐回答：

> Critic 不负责重新推荐学校，而是做质量闸门。它看报告有没有把风险讲清楚，看矩阵里有没有保底不足和黑名单调剂问题。如果风险严重，就通过 supervisor 回退到对应节点，而不是让有问题的报告直接给用户。

一句话记忆：

> Critic 是质量闸门，不是另一个推荐器。

### 16.11 3 分钟项目介绍完整版

> 我这个项目是一个面向高考志愿填报的多智能体决策推荐系统，核心目标不是让 LLM 随便生成学校，而是把“分数位次、专业偏好、城市偏好、风险偏好、调剂风险、招生政策”这些因素组织成一个可计算、可审查、可回退的推荐流程。系统入口是前端和 FastAPI，用户提交分数、位次、选科和偏好后，FastAPI 会做参数校验、限流和消息拼接，然后构造 `SupervisorState` 调用 LangGraph。
>
> 进入图以后，Supervisor 先调 Router 判断任务类型。如果是常规志愿推荐，就走 fast loop：Profiling 把自然语言抽成 `UserProfile`，包括 score、rank、subject_group、preferred_cities、preferred_majors、blacklist_majors、risk_tolerance 等字段；Game Agent 再基于历史录取数据生成专业组级别的 `GameMatrix`。这里推荐单位是专业组，不是学校，因为新高考填报和调剂都是专业组维度。Game 会先按同选科和相近位次检索候选，再对每个专业组计算录取概率、预测最低位次、置信区间、Z-score、综合评分和调剂风险，然后按 Z-score 分成冲、稳、保。最终选择不是简单排序，而是先保留保底候选，对非保底候选做 Pareto 筛选，再根据用户风险偏好用 runtime policy 调整冲稳保配比，并通过组合优化形成最终推荐。
>
> Game 之后不是直接生成报告，而是进入并行审查。Risk Advisor 看保底数量和组合风险，Opportunity Advisor 看方案是否过保守、有没有机会空间，Evidence Advisor 看是否缺外部证据。三个 advisor 都通过结构化 `AgentMessage` 给出 action_preference 和 confidence，Coordinator 汇总成 `DeliberationSummary`，交给 Supervisor 决定下一步。如果证据不足或风险异常，就进 Deep Research；如果可以生成，就进 Report。
>
> Report Agent 会把 `UserProfile`、`GameMatrix` 和 research context 生成结构化 `ReportDraft`，包括执行摘要、策略分析、院校推荐、风险警示和遗憾值分析。最后 Critic 做质量审计，检查保底概率、黑名单调剂、冲稳保比例和报告完整性。如果不通过，Supervisor 会回退到 Game、Report、Profiling 或 Deep Research。最终 FastAPI 把 report、game_matrix、user_profile、orchestration_trace、agent_messages 和 deliberation_summaries 返回前端。所以这个系统的关键点是：推荐依据来自结构化数据，agent 负责分工审查和解释，Supervisor 负责调度和回退。

一句话记忆：

> 这是一个“数据生成候选、agent 审查风险、supervisor 控制回退”的志愿推荐系统。

### 16.12 面试官按图追问时的短答

如果问“这张图里最核心的是哪个节点？”：

> 最核心的是 Game Agent，因为它真正把用户画像和历史录取数据转成专业组候选、概率、冲稳保和组合推荐；其他 agent 主要围绕它做路由、审查、解释和兜底。

如果问“为什么需要 Supervisor？”：

> 因为流程不是固定线性链路。profiling 之后可能缺信息，game 之后可能证据不足，critic 之后可能要回退。Supervisor 把这些分支显式建成状态机，保证每次跳转可记录、可解释。

如果问“为什么 Game 后面要三个 Advisor？”：

> 因为推荐方案的风险不是单一维度。Risk 看下行风险，Opportunity 看上行机会，Evidence 看证据充分性。拆开后每个审查视角的责任更清楚，也方便把 vote 记录成可回放轨迹。

如果问“Coordinator 有什么用？”：

> Coordinator 把三个 advisor 的 action_preference 和 confidence 汇总成一个 `DeliberationSummary`。没有它，Supervisor 只能读到零散意见；有了它，分歧会被量化成 vote_scores、dissent_count 和 consensus_strength。

如果问“Report 和 Critic 有什么区别？”：

> Report 负责表达，把矩阵和上下文变成用户能读的建议书；Critic 负责审计，检查报告有没有漏风险、保底是否不足、黑名单是否说明清楚。一个生成，一个把关。

如果问“Deep Research 和 Evidence Advisor 区别是什么？”：

> Evidence Advisor 是判断是否缺证据的轻量审查节点，Deep Research 是真正去补证据的慢路径执行节点。

如果问“你的 RL 在这张图里在哪里？”：

> 主要在两个位置：一是 Supervisor 的调度轨迹可以被记录成 trajectory，用于后续 reward 和 GRPO-compatible 训练；二是 Game 里的 runtime policy 会影响冲稳保配比、风险偏好和候选重排。但学校事实和录取概率本身仍然来自结构化数据。

一句话记忆：

> 被追问时围绕 Game、Advisor、Coordinator、Critic、Supervisor 五个关键词展开。

## 17. Harness Engineer 视角：把复杂 Agent 图讲成可控执行框架

这一节解决一个实际问题：如果你按原图从 Router、Profiling、Game、Advisor、Coordinator、Report、Critic 一路讲，很容易把自己绕进去。更稳的讲法是把项目定位成一个面向高风险推荐任务的 Agent Harness：你不是只做“推荐模型”，而是搭了一个能接请求、建状态、调度 agent、记录轨迹、评估输出、失败回退的执行框架。

一句话记忆：

> 不要先讲十几个节点，先讲我搭了一个可执行、可观测、可评估、可回退的 agent harness。

### 17.1 什么叫 Harness Engineer 视角？

推荐回答：

> Harness Engineer 视角不是强调“我用了多少个 agent”，而是强调我怎么把不稳定的 LLM / agent 能力包装成一个稳定工程系统。这个系统要有 typed state、明确的执行图、工具和数据接入、可观测 trace、自动评估、失败回退和最终结构化输出。对高考志愿这种高风险场景，harness 的价值就是把生成式能力关进一个可控流程里。

| 普通 Agent 讲法 | Harness Engineer 讲法 |
| --- | --- |
| 我有 Router、Profiling、Game、Report、Critic 很多 agent | 我设计了一个多阶段 execution harness，每个节点有明确输入输出 |
| Agent 之间协作生成推荐 | 节点通过 typed state 和 structured message 通信 |
| Critic 检查结果 | Evaluation gate 负责质量闸门和 reroute |
| RL 优化流程 | 轨迹、reward proxy 和策略接口被设计成可训练 harness |
| 最终生成报告 | 输出经过 schema、risk check 和 fallback 才返回前端 |

一句话记忆：

> Harness 的核心不是“agent 多”，而是“流程受控”。

### 17.2 新流程图只画 5 个盒子

以后面试主图建议改成这个：

> User / Frontend -> API Adapter -> Agent Execution Harness -> Domain Executors -> Evaluation Gate -> Structured Response

更细一点：

| 简化模块 | 包含什么 | 一句话解释 |
| --- | --- | --- |
| API Adapter | Frontend、FastAPI、QueryRequest、rate limit | 把用户请求变成可执行 state |
| Agent Execution Harness | Supervisor、LangGraph、SupervisorState、routing policy、trace | 控制执行顺序、分支和回退 |
| Domain Executors | Profiling、Game、Deep Research、Report、Multimodal | 真正完成画像、推荐、调研和报告 |
| Evaluation Gate | Risk Advisor、Opportunity Advisor、Evidence Advisor、Coordinator、Critic | 审查风险、证据、机会和报告质量 |
| Structured Response | ReportDraft、GameMatrix、UserProfile、orchestration_trace | 返回报告、矩阵、画像和可观测信息 |

一句话记忆：

> 主图只讲 5 个盒子，agent 明细只在追问时展开。

### 17.3 你应该怎么改原来的流程图？

不要再画所有节点之间的细箭头。改成两层图：

第一层：主链路。

> `User -> FastAPI -> Harness / Supervisor -> Recommendation Core -> Evaluation Gate -> Response`

第二层：模块展开。

> Recommendation Core 里面再展开 `Profiling + Game + Deep Research + Report`；Evaluation Gate 里面再展开 `Risk Advisor + Opportunity Advisor + Evidence Advisor + Coordinator + Critic`。

推荐图结构：

| 大模块 | 子模块 | 不在主图里展开的原因 |
| --- | --- | --- |
| Harness / Supervisor | Router、supervisor_after_*、trace recorder | 这些是控制逻辑，不是用户直接关心的业务步骤 |
| Recommendation Core | Profiling、Game、Deep Research、Report | 这是主业务能力，可以作为第二层展开 |
| Evaluation Gate | 三个 Advisor、Coordinator、Critic | 这是质量保障能力，适合统一讲 |
| Observability | debug_logs、agent_messages、deliberation_summaries、orchestration_trace | 面试官深挖工程性时再讲 |

一句话记忆：

> 主图讲主链路，展开图讲模块，表格讲 agent。

### 17.4 按 Harness 视角重新介绍项目

30 秒版本：

> 我这个项目可以理解成一个面向高考志愿推荐的 Agent Execution Harness。前端请求进入 FastAPI 后，会被封装成 typed `SupervisorState`，然后 LangGraph Supervisor 调度不同执行节点：Profiling 抽用户画像，Game 用历史录取数据生成专业组候选和冲稳保组合，Deep Research 处理证据不足的慢路径，Report 生成结构化建议书。系统不是直接把结果返回，而是经过 Risk / Opportunity / Evidence Advisor 和 Critic 做评估，必要时回退重算。我的重点工作是把推荐、调度、评估、trace 和 fallback 组织成一个可控闭环。

90 秒版本：

> 我不会把这个项目描述成“很多 agent 串起来”，而是一个 agent harness。第一层是 API adapter，FastAPI 做参数校验、限流，把分数、位次、选科和用户偏好拼成请求，并初始化 `SupervisorState`。第二层是 execution harness，基于 LangGraph `StateGraph` 注册节点和条件边，Supervisor 根据 state 选择下一步，并记录 orchestration trace。第三层是 domain executor，Profiling 抽 `UserProfile`，Game Agent 基于历史录取数据生成 `GameMatrix`，包括录取概率、Z-score、冲稳保、综合分和调剂风险；Deep Research 用于处理政策和证据缺口；Report 生成 `ReportDraft`。第四层是 evaluation gate，三个 advisor 从风险、机会、证据三个角度给 vote，Coordinator 汇总分歧，Critic 最后检查保底、黑名单和报告完整性。最后 FastAPI 返回 report、game_matrix、user_profile、trace 和 agent messages。所以这个系统的工程价值是：让 LLM 参与决策，但所有步骤都被 state、schema、trace、eval 和 reroute 约束住。

一句话记忆：

> 我做的不是“让模型推荐学校”，而是“把推荐 agent 放进一个可控 harness 里运行”。

### 17.5 Harness 里每一层怎么实现？

| Harness 层 | 代码锚点 | 你负责讲什么 |
| --- | --- | --- |
| API Adapter | `backend/src/main.py` | `QueryRequest` 校验、速率限制、构造 `HumanMessage`、初始化 `SupervisorState`、调用 graph |
| Typed State | `models/state.py`、`models/user_profile.py`、`models/game_matrix.py`、`models/report.py` | 所有节点共享 state，不靠隐式 prompt 传参 |
| Graph Orchestrator | `graph/dual_loop_supervisor.py` | `StateGraph`、节点注册、条件边、recursion limit、reroute |
| Supervisor Policy | `rl/supervisor_policy.py` | after_profiling / after_game / after_report / after_critic 如何选择 next_action |
| Domain Executor | `agents/profiling_agent.py`、`agents/game_agent.py`、`agents/deep_research_agent.py`、`agents/report_agent.py` | 画像、候选生成、调研、报告 |
| Agent Protocol | `utils/agent_bus.py`、`models/agent_communication.py` | `AgentMessage`、`AgentMemoryEntry`、`DeliberationSummary` |
| Evaluation Gate | `agents/deliberation_agents.py`、`agents/critic_agent_enhanced.py` | advisor vote、coordinator 聚合、critic 审计 |
| Observability | `orchestration_trace`、`debug_logs`、`agent_messages`、`deliberation_summaries` | 怎么回放、排查和评估一次运行 |
| Recovery | `route_after_critic`、`audit.reroute_to` | 不通过时回退到 game/report/profile/research |

一句话记忆：

> Harness 的实现证据是 state、graph、protocol、eval、trace、reroute。

### 17.6 原来的 Agent 应该怎么放进新图？

| 新图模块 | 放哪些旧节点 | 面试展开顺序 |
| --- | --- | --- |
| API Adapter | User / Frontend、FastAPI | 只讲输入校验和 state 初始化 |
| Agent Execution Harness | Supervisor、Router、supervisor_after_* | 讲 LangGraph、条件路由、trace |
| Recommendation Core | Profiling、Game、Deep Research、Report、Multimodal | 先讲 Game，再补 Profiling / Research / Report |
| Evaluation Gate | Risk Advisor、Opportunity Advisor、Evidence Advisor、Coordinator、Critic | 先讲 Critic，再讲三个 advisor |
| Response / Observability | QueryResponse、debug_logs、agent_messages、trace | 最后讲可观测和回放 |

推荐展开顺序：

> 先讲 `Game`，因为它是真推荐核心；再讲 `Supervisor`，因为它解释为什么流程可控；再讲 `Critic / Advisor`，因为它解释为什么输出可信；最后讲 `Trace / Reward`，因为它解释为什么能评估和优化。

一句话记忆：

> 展开时先业务核心，再调度，再评估，最后观测。

### 17.7 面试官如果是 Harness Engineer，会怎么问？

| 追问 | 他们真正关心 | 稳妥回答 |
| --- | --- | --- |
| 你怎么保证 agent 输出稳定？ | schema、state、fallback | 用 structured output、typed state、fallback report 和 critic gate 限制输出 |
| agent 失败了怎么办？ | recovery | supervisor 根据 audit reroute 到 game/report/profile/research |
| 怎么 debug 一次错误运行？ | observability | 看 orchestration_trace、debug_logs、agent_messages、deliberation_summaries |
| 怎么评估一次运行好不好？ | eval harness | 看保底概率、黑名单风险、约束满足、report warning、专家 rubric 和 reward proxy |
| 怎么避免 prompt 串联不可控？ | orchestration | 用 LangGraph `StateGraph` 和条件边显式控制每一步 |
| 多 agent 怎么通信？ | protocol | 通过 `AgentMessage` 和 `DeliberationSummary`，不是自然语言群聊 |
| 怎么接入新工具或新 agent？ | extensibility | 新节点只要读写 `SupervisorState`，再接入 graph 和 policy |
| RL 在 harness 里怎么用？ | trainable interface | 先记录 trajectory 和 reward proxy，再把 supervisor decision 设计成可训练策略 |

一句话记忆：

> Harness 面试官关心稳定性、可观测、可评估、可恢复、可扩展。

### 17.8 你应该删减哪些说法？

不要优先说：

> 我做了一个 11 个 agent 的复杂多智能体系统。

改成：

> 我做了一个可控的 agent execution harness，里面有若干 domain executor 和 evaluation agent。

不要优先说：

> Supervisor 连到很多 agent，agent 之间互相协作。

改成：

> Supervisor 维护 typed state，通过条件边调度节点；agent 之间通过结构化 message 写入 state。

不要优先说：

> RL 优化了整个推荐。

改成：

> 当前 RL 更准确说是 harness 里的调度轨迹、reward proxy 和 runtime policy 接口，学校事实和概率仍来自结构化数据。

不要优先说：

> Deep Research、Advisor、Critic 都很重要。

改成：

> 常规请求只走主链路；当证据不足、风险异常或 critic 不通过时，才触发 research 或 reroute。

一句话记忆：

> 所有复杂名词都降级成工程职责。

### 17.9 新版最简流程图口述

你可以在白板上只画这 5 个框：

> `Input Adapter -> Execution Harness -> Recommendation Core -> Evaluation Gate -> Structured Output`

每个框一句话：

| 框 | 一句话 |
| --- | --- |
| Input Adapter | FastAPI 把用户请求变成 typed state |
| Execution Harness | Supervisor 用 LangGraph 调度节点、记录 trace、处理回退 |
| Recommendation Core | Profiling + Game + Research + Report 完成画像、候选、调研和报告 |
| Evaluation Gate | Advisor + Coordinator + Critic 检查风险、证据、分歧和报告质量 |
| Structured Output | 返回报告、候选矩阵、用户画像、轨迹和调试信息 |

如果面试官要求展开，再画第二层：

> Recommendation Core = `Profiling -> Game -> Report`，必要时接 `Deep Research`。Evaluation Gate = `Risk / Opportunity / Evidence -> Coordinator -> Critic`。

一句话记忆：

> 白板只画 5 框，追问再展开 agent。

### 17.10 1 分钟最终版：按 Harness Engineer 讲

> 我现在会把这个项目讲成一个 agent harness，而不是单纯的多 agent demo。用户请求从前端进入 FastAPI 后，先被校验并封装成 `SupervisorState`；LangGraph Supervisor 负责调度和回退，所有节点都读写同一个 typed state。业务执行层里，Profiling 抽用户画像，Game 基于历史录取数据生成专业组候选、录取概率、Z-score、冲稳保和组合推荐，Report 把结果写成结构化建议书，Deep Research 只在证据不足时触发。评估层里，Risk / Opportunity / Evidence 三个 advisor 审查候选，Coordinator 汇总 vote，Critic 最后检查保底、黑名单和报告完整性。如果不通过，Supervisor 会 reroute 到对应节点。整个系统返回的不只是报告，还有 game_matrix、user_profile、trace 和 agent_messages，所以它是可观测、可评估、可回放的。

一句话记忆：

> 这是一个高风险推荐场景下的 agent harness：typed state 控制执行，domain executor 产方案，evaluation gate 保质量。

