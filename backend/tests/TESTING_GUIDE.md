# GaokaoAgent 测试框架使用指南

## 概述

本测试框架包含 **50 个高难度多跳问题**，用于全面评估 GaokaoAgent 的双循环智能体系统。

## 测试用例结构

### 分类统计

| 分类 | 数量 | 说明 |
|------|------|------|
| **quant_research** | 20 | 量化 + 研究双循环 |
| **quant_multimodal** | 15 | 量化 + 多模态双循环 |
| **research_multimodal** | 10 | 研究 + 多模态双循环 |
| **triple_loop** | 5 | 三循环混合（最难） |

### 难度分布

| 难度 | 数量 | 特征 |
|------|------|------|
| **medium** | 20 | 双跳问题，需要 2 个工具 |
| **hard** | 20 | 三跳问题，需要 3+ 个工具 |
| **very_hard** | 10 | 四跳+问题，需要复杂推理链 |

---

## 快速开始

### 1. 运行所有测试（完整版）

```bash
cd backend/tests
python run_tests.py
```

预计耗时：**20-30 分钟**（50 个测试，每个约 30-40 秒）

### 2. 运行部分测试（快速验证）

#### 仅运行前 10 个测试
```bash
python run_tests.py --limit 10
```

#### 按分类运行
```bash
# 仅运行量化+研究类测试
python run_tests.py --category quant_research

# 仅运行多模态类测试
python run_tests.py --category quant_multimodal
```

#### 按难度运行
```bash
# 仅运行中等难度测试
python run_tests.py --difficulty medium

# 仅运行最高难度测试
python run_tests.py --difficulty very_hard
```

#### 组合过滤
```bash
# 运行前 5 个最难的三循环测试
python run_tests.py --category triple_loop --difficulty very_hard --limit 5
```

---

## 测试用例示例

### 示例 1：量化 + 研究（QR001）

**问题**: "我 620 分，位次 12000，想学计算机，推荐 3 个保研率超过 20% 的 985 院校"

**预期行为**:
1. **Meta-Router**: 分类为 MIXED (quant + research)
2. **Fast Loop**: 用量化引擎筛选位次 12000 能上的 985 计算机专业
3. **Slow Loop**: 搜索各院校保研率数据
4. **Report Agent**: 整合推荐 3 个院校

**成功标准**:
- ✓ 生成 Game Matrix
- ✓ 生成 Research Report
- ✓ 至少推荐 3 个院校
- ✓ 报告中提到"保研率"

---

### 示例 2：量化 + 多模态（QM001）

**问题**: "我色弱，620 分想学计算机，哪些 985 院校对色弱没有限制？"

**预期行为**:
1. **Meta-Router**: 分类为 MIXED (quant + multimodal)
2. **Multimodal Loop**:
   - PDF Parser: 提取 985 计算机招生章程
   - Vision Analyzer: 识别体检限制表格
   - 筛选出无色弱限制的院校
3. **Fast Loop**: 用 620 分匹配可上院校

**成功标准**:
- ✓ 检查体检限制（PDF 解析或 Vision 分析）
- ✓ 按分数筛选
- ✓ 排除色弱限制院校

---

### 示例 3：三循环混合（TL001）- 最难

**问题**: "找一个广东的 985 大学，计算机保研率前三且对色弱友好，我位次 8000 能上吗？"

**预期行为**:
1. **Slow Loop**: 搜索"广东 985 计算机保研率排名"
2. **Multimodal Loop**: 解析招生章程检查色弱限制
3. **Fast Loop**: 用位次 8000 计算录取概率

**成功标准**:
- ✓ 搜索保研率
- ✓ 检查色弱限制
- ✓ 计算录取概率
- ✓ 按地理位置筛选

---

## 评估指标

### 1. Intent Classification Accuracy（意图分类准确率）

测试 Meta-Router 是否正确识别用户意图：
- QUANT：纯量化问题
- RESEARCH：纯研究问题
- MULTIMODAL：纯多模态问题
- MIXED：混合型问题

**目标**: ≥ 90% 准确率

### 2. Loop Activation Accuracy（循环激活准确率）

测试 Supervisor 是否激活了正确的循环序列：
- Fast Loop（量化循环）
- Slow Loop（研究循环）
- Multimodal Loop（多模态循环）

**目标**: ≥ 85% 准确率

### 3. Tool Call Efficiency（工具调用效率）

测试是否调用了正确的工具：
- quant_engine：量化引擎
- search_tool：网络搜索
- pdf_parser：PDF 解析
- vision_analyzer：视觉分析

**目标**: ≥ 80% 准确率（无冗余调用）

### 4. End-to-End Success Rate（端到端成功率）

测试是否满足所有成功标准（must_* 条件）

**目标**: ≥ 75% 成功率

---

## 测试报告解读

### 控制台输出示例

```
==================================================
GaokaoAgent 测试运行器
==================================================
[加载] 从 tests/test_cases.json 加载测试用例...
[OK] 加载了 50 个测试用例

分类统计:
  - quant_research: 20
  - quant_multimodal: 15
  - research_multimodal: 10
  - triple_loop: 5

难度统计:
  - medium: 20
  - hard: 20
  - very_hard: 10

[初始化] 创建 Dual-Loop Supervisor Graph...
[OK] Graph 创建成功


进度: 1/50
============================================================
[测试] QR001 (quant_research / medium)
[问题] 我620分，位次12000，想学计算机，推荐3个保研率超过20%的985院校
============================================================

[Router Agent] 正在分析用户意图...
[Profiling Agent] 提取用户画像...
[Game Agent] 搜索候选院校...
[Deep Research] 搜索保研率数据...
[Report Agent] 生成报告...
[Critic Agent] 审计通过

[结果] ✓ 通过
[耗时] 35.2s
[意图] 预期: MIXED, 实际: MIXED
[循环] 预期: ['fast', 'slow'], 实际: ['fast', 'slow']

...
```

