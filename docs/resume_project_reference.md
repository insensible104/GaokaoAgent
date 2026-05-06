# GaokaoAgent 项目简历/面试参考记录

本文档用于整理与简历撰写、项目介绍、面试回答最相关的文件，方便后续快速查找和引用。

## 1. 项目定位

推荐对外描述为：

- 基于 LangGraph 的多智能体决策系统
- 面向高考志愿填报这一高风险、长路径、多约束场景
- 技术方向：多智能体决策、长路径推理、面向智能体调度的大模型对齐（RLHF/GRPO）

更准确的系统定位是：

- graph-orchestrated multi-agent decision system
- 可运行的研究型原型

## 2. 最适合简历展开的主线能力

### 2.1 多智能体协同决策

核心要点：

- 使用监督者统一调度各任务节点
- 不是单次模型调用，而是多阶段状态驱动决策
- 已补充显式消息协议、局部记忆和并行评审层

相关文件：

- `backend/src/graph/dual_loop_supervisor.py`
- `backend/src/models/state.py`
- `backend/src/models/agent_communication.py`
- `backend/src/utils/agent_bus.py`
- `backend/src/agents/deliberation_agents.py`
- `backend/src/rl/supervisor_policy.py`

### 2.2 深度调研

核心要点：

- 支持任务拆解、多跳检索、多源交叉核验、研究报告生成
- 支持无外部检索时的 fallback 调研模式
- 支持 research-only 输出，不依赖量化矩阵也能闭环成报告

相关文件：

- `backend/src/agents/deep_research_agent.py`
- `backend/src/subgraphs/deep_research.py`
- `backend/src/subgraphs/__init__.py`
- `backend/src/agents/report_agent.py`

### 2.3 推荐与风险控制

核心要点：

- 基于真实录取数据、招生计划和一分一段表生成候选方案
- 结合录取概率建模、蒙特卡洛仿真、组合筛选和规则审查
- 输出志愿表、风险说明和合规检查结果

相关文件：

- `backend/src/agents/game_agent.py`
- `backend/src/engines/quant_engine.py`
- `backend/src/engines/probability.py`
- `backend/src/engines/monte_carlo_sim.py`
- `backend/src/agents/critic_agent_enhanced.py`
- `backend/src/models/game_matrix.py`
- `backend/data/`

### 2.4 对齐 / RL / 调度优化

核心要点：

- RL 不直接用于“冲稳保比例”这类强先验规则
- 主要用于 supervisor 的长路径调度策略
- 已具备 trace、pairwise preference、reward model、GRPO、在线接管接口

相关文件：

- `backend/src/rl/orchestration_data_pipeline.py`
- `backend/src/rl/orchestration_alignment.py`
- `backend/src/rl/orchestration_trl_utils.py`
- `backend/src/rl/reward_model_scorer.py`
- `backend/src/rl/supervisor_policy.py`
- `backend/scripts/train_supervisor_action_ranker.py`
- `backend/scripts/train_orchestration_reward_model.py`
- `backend/scripts/train_orchestration_grpo.py`
- `backend/scripts/train_orchestration_grpo_hf_job.py`
- `backend/scripts/train_minimal_supervisor_reward_model.py`
- `backend/scripts/evaluate_orchestration_policies.py`

## 3. 简历关键表述与支撑文件

### 表述 1

“基于 LangGraph 搭建监督者-执行者式多智能体架构”

支撑文件：

- `backend/src/graph/dual_loop_supervisor.py`
- `backend/src/main.py`
- `backend/src/agents/__init__.py`

### 表述 2

“通过中央路由节点协同画像分析、院校调研、策略生成与结果审查”

支撑文件：

- `backend/src/agents/router_agent.py`
- `backend/src/agents/profiling_agent.py`
- `backend/src/agents/game_agent.py`
- `backend/src/agents/deep_research_agent.py`
- `backend/src/agents/report_agent.py`
- `backend/src/agents/critic_agent_enhanced.py`

### 表述 3

