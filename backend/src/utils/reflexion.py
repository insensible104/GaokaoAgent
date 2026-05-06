"""Reflexion 机制实现（In-context Reinforcement Learning）

核心思想：
1. Agent 执行任务
2. Critic 评估并生成批评
3. 将批评加入短期记忆
4. Agent 重试时参考批评历史
5. 迭代改进

参考论文：Reflexion: Language Agents with Verbal Reinforcement Learning
"""
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from langchain_core.messages import AIMessage, HumanMessage


class ReflexionEntry(BaseModel):
    """反思记录条目"""
    attempt_id: int = Field(description="尝试编号")
    task_description: str = Field(description="任务描述")
    execution_trace: str = Field(description="执行轨迹")
    outcome: str = Field(description="执行结果")
    criticism: str = Field(description="批评内容")
    improvement_suggestion: str = Field(description="改进建议")
    timestamp: str = Field(description="时间戳")


class ReflexionMemory:
    """Reflexion 短期记忆管理器"""

    def __init__(self, max_entries: int = 5):
        """
        初始化 Reflexion 记忆

        Args:
            max_entries: 最大记忆条目数（保持短期记忆）
        """
        self.max_entries = max_entries
        self.entries: List[ReflexionEntry] = []

    def add_reflection(
        self,
        attempt_id: int,
        task_description: str,
        execution_trace: str,
        outcome: str,
        criticism: str,
        improvement_suggestion: str
    ):
        """添加反思记录"""
        from datetime import datetime

        entry = ReflexionEntry(
            attempt_id=attempt_id,
            task_description=task_description,
            execution_trace=execution_trace,
            outcome=outcome,
            criticism=criticism,
            improvement_suggestion=improvement_suggestion,
            timestamp=datetime.now().isoformat()
        )

        self.entries.append(entry)

        # 保持短期记忆（FIFO）
        if len(self.entries) > self.max_entries:
            self.entries.pop(0)

    def get_recent_reflections(self, n: int = 3) -> List[ReflexionEntry]:
        """获取最近的 N 条反思记录"""
        return self.entries[-n:] if len(self.entries) >= n else self.entries

    def format_for_prompt(self) -> str:
        """格式化为 Prompt（用于 in-context learning）"""
        if not self.entries:
            return "（暂无反思历史）"

        formatted = "## 之前的尝试记录（请从失败中学习）\n\n"

        for entry in self.entries:
            formatted += f"### 尝试 {entry.attempt_id}\n"
            formatted += f"**任务**: {entry.task_description}\n"
            formatted += f"**执行**: {entry.execution_trace}\n"
            formatted += f"**结果**: {entry.outcome}\n"
            formatted += f"**批评**: {entry.criticism}\n"
            formatted += f"**建议**: {entry.improvement_suggestion}\n\n"

        return formatted

    def clear(self):
        """清空记忆"""
        self.entries.clear()


class ReflexionPromptBuilder:
    """Reflexion Prompt 构建器"""

    @staticmethod
    def build_retry_prompt(
        original_task: str,
        reflexion_memory: ReflexionMemory,
        additional_context: Optional[str] = None
    ) -> str:
        """
        构建重试 Prompt（包含反思历史）

        Args:
            original_task: 原始任务
            reflexion_memory: 反思记忆
            additional_context: 额外上下文

        Returns:
            增强的 Prompt
        """
        prompt = f"""你需要完成以下任务：

{original_task}

{reflexion_memory.format_for_prompt()}

## 当前尝试的要求
请仔细阅读上述失败记录，**避免重复相同的错误**。

具体要求：
1. 分析之前失败的原因
2. 调整你的策略和工具选择
3. 确保本次执行不会犯同样的错误
4. 如果之前的批评提到了具体建议，请采纳

"""

        if additional_context:
            prompt += f"\n## 额外信息\n{additional_context}\n"

        prompt += "\n现在请重新执行任务。"

        return prompt

    @staticmethod
    def build_critic_prompt(
        task: str,
        execution_trace: str,
        result: str,
        expected_outcome: Optional[str] = None
    ) -> str:
        """
        构建 Critic Prompt（生成批评和建议）

        Args:
            task: 任务描述
            execution_trace: 执行轨迹
            result: 执行结果
            expected_outcome: 期望结果

        Returns:
            Critic Prompt
        """
        prompt = f"""你是一个严格的评审专家，需要评估 Agent 的执行质量。

## 任务
{task}

## 执行轨迹
{execution_trace}

## 实际结果
{result}

"""

        if expected_outcome:
            prompt += f"""## 期望结果
{expected_outcome}

"""

        prompt += """## 评估要求
请回答以下问题：

1. **执行是否成功？** （成功 / 部分成功 / 失败）
2. **失败原因是什么？** （如果失败）
   - 工具选择错误？
   - 查询参数不当？
   - 结果解析错误？
   - 逻辑推理错误？

3. **具体的批评** （指出问题所在）

4. **改进建议** （下次应该如何做）

请用以下格式回答：
```
评估结果: [成功/部分成功/失败]
失败原因: [具体原因]
批评: [具体批评内容]
建议: [改进建议]
```
"""

        return prompt


