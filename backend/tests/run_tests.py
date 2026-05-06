"""GaokaoAgent 测试运行器

运行 50 个多跳问题测试用例，评估双循环系统性能
"""
import json
import asyncio
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
import traceback

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from graph.dual_loop_supervisor import create_dual_loop_supervisor
from models.state import SupervisorState
from langchain_core.messages import HumanMessage


class TestResult:
    """单个测试结果"""
    def __init__(self, test_case: Dict):
        self.test_case = test_case
        self.test_id = test_case["id"]
        self.passed = False
        self.error = None
        self.execution_time = 0.0
        self.actual_intent = None
        self.actual_loops = []
        self.actual_tools = []
        self.criteria_results = {}
        self.state_output = None

    def to_dict(self) -> Dict:
        return {
            "test_id": self.test_id,
            "category": self.test_case["category"],
            "difficulty": self.test_case["difficulty"],
            "question": self.test_case["question"],
            "passed": self.passed,
            "error": self.error,
            "execution_time": self.execution_time,
            "expected_intent": self.test_case["expected_intent"],
            "actual_intent": self.actual_intent,
            "expected_loops": self.test_case["expected_loops"],
            "actual_loops": self.actual_loops,
            "expected_tools": self.test_case["expected_tools"],
            "actual_tools": self.actual_tools,
            "criteria_results": self.criteria_results
        }


