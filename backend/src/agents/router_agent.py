"""Meta-Router Agent：意图分类与循环路由"""
from langchain_core.messages import AIMessage

from models.state import SupervisorState
from models.intent import IntentClassification, IntentType, LoopType
from rl.supervisor_policy import HeuristicSupervisorPolicy, append_trace_record
from utils.agent_bus import publish_agent_message, remember
from utils.llm_factory import get_llm


# === Prompt Template ===
ROUTER_PROMPT = """你是 GaokaoAgent 的元认知路由器，负责分析用户意图并选择最优的执行路径。

## 背景知识
GaokaoAgent 有三个核心能力循环：

1. **快思考循环 (Fast Loop - Quant Engine)**
   - 处理对象：结构化数据（CSV 历史录取数据）
   - 核心能力：
     * 录取概率计算（正态分布 + 小样本惩罚）
     * 位次预测（加权平均 + 置信区间）
     * 冲稳保策略生成（博弈矩阵）
     * 调剂风险模拟
   - 适用场景：用户问"能上吗？""概率多少？""推荐哪些学校？"

2. **慢思考循环 (Slow Loop - Deep Research)**
   - 处理对象：非结构化信息（网络搜索）
   - 核心能力：
     * 多轮迭代搜索（Plan-Execute-Reflect）
     * 知识缺口识别
     * 深度研究报告生成
   - 适用场景：用户问"这个学校怎么样？""专业前景如何？""就业去向？""保研率？"

3. **多模态循环 (Multimodal Loop)**
   - 处理对象：PDF 文件、图表（招生章程、体检表）
   - 核心能力：
     * 语义定位（关键词索引）
     * 图表识别（Vision 模型）
     * 政策解读（体检限制提取）
   - 适用场景：用户问"色弱受限吗？""单科有要求吗？""招生章程怎么说？"

## 任务
分析用户的问题，判断需要哪个/哪些循环，并给出推理过程。

## 用户消息
{user_message}

## 用户画像（如果有）
{user_profile}

## 分类示例

**示例 1：纯定量问题**
用户："我620分，位次12000，能上哪些985？"
推理：这是典型的录取概率计算问题，需要访问 CSV 历史数据，使用量化引擎。
分类：
- primary_intent: QUANT
- requires_quant: true
- requires_search: false
- requires_vision: false

**示例 2：纯研究问题**
用户："中山大学计算机专业怎么样？保研率高吗？"
推理：这需要查找网络上的非结构化信息（学科评估、保研数据、学生评价），CSV 里没有这些。
分类：
- primary_intent: RESEARCH
- requires_quant: false
- requires_search: true
- requires_vision: false

**示例 3：多模态问题**
用户："我色弱，能报电子信息工程吗？"
推理：需要读取招生章程中的体检限制表格，通常是图表形式，需要 Vision 模型。
分类：
- primary_intent: MULTIMODAL
- requires_quant: false
- requires_search: false
- requires_vision: true

**示例 4：混合问题**
用户："推荐一些保研率高的985计算机专业，我620分能上哪些？"
推理：这同时需要：
1. 量化引擎筛选"我能上的985"（Fast Loop）
2. 网络搜索"保研率数据"（Slow Loop）
分类：
- primary_intent: MIXED
- secondary_intents: [QUANT, RESEARCH]
- requires_quant: true
- requires_search: true
- requires_vision: false

## 重要原则
1. **优先判断数据源**：CSV 有的数据不要去搜索，CSV 没有的数据不要去计算
2. **避免无效调用**：如果问"清华地址"，不要调用量化引擎（浪费算力）
3. **置信度评估**：如果问题模糊，降低置信度，并在 reasoning 中说明
4. **主动深度研究**（新增）：即使用户没有明确要求，也要识别以下隐含的深度研究需求：
   - 用户位次处于边界情况（如全省前1%或后20%）
   - 用户专业偏好非常具体（如"想学AI芯片设计"）
   - 用户提到特殊限制（如"不想离开省""必须考虑保研"）
   - 这些情况下应该设置 requires_search=true，触发混合循环

现在请分析上述用户消息，返回意图分类结果。
"""