### JSON 报告示例

测试完成后，会生成详细的 JSON 报告：

```json
{
  "summary": {
    "total": 50,
    "passed": 38,
    "failed": 12,
    "pass_rate": 0.76,
    "total_time": 1850.3,
    "avg_time": 37.0
  },
  "by_category": {
    "quant_research": {
      "total": 20,
      "passed": 17
    },
    "quant_multimodal": {
      "total": 15,
      "passed": 11
    },
    ...
  },
  "test_results": [
    {
      "test_id": "QR001",
      "passed": true,
      "execution_time": 35.2,
      "criteria_results": {
        "must_have_game_matrix": true,
        "must_have_research_report": true,
        "min_recommendations": true,
        "must_mention_保研率": true
      }
    },
    ...
  ]
}
```

---

## 失败案例调试

### 常见失败原因

#### 1. Intent Classification 错误

**现象**: `actual_intent` 与 `expected_intent` 不符

**解决方法**:
- 检查 `backend/src/agents/router_agent.py` 的 ROUTER_PROMPT
- 增加示例覆盖该类型问题
- 调整 Pydantic 模型的字段说明

#### 2. Tool Call 缺失

**现象**: `expected_tools` 中的工具未在 `actual_tools` 中出现

**解决方法**:
- 检查对应 Agent 是否正确触发
- 检查 `dual_loop_supervisor.py` 的路由逻辑
- 添加 debug_logs 追踪执行流程

#### 3. Criteria 未满足

**现象**: `criteria_results` 中某些标准为 `false`

**解决方法**:
- 查看 `run_tests.py` 中 `_evaluate_criteria()` 的实现
- 检查 State 中是否缺少必要数据
- 验证 Agent 输出格式是否正确

---

## 优化建议

基于测试结果，可以进行以下优化：

### 1. Router Prompt 优化

如果 Intent Classification Accuracy < 90%：
- 增加失败案例到 ROUTER_PROMPT 示例
- 调整 IntentClassification 的 reasoning 权重
- 使用 Few-Shot Learning 技术

### 2. Reflection Threshold 调优

如果重试次数过多（avg_time > 45s）：
- 调整 `critic_agent_enhanced.py` 中的 `reward_value < -0.5` 阈值
- 增加 `max_retry_count` 限制
- 优化 Reflexion 记忆的格式

### 3. Step Reward Rules 调整

如果工具选择错误率高：
- 修改 `models/step_reward.py` 中的关键词映射
- 调整 `INAPPROPRIATE_TOOL_PENALTY` 惩罚值
- 增加新的工具-任务映射规则

---

## 高级用法

### 1. 单个测试调试

编辑 `run_tests.py`，在 `main()` 中硬编码测试 ID：

```python
async def main():
    runner = TestRunner()
    runner.load_test_cases()

    # 仅运行特定测试
    test_case = next(tc for tc in runner.test_cases if tc["id"] == "QR001")
    result = await runner.run_single_test(test_case)
    print(result.to_dict())
```

### 2. 导出失败案例

```python
# 在 generate_report() 中添加
failed_cases = [r for r in self.results if not r.passed]
with open("failed_cases.json", 'w', encoding='utf-8') as f:
    json.dump([r.to_dict() for r in failed_cases], f, ensure_ascii=False, indent=2)
```

### 3. 添加自定义评估标准

在 `_evaluate_criteria()` 中添加新的标准：

```python
elif key == "must_have_cost_analysis":
    report = state.get("report_draft")
    if report:
        results[key] = "学费" in report.full_markdown
    else:
        results[key] = False
```

---

## 预期结果（基线）

根据初步估计，GaokaoAgent 双循环系统的目标性能：

| 指标 | 目标值 | 备注 |
|------|--------|------|
| **总体通过率** | ≥ 75% | 38+/50 |
| **Medium 通过率** | ≥ 85% | 17+/20 |
| **Hard 通过率** | ≥ 70% | 14+/20 |
| **Very Hard 通过率** | ≥ 60% | 6+/10 |
| **意图分类准确率** | ≥ 90% | 45+/50 |
| **平均响应时间** | ≤ 40s | 每个测试 |

---

## 持续集成

### GitHub Actions 集成（示例）

```yaml
name: GaokaoAgent Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
      - name: Run tests
        run: |
          cd backend/tests
          python run_tests.py --limit 10
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          TAVILY_API_KEY: ${{ secrets.TAVILY_API_KEY }}
```

---

## 下一步

完成测试后，根据结果进行：

1. **Router Prompt 优化**：分析意图分类错误案例
2. **Reflection Threshold 调优**：减少不必要的重试
3. **Step Reward Rules 调整**：提高工具选择准确率
4. **Tool Call 优化**：减少冗余调用

---

**测试文件位置**:
- 测试用例：`backend/tests/test_cases.json`
- 测试运行器：`backend/tests/run_tests.py`
- 测试报告：`backend/tests/test_report_YYYYMMDD_HHMMSS.json`
