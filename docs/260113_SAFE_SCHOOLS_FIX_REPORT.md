# 本次修复报告：保底院校为 0 的问题

## 背景
用户位次 7999（物理类）时，系统长期返回保底院校为 0，存在严重滑档风险。本次修复集中在搜索范围、候选池、异常值鲁棒性与筛选逻辑上，目标是恢复保底院校输出并保证策略分布合理。

## 核心问题定位
1. 搜索范围扩展不足：`quant_engine.py` 中 `max_iterations=5` 导致最大搜索上限只能到 47,999，覆盖不到 40,000-50,000 的真实保底区间。
2. 候选池过小：`rank_gradient_strategy.py` 中候选池原为 80，无法覆盖扩大后的搜索范围。
3. 异常年份影响：传统 std 在“大小年”场景下波动过大，Z-score 被稀释。
4. Pareto 筛选误杀：保底院校在 Pareto 过滤时被当作“支配解”剔除。

## 关键修复项
### 1) 扩大最大保底搜索范围
- 文件：`backend/src/engines/quant_engine.py`
- 修改：`max_safe` 从 35000 调整为 60000
- 效果：位次 7999 的最大搜索上限扩展到 67,999

### 2) 增加扩张迭代次数
- 文件：`backend/src/engines/quant_engine.py`
- 修改：`max_iterations` 从 5 调整为 15
- 效果：允许搜索范围完整扩展到 `max_safe`，解决中途停止问题

### 3) 扩大候选池规模
- 文件：`backend/src/rl/rank_gradient_strategy.py`
- 修改：`candidate_pool_size` 从 80 调整为 2000
- 效果：覆盖扩大后的搜索范围，确保保底院校进入候选集

### 4) 引入 MAD（Median Absolute Deviation）
- 文件：`backend/src/engines/probability.py`、`backend/src/engines/monte_carlo_sim.py`
- 修改：使用 MAD 计算波动性，替代 std
- 效果：对“大小年”异常值更鲁棒，Z-score 更合理

### 5) 保底院校绕过 Pareto 筛选
- 文件：`backend/src/agents/game_agent.py`
- 修改：保底院校（Z-score≥2.0）不参与 Pareto 筛选
- 效果：避免保底院校被误删

## 验证与结果
- 后端日志显示：
  - 候选池大小：2000
  - 搜索范围：1-67999
  - 专业组候选：1388
- API 输出（端口 8001）：
  - 冲刺：6
  - 稳妥：13
  - 保底：11
- 保底院校录取概率区间：92.5% - 100%

## 代表性保底院校（节选）
- 四川大学
- 苏州大学
- 山东大学
- 郑州大学
- 暨南大学
- 中国海洋大学
- 华东理工大学

## 环境与运行说明
- 8000 端口存在僵尸占用问题，当前后端运行于 8001 端口
- 需后续处理端口占用，恢复到标准端口

## 文件整理与清理
- 删除临时测试 JSON、临时日志、诊断脚本、tmpclaude 临时目录
- 保留：
  - `backend/test_request.json`
  - `backend/test_port8001.json`
  - `backend/backend_port8001.log`

## 后续建议
1. 解决 8000 端口僵尸占用并恢复默认端口
2. 前后端联调确认 UI 展示保底院校
3. 对其他位次段进行回归测试（如 1000、15000、30000）
4. 评估扩大候选池后的性能表现