def apply_reflexion_to_agent(
    agent_func,
    task: str,
    max_attempts: int = 3,
    reflexion_memory: Optional[ReflexionMemory] = None
):
    """
    为 Agent 函数应用 Reflexion 机制（装饰器模式）

    Args:
        agent_func: 原始 Agent 函数
        task: 任务描述
        max_attempts: 最大尝试次数
        reflexion_memory: Reflexion 记忆（可选，不提供则创建新的）

    Returns:
        执行结果
    """
    if reflexion_memory is None:
        reflexion_memory = ReflexionMemory()

    for attempt in range(1, max_attempts + 1):
        print(f"[Reflexion] 尝试 {attempt}/{max_attempts}")

        # 如果不是第一次尝试，使用反思增强的 Prompt
        if attempt > 1:
            enhanced_prompt = ReflexionPromptBuilder.build_retry_prompt(
                original_task=task,
                reflexion_memory=reflexion_memory
            )
            result = agent_func(enhanced_prompt)
        else:
            result = agent_func(task)

        # 评估结果
        if is_successful(result):
            print(f"[Reflexion] 成功！（第 {attempt} 次尝试）")
            return result

        # 失败：生成批评并记录
        criticism, suggestion = generate_criticism(task, result)

        reflexion_memory.add_reflection(
            attempt_id=attempt,
            task_description=task,
            execution_trace=str(result.get("trace", "N/A")),
            outcome="失败",
            criticism=criticism,
            improvement_suggestion=suggestion
        )

        print(f"[Reflexion] 失败，记录反思：{criticism}")

    # 达到最大尝试次数
    print(f"[Reflexion] 达到最大尝试次数 {max_attempts}，终止")
    return None


def is_successful(result: Dict) -> bool:
    """
    判断结果是否成功（简单实现）

    Args:
        result: Agent 执行结果

    Returns:
        是否成功
    """
    # 根据具体的结果格式判断
    if isinstance(result, dict):
        return result.get("success", False)
    return False


def generate_criticism(task: str, result: Dict) -> tuple:
    """
    生成批评和建议（简化版本）

    在完整实现中，应该使用 LLM 生成

    Args:
        task: 任务
        result: 结果

    Returns:
        (criticism, suggestion)
    """
    # 简化实现：基于规则生成批评
    criticism = "执行失败，未达到预期目标"
    suggestion = "建议检查工具选择和参数设置"

    # 可以根据 result 中的错误信息生成更具体的批评
    if isinstance(result, dict):
        error = result.get("error", "")
        if "empty" in error.lower():
            criticism = "工具调用返回空结果"
            suggestion = "建议检查查询参数，或尝试使用其他工具"
        elif "not found" in error.lower():
            criticism = "未找到相关数据"
            suggestion = "建议扩大搜索范围或使用更通用的查询"

    return criticism, suggestion


# === 集成到 GaokaoAgent 的辅助函数 ===
def create_reflexion_prompt_for_retry(state: dict, attempt_id: int) -> str:
    """
    为 GaokaoAgent 重试创建 Reflexion 增强 Prompt

    Args:
        state: SupervisorState
        attempt_id: 尝试编号

    Returns:
        增强的 Prompt
    """
    reflexion_history = state.get("reflection_history", [])

    if not reflexion_history:
        # 第一次尝试，不需要增强
        return ""

    # 格式化反思历史
    prompt = "\n\n## 🔄 反思历史（请避免重复错误）\n\n"

    for i, reflection in enumerate(reflexion_history, 1):
        prompt += f"### 尝试 {i} 的教训\n"
        prompt += f"{reflection}\n\n"

    prompt += "请根据上述反思，调整你的策略和工具选择，不要重复相同的错误。\n"

    return prompt