“设计具备多跳检索、多源交叉核验与风险提示能力的调研流程”

支撑文件：

- `backend/src/subgraphs/deep_research.py`
- `backend/src/agents/deep_research_agent.py`
- `backend/src/agents/report_agent.py`
- `backend/src/agents/critic_agent_enhanced.py`

### 表述 4

“围绕监督者的路由、检索、反思与停止策略，构建 rollout trace、pairwise preference、reward model 与 GRPO 训练链路”

支撑文件：

- `backend/src/rl/orchestration_data_pipeline.py`
- `backend/src/rl/orchestration_alignment.py`
- `backend/src/rl/orchestration_trl_utils.py`
- `backend/scripts/export_orchestration_alignment_data.py`
- `backend/scripts/train_orchestration_reward_model.py`
- `backend/scripts/train_orchestration_grpo.py`
- `backend/scripts/train_orchestration_grpo_hf_job.py`
- `backend/scripts/train_minimal_supervisor_reward_model.py`

### 表述 5

“提供在线策略接管接口，探索将强化学习用于多智能体系统的长路径调度优化”

支撑文件：

- `backend/src/rl/supervisor_policy.py`
- `backend/src/rl/reward_model_scorer.py`
- `backend/src/rl/orchestration_alignment.py`

## 4. 已有文档

### 架构文档

- `docs/project_architecture_guide.md`
- `docs/current_project_status_overview.md`

### 训练与评测文档

- `backend/docs/orchestration_alignment_training.md`
- `backend/docs/hf_jobs_submission_example.md`

## 5. 可用于证明当前实现状态的测试

### 主决策链 / 多智能体

- `backend/src/test_supervisor_policy_smoke.py`
- `backend/src/test_multi_agent_deliberation_smoke.py`
- `backend/src/test_agent_protocol_smoke.py`
- `backend/src/test_report_agent_research_only_smoke.py`

### 对齐 / RL / 评测

- `backend/src/test_orchestration_alignment_smoke.py`
- `backend/src/test_orchestration_data_pipeline_smoke.py`
- `backend/src/test_orchestration_trl_utils_smoke.py`
- `backend/src/test_orchestration_evaluation_smoke.py`
- `backend/src/test_supervisor_reward_model_smoke.py`

## 6. 当前完成度记录

当前建议按以下口径对外说明：

- 主决策链：82-85%
- 对齐 / RL 管线：72-78%
- 深度调研分支：68-75%
- 多模态：仍非主线能力

说明：

- 主决策链已经足以支撑“多智能体长路径决策系统”的讲法
- 对齐 / RL 已打通训练链、评测脚本和在线接管接口，但收益评测仍需继续做实
- 深度调研已经能闭环输出研究型报告，但仍依赖检索质量与来源可信度控制

## 7. 简历中建议使用的技术方向表述

推荐写法：

`技术方向：多智能体决策、长路径推理、面向智能体调度的大模型对齐（RLHF/GRPO）`

不建议写得过泛：

- “大模型对齐（RLHF/GRPO）、多智能体决策、长路径推理”

原因：

- 太大，容易被面试官追问“RLHF 具体做在哪里”
- 当前更自洽的说法，是把 RLHF/GRPO 的落点限定在 supervisor 调度优化上

## 8. 当前最重要的事实记录

- reward model 的真实 checkpoint 加载链路已经打通
- reward model 可以在 supervisor 运行时参与动作打分
- 但当前本机最小训练得到的 reward model 区分能力仍较弱，收益评测还需要进一步加强
- 因此，当前最准确的说法是：
  - “训练链、评测链、在线接管接口已打通”
  - 而不是“强化学习已经稳定提升线上效果”

## 9. 后续继续推进时最值得优先做的事

1. 扩充更接近真实分布的 pairwise preference 数据
2. 重训 reward model，争取在 supervisor 中出现可观测的真实 override
3. 补更系统的 baseline 对比实验报告
4. 继续加强 deep research 的来源可信度和官方信息优先级