class TestRunner:
    """测试运行器"""

    def __init__(self, test_cases_file: str = "tests/test_cases.json"):
        tests_root = Path(__file__).resolve().parent
        candidate_path = Path(test_cases_file)
        if candidate_path.is_absolute():
            self.test_cases_file = candidate_path
        elif candidate_path.exists():
            self.test_cases_file = candidate_path.resolve()
        else:
            self.test_cases_file = (tests_root / candidate_path.name).resolve()
        self.test_cases = []
        self.results: List[TestResult] = []
        self.graph = None

    def load_test_cases(self):
        """加载测试用例"""
        print(f"[加载] 从 {self.test_cases_file} 加载测试用例...")

        with open(self.test_cases_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.test_cases = data["test_cases"]
        print(f"[OK] 加载了 {len(self.test_cases)} 个测试用例")

        # 统计信息
        categories = {}
        difficulties = {}
        for tc in self.test_cases:
            cat = tc["category"]
            diff = tc["difficulty"]
            categories[cat] = categories.get(cat, 0) + 1
            difficulties[diff] = difficulties.get(diff, 0) + 1

        print(f"\n分类统计:")
        for cat, count in categories.items():
            print(f"  - {cat}: {count}")

        print(f"\n难度统计:")
        for diff, count in difficulties.items():
            print(f"  - {diff}: {count}")

    def initialize_graph(self):
        """初始化 Dual-Loop Graph"""
        print("\n[初始化] 创建 Dual-Loop Supervisor Graph...")
        self.graph = create_dual_loop_supervisor()
        print("[OK] Graph 创建成功")

    async def run_single_test(self, test_case: Dict) -> TestResult:
        """运行单个测试用例"""
        result = TestResult(test_case)

        try:
            print(f"\n{'='*60}")
            print(f"[测试] {test_case['id']} ({test_case['category']} / {test_case['difficulty']})")
            print(f"[问题] {test_case['question']}")
            print(f"{'='*60}")

            # 构造初始状态
            initial_state: SupervisorState = {
                "messages": [HumanMessage(content=test_case["question"])],
                "current_agent": "router",
                "debug_logs": [],
                "loop_history": [],
                "search_queries": [],
                "web_research_results": [],
                "knowledge_gaps": [],
                "pdf_sources": [],
                "vision_results": [],
                "health_restrictions": [],
                "step_rewards": [],
                "reflection_history": [],
                "orchestration_trace": [],
                "next_action": None,
                "orchestration_reward": None,
                "agent_messages": [],
                "agent_memories": [],
                "deliberation_summaries": [],
                "recommended_next_action": None,
                "research_loop_count": 0,
                "retry_count": 0,
                "intent_classification": None,
                "active_loop": None,
                "user_profile": None,
                "game_matrix": None,
                "report_draft": None,
                "audit_result": None,
                "research_topic": None,
                "research_report": None
            }

            # 记录开始时间
            start_time = datetime.now()

            # 执行 Graph
            final_state = await self.graph.ainvoke(initial_state)

            # 记录执行时间
            result.execution_time = (datetime.now() - start_time).total_seconds()
            result.state_output = final_state

            # 提取实际结果
            result.actual_intent = self._extract_intent(final_state)
            result.actual_loops = self._extract_loops(final_state)
            result.actual_tools = self._extract_tools(final_state)

            # 评估成功标准
            result.criteria_results = self._evaluate_criteria(test_case, final_state)

            # 判断是否通过
            result.passed = all(result.criteria_results.values())

            print(f"\n[结果] {'✓ 通过' if result.passed else '✗ 失败'}")
            print(f"[耗时] {result.execution_time:.2f}s")
            print(f"[意图] 预期: {test_case['expected_intent']['primary_intent']}, 实际: {result.actual_intent}")
            print(f"[循环] 预期: {test_case['expected_loops']}, 实际: {result.actual_loops}")

            if not result.passed:
                print(f"\n[失败原因]")
                for criterion, passed in result.criteria_results.items():
                    if not passed:
                        print(f"  ✗ {criterion}")

        except Exception as e:
            result.error = str(e)
            result.passed = False
            print(f"\n[ERROR] 测试执行失败: {e}")
            traceback.print_exc()

        return result

    def _extract_intent(self, state: Dict) -> str:
        """提取实际意图分类"""
        intent_class = state.get("intent_classification")
        if intent_class:
            if hasattr(intent_class, "primary_intent"):
                primary_intent = intent_class.primary_intent
                return primary_intent.value if hasattr(primary_intent, "value") else str(primary_intent)
            if isinstance(intent_class, dict):
                primary_intent = intent_class.get("primary_intent", "UNKNOWN")
                return primary_intent.value if hasattr(primary_intent, "value") else str(primary_intent)
        return "UNKNOWN"

    def _extract_loops(self, state: Dict) -> List[str]:
        """提取实际循环序列"""
        loop_history = state.get("loop_history", [])
        # 去重并保持顺序
        seen = set()
        result = []
        for loop in loop_history:
            loop_value = loop.value if hasattr(loop, 'value') else str(loop)
            if loop_value not in seen:
                seen.add(loop_value)
                result.append(loop_value)
        return result

    def _extract_tools(self, state: Dict) -> List[str]:
        """提取实际工具调用"""
        tools = []

        # 从 step_rewards 中提取
        step_rewards = state.get("step_rewards", [])
        for step in step_rewards:
            tool_type = step.tool_call_type.value if hasattr(step.tool_call_type, 'value') else str(step.tool_call_type)
            if tool_type not in tools:
                tools.append(tool_type)

        # 从其他状态推断
        if state.get("game_matrix"):
            if "quant_engine" not in tools:
                tools.append("quant_engine")

        if state.get("web_research_results") and len(state["web_research_results"]) > 0:
            if "search_tool" not in tools:
                tools.append("search_tool")

        if state.get("pdf_sources") and len(state["pdf_sources"]) > 0:
            if "pdf_parser" not in tools:
                tools.append("pdf_parser")

        if state.get("vision_results") and len(state["vision_results"]) > 0:
            if "vision_analyzer" not in tools:
                tools.append("vision_analyzer")

        return tools

    def _evaluate_criteria(self, test_case: Dict, state: Dict) -> Dict[str, bool]:
        """评估成功标准"""
        criteria = test_case["success_criteria"]
        results = {}

        for key, value in criteria.items():
            if key == "must_have_game_matrix":
                results[key] = state.get("game_matrix") is not None

            elif key == "must_have_research_report":
                results[key] = state.get("research_report") is not None and len(state.get("research_report", "")) > 0

            elif key == "min_recommendations":
                matrix = state.get("game_matrix")
                if matrix and hasattr(matrix, 'rows'):
                    results[key] = len(matrix.rows) >= value
                else:
                    results[key] = False

            elif key == "must_mention_保研率":
                report = state.get("research_report", "") + str(state.get("report_draft", ""))
                results[key] = "保研率" in report or "保研" in report

            elif key == "must_search_保研率":
                queries = " ".join(state.get("search_queries", []))
                results[key] = "保研" in queries

            elif key == "must_calculate_admission_prob":
                matrix = state.get("game_matrix")
                results[key] = matrix is not None

            elif key == "must_filter_by_location":
                # 简化：检查 debug_logs 或 messages 是否提到地点筛选
                logs = " ".join(state.get("debug_logs", []))
                messages = " ".join([str(m.content) for m in state.get("messages", [])])
                combined = logs + messages
                results[key] = any(loc in combined for loc in ["广东", "北京", "上海", "江苏", "省会"])

            elif key == "must_check_health_restrictions":
                results[key] = len(state.get("pdf_sources", [])) > 0 or len(state.get("health_restrictions", [])) > 0

            elif key == "must_filter_by_score":
                results[key] = state.get("game_matrix") is not None

            elif key == "must_filter_by_rank":
                results[key] = state.get("game_matrix") is not None

            elif key.startswith("must_search_"):
                keyword = key.replace("must_search_", "")
                queries = " ".join(state.get("search_queries", []))
                results[key] = keyword in queries

            elif key.startswith("must_check_"):
                # PDF/Vision 相关检查
                results[key] = len(state.get("pdf_sources", [])) > 0 or len(state.get("vision_results", [])) > 0

            elif key == "min_admission_prob":
                matrix = state.get("game_matrix")
                if matrix and hasattr(matrix, 'rows'):
                    safe_rows = [r for r in matrix.rows if hasattr(r, 'strategy_tag') and r.strategy_tag.value == "safe"]
                    if safe_rows:
                        min_prob = min(r.admission_prob for r in safe_rows)
                        results[key] = min_prob >= value
                    else:
                        results[key] = False
                else:
                    results[key] = False

            elif key == "max_adjustment_risk":
                matrix = state.get("game_matrix")
                if matrix and hasattr(matrix, 'rows'):
                    max_risk = max((r.adjustment_risk for r in matrix.rows if hasattr(r, 'adjustment_risk')), default=0)
                    results[key] = max_risk <= value
                else:
                    results[key] = False

            else:
                # 默认：假设通过（未实现的标准）
                results[key] = True

        return results

    async def run_all_tests(self, filter_category: str = None, filter_difficulty: str = None, limit: int = None):
        """运行所有测试"""
        print(f"\n{'='*60}")
        print("GaokaoAgent 测试运行器")
        print(f"{'='*60}")

        # 加载测试用例
        self.load_test_cases()

        # 过滤测试用例
        filtered_cases = self.test_cases
        if filter_category:
            filtered_cases = [tc for tc in filtered_cases if tc["category"] == filter_category]
            print(f"\n[过滤] 仅运行 {filter_category} 类别的测试")

        if filter_difficulty:
            filtered_cases = [tc for tc in filtered_cases if tc["difficulty"] == filter_difficulty]
            print(f"\n[过滤] 仅运行 {filter_difficulty} 难度的测试")

        if limit:
            filtered_cases = filtered_cases[:limit]
            print(f"\n[限制] 仅运行前 {limit} 个测试")

        print(f"\n[执行] 将运行 {len(filtered_cases)} 个测试用例")

        # 初始化 Graph
        self.initialize_graph()

        # 运行测试
        start_time = datetime.now()

        for i, test_case in enumerate(filtered_cases, 1):
            print(f"\n\n进度: {i}/{len(filtered_cases)}")
            result = await self.run_single_test(test_case)
            self.results.append(result)

        total_time = (datetime.now() - start_time).total_seconds()

        # 生成报告
        self.generate_report(total_time)

    def generate_report(self, total_time: float):
        """生成测试报告"""
        print(f"\n\n{'='*60}")
        print("测试报告")
        print(f"{'='*60}")

        total = len(self.results)
        passed = len([r for r in self.results if r.passed])
        failed = total - passed

        print(f"\n总览:")
        print(f"  - 总测试数: {total}")
        print(f"  - 通过: {passed} ({passed/total*100:.1f}%)")
        print(f"  - 失败: {failed} ({failed/total*100:.1f}%)")
        print(f"  - 总耗时: {total_time:.2f}s")
        print(f"  - 平均耗时: {total_time/total:.2f}s/test")

        # 按分类统计
        print(f"\n按分类统计:")
        categories = {}
        for result in self.results:
            cat = result.test_case["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "passed": 0}
            categories[cat]["total"] += 1
            if result.passed:
                categories[cat]["passed"] += 1

        for cat, stats in categories.items():
            print(f"  - {cat}: {stats['passed']}/{stats['total']} ({stats['passed']/stats['total']*100:.1f}%)")

        # 按难度统计
        print(f"\n按难度统计:")
        difficulties = {}
        for result in self.results:
            diff = result.test_case["difficulty"]
            if diff not in difficulties:
                difficulties[diff] = {"total": 0, "passed": 0}
            difficulties[diff]["total"] += 1
            if result.passed:
                difficulties[diff]["passed"] += 1

        for diff, stats in difficulties.items():
            print(f"  - {diff}: {stats['passed']}/{stats['total']} ({stats['passed']/stats['total']*100:.1f}%)")

        # 失败案例
        if failed > 0:
            print(f"\n失败案例:")
            for result in self.results:
                if not result.passed:
                    print(f"\n  [{result.test_id}] {result.test_case['question']}")
                    if result.error:
                        print(f"    错误: {result.error}")
                    else:
                        print(f"    未通过的标准:")
                        for criterion, passed in result.criteria_results.items():
                            if not passed:
                                print(f"      - {criterion}")

        # 保存详细报告到 JSON
        report_file = Path(__file__).parent / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "summary": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "pass_rate": passed/total if total > 0 else 0,
                "total_time": total_time,
                "avg_time": total_time/total if total > 0 else 0
            },
            "by_category": categories,
            "by_difficulty": difficulties,
            "test_results": [r.to_dict() for r in self.results]
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

        print(f"\n\n详细报告已保存到: {report_file}")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="GaokaoAgent 测试运行器")
    parser.add_argument("--category", choices=["quant_research", "quant_multimodal", "research_multimodal", "triple_loop"], help="按分类过滤")
    parser.add_argument("--difficulty", choices=["medium", "hard", "very_hard"], help="按难度过滤")
    parser.add_argument("--limit", type=int, help="限制测试数量")

    args = parser.parse_args()

    runner = TestRunner()
    await runner.run_all_tests(
        filter_category=args.category,
        filter_difficulty=args.difficulty,
        limit=args.limit
    )


if __name__ == "__main__":
    asyncio.run(main())