def router_agent_node(state: SupervisorState) -> dict:
    """
    Meta-Router Agent 节点：意图分类与循环路由

    职责：
    1. 分析用户消息
    2. 分类意图（Quant / Research / Multimodal / Mixed）
    3. 决定激活哪个循环
    """
    print("[Meta-Router] 启动意图分析...")
    print("[进度] 正在分析用户意图...")

    # 获取用户消息
    messages = state.get("messages", [])
    if not messages:
        return {
            "current_agent": "router_agent",
            "debug_logs": ["[ERROR] Router: 没有用户消息"],
            "messages": [AIMessage(content="错误：没有用户消息")]
        }

    user_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])

    # 获取用户画像（如果有）
    user_profile = state.get("user_profile")
    profile_str = str(user_profile) if user_profile else "暂无用户画像"

    # 调用 LLM 进行意图分类
    print("[进度] 正在调用LLM进行意图分类...")
    llm = get_llm(temperature=0)  # 使用低温度确保稳定性
    structured_llm = llm.with_structured_output(IntentClassification)

    prompt = ROUTER_PROMPT.format(
        user_message=user_message,
        user_profile=profile_str
    )

    try:
        intent: IntentClassification = structured_llm.invoke(prompt)
        policy = HeuristicSupervisorPolicy()

        print(f"[Meta-Router] 意图分类完成")
        print(f"  - 主意图: {intent.primary_intent.value}")
        print(f"  - 需要 Quant: {intent.requires_quant}")
        print(f"  - 需要 Search: {intent.requires_search}")
        print(f"  - 需要 Vision: {intent.requires_vision}")
        print(f"  - 置信度: {intent.confidence:.2f}")
        print(f"  - 推理: {intent.reasoning}")

        # 决定激活哪个循环
        if intent.primary_intent == IntentType.MIXED:
            active_loop = LoopType.HYBRID
        elif intent.should_use_fast_loop:
            active_loop = LoopType.FAST
        elif intent.should_use_slow_loop:
            active_loop = LoopType.SLOW
        elif intent.should_use_multimodal:
            active_loop = LoopType.MULTIMODAL
        else:
            # 默认走快思考
            active_loop = LoopType.FAST

        decision = policy.decide_after_router({
            **state,
            "intent_classification": intent,
            "active_loop": active_loop,
        })

        policy_update = append_trace_record(state, decision)

        protocol_update = publish_agent_message(
            sender="router_agent",
            stage="routing",
            message_type="task",
            content=f"Intent={intent.primary_intent.value}, active_loop={active_loop.value}",
            recipients=[decision.selected_action],
            action_preference=decision.selected_action,
            confidence=intent.confidence,
            metadata={
                "requires_quant": intent.requires_quant,
                "requires_search": intent.requires_search,
                "requires_vision": intent.requires_vision,
            },
        )
        memory_update = remember(
            agent_name="router_agent",
            stage="routing",
            note_type="routing_decision",
            content=f"Routed to {decision.selected_action} with confidence {intent.confidence:.2f}",
            importance=intent.confidence,
        )

        return {
            "intent_classification": intent,
            "active_loop": active_loop,
            "loop_history": [active_loop.value],
            "next_action": policy_update["next_action"],
            "orchestration_trace": policy_update["orchestration_trace"],
            "agent_messages": protocol_update["agent_messages"],
            "agent_memories": memory_update["agent_memories"],
            "current_agent": "router_agent",
            "debug_logs": policy_update["debug_logs"] + [
                f"[Router] 分类完成: {intent.primary_intent.value} (置信度: {intent.confidence:.2f})",
                f"[Router] 激活循环: {active_loop.value}",
                f"[Router] 推理: {intent.reasoning}"
            ],
            "messages": [AIMessage(content=f"意图分析完成，激活 {active_loop.value} 循环...")]
        }

    except Exception as e:
        print(f"[ERROR] Router 意图分类失败: {e}")
        # Fallback：默认走快思考循环
        return {
            "intent_classification": None,
            "active_loop": LoopType.FAST,
            "loop_history": ["fast"],
            "next_action": "profiling_agent",
            "agent_messages": publish_agent_message(
                sender="router_agent",
                stage="routing",
                message_type="task",
                content="Router fallback to profiling_agent after LLM failure.",
                recipients=["profiling_agent"],
                action_preference="profiling_agent",
                confidence=0.3,
            )["agent_messages"],
            "current_agent": "router_agent",
            "debug_logs": [f"[WARN] Router 失败，默认使用 Fast Loop: {e}"],
            "messages": [AIMessage(content="意图分析失败，使用默认策略...")]
        }

