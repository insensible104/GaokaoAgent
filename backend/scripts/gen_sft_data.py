"""SFT 训练数据生成器（Supervised Fine-Tuning Data Generator）

生成 (Question, Thought_Trace, Tool_Call) 三元组
用于训练 Router Agent 的工具选择能力
"""
import json
import random
from pathlib import Path
from typing import List, Dict
import pandas as pd


class SFTDataGenerator:
    """SFT 数据生成器"""

    def __init__(self, csv_dir: str = "data"):
        """
        初始化生成器

        Args:
            csv_dir: CSV 数据目录
        """
        self.csv_dir = Path(csv_dir)
        self.schools = []
        self.majors = []
        self.load_data()

    def load_data(self):
        """加载 CSV 数据"""
        csv_files = list(self.csv_dir.glob("*.csv"))

        if not csv_files:
            print(f"[WARN] 未找到 CSV 文件在 {self.csv_dir}")
            return

        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, encoding='utf-8-sig')
            except:
                df = pd.read_csv(csv_file, encoding='gbk')

            # 提取学校和专业名称
            if 'school' in df.columns:
                self.schools.extend(df['school'].unique().tolist())
            if 'major' in df.columns:
                self.majors.extend(df['major'].unique().tolist())

        # 去重
        self.schools = list(set(self.schools))
        self.majors = list(set(self.majors))

        print(f"[OK] 加载了 {len(self.schools)} 所学校，{len(self.majors)} 个专业")

    def generate_all_data(self, output_file: str = "sft_training_data.jsonl"):
        """
        生成所有类型的训练数据

        Args:
            output_file: 输出文件路径
        """
        all_data = []

        # 1. 定量问题（使用 quant_engine）
        all_data.extend(self.generate_quant_questions(num_samples=50))

        # 2. 研究问题（使用 search_tool）
        all_data.extend(self.generate_research_questions(num_samples=30))

        # 3. 多模态问题（使用 pdf_parser / vision_analyzer）
        all_data.extend(self.generate_multimodal_questions(num_samples=20))

        # 4. 负例（错误的工具调用）
        all_data.extend(self.generate_negative_examples(num_samples=30))

        # 写入文件
        output_path = Path(output_file)
        with open(output_path, 'w', encoding='utf-8') as f:
            for item in all_data:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')

        print(f"[OK] 生成了 {len(all_data)} 条训练数据 -> {output_path}")

        return all_data

    def generate_quant_questions(self, num_samples: int) -> List[Dict]:
        """生成定量分析问题（正例）"""
        data = []

        templates = [
            {
                "question": "我{score}分，位次{rank}，能上{school}{major}吗？",
                "thought": "这是典型的录取概率计算问题，需要访问历史录取数据。CSV 中有 school、major、min_rank 等字段，应该使用 quant_engine。",
                "tool_call": "quant_engine.search(school='{school}', major='{major}', user_rank={rank})"
            },
            {
                "question": "{school}{major}的最低录取位次是多少？",
                "thought": "查询历史最低录取位次，这是结构化数据，在 CSV 的 min_rank 字段中，应该使用 quant_engine。",
                "tool_call": "quant_engine.get_min_rank(school='{school}', major='{major}')"
            },
            {
                "question": "推荐一些{score}分能上的{major}专业",
                "thought": "根据分数筛选专业，需要计算录取概率，属于量化分析任务，使用 quant_engine。",
                "tool_call": "quant_engine.search_by_score(score={score}, major='{major}')"
            },
            {
                "question": "位次{rank}冲刺哪些985大学比较稳？",
                "thought": "根据位次推荐院校，需要计算冲稳保策略，这是量化引擎的核心功能，使用 quant_engine。",
                "tool_call": "quant_engine.recommend_schools(user_rank={rank}, school_type='985', strategy='stable')"
            },
        ]

        for _ in range(num_samples):
            template = random.choice(templates)
            school = random.choice(self.schools) if self.schools else "清华大学"
            major = random.choice(self.majors) if self.majors else "计算机"
            score = random.randint(550, 700)
            rank = random.randint(1000, 50000)

            question = template["question"].format(
                school=school, major=major, score=score, rank=rank
            )
            thought = template["thought"].format(
                school=school, major=major, score=score, rank=rank
            )
            tool_call = template["tool_call"].format(
                school=school, major=major, score=score, rank=rank
            )

            data.append({
                "question": question,
                "thought": thought,
                "tool_call": tool_call,
                "tool_type": "quant_engine",
                "label": "positive",
                "category": "quantitative"
            })

        return data

    def generate_research_questions(self, num_samples: int) -> List[Dict]:
        """生成研究问题（正例）"""
        data = []

        templates = [
            {
                "question": "{school}{major}的保研率是多少？",
                "thought": "保研率不在 CSV 数据中，需要通过网络搜索获取，应该使用 search_tool。",
                "tool_call": "search_tool.invoke('{school} {major} 保研率')"
            },
            {
                "question": "{school}在哪个城市？",
                "thought": "地址信息不在量化数据中，属于基本信息查询，应该使用 search_tool。",
                "tool_call": "search_tool.invoke('{school} 地址 城市')"
            },
            {
                "question": "{major}专业的就业前景怎么样？",
                "thought": "就业前景属于定性分析，需要查找行业报告、评价等非结构化信息，使用 search_tool。",
                "tool_call": "search_tool.invoke('{major} 就业前景 薪资')"
            },
            {
                "question": "{school}的学科评估结果是什么？",
                "thought": "学科评估结果属于教育部公开数据，不在我们的 CSV 中，需要网络搜索，使用 search_tool。",
                "tool_call": "search_tool.invoke('{school} 学科评估 第五轮')"
            },
        ]

        for _ in range(num_samples):
            template = random.choice(templates)
            school = random.choice(self.schools) if self.schools else "清华大学"
            major = random.choice(self.majors) if self.majors else "计算机"

            question = template["question"].format(school=school, major=major)
            thought = template["thought"].format(school=school, major=major)
            tool_call = template["tool_call"].format(school=school, major=major)

            data.append({
                "question": question,
                "thought": thought,
                "tool_call": tool_call,
                "tool_type": "search_tool",
                "label": "positive",
                "category": "research"
            })

        return data

    def generate_multimodal_questions(self, num_samples: int) -> List[Dict]:
        """生成多模态问题（正例）"""
        data = []

        templates = [
            {
                "question": "我色弱，能报{school}{major}吗？",
                "thought": "这是体检限制问题，需要查询招生章程中的体检要求。招生章程是 PDF 文档，应该使用 pdf_parser 提取体检要求段落。",
                "tool_call": "pdf_parser.extract_health_requirements('{school}招生章程.pdf')"
            },
            {
                "question": "{school}的单科成绩有要求吗？",
                "thought": "单科成绩要求在招生章程的录取规则部分，属于 PDF 文档解析任务，使用 pdf_parser。",
                "tool_call": "pdf_parser.extract_admission_rules('{school}招生章程.pdf')"
            },
            {
                "question": "{school}的学费是多少？",
                "thought": "学费信息在招生章程中，但不一定在 CSV 数据中，应该先尝试 pdf_parser。",
                "tool_call": "pdf_parser.extract_sections_by_keywords('{school}招生章程.pdf', keywords=['学费', '收费'])"
            },
        ]

        for _ in range(num_samples):
            template = random.choice(templates)
            school = random.choice(self.schools) if self.schools else "清华大学"
            major = random.choice(self.majors) if self.majors else "计算机"

            question = template["question"].format(school=school, major=major)
            thought = template["thought"].format(school=school, major=major)
            tool_call = template["tool_call"].format(school=school, major=major)

            data.append({
                "question": question,
                "thought": thought,
                "tool_call": tool_call,
                "tool_type": "pdf_parser",
                "label": "positive",
                "category": "multimodal"
            })

        return data

    def generate_negative_examples(self, num_samples: int) -> List[Dict]:
        """生成负例（错误的工具调用）"""
        data = []

        # 负例类型 1：用 quant_engine 查非结构化信息
        negative_templates_quant = [
            {
                "question": "{school}在哪个城市？",
                "thought": "错误推理：尝试用量化引擎查询地址。",
                "tool_call": "quant_engine.search(school='{school}')",
                "correct_tool": "search_tool",
                "error_reason": "地址信息不在结构化数据中，不应使用 quant_engine"
            },
            {
                "question": "{school}的校训是什么？",
                "thought": "错误推理：尝试用量化引擎查询校训。",
                "tool_call": "quant_engine.get_info(school='{school}', field='motto')",
                "correct_tool": "search_tool",
                "error_reason": "校训不是录取数据，不应使用 quant_engine"
            },
        ]

        # 负例类型 2：用 search_tool 查结构化数据
        negative_templates_search = [
            {
                "question": "{school}{major}的最低录取位次是多少？",
                "thought": "错误推理：尝试用搜索工具查询精确的位次数据。",
                "tool_call": "search_tool.invoke('{school} {major} 最低位次')",
                "correct_tool": "quant_engine",
                "error_reason": "精确的录取位次在 CSV 数据中，应使用 quant_engine"
            },
        ]

        # 生成负例
        for _ in range(num_samples // 2):
            template = random.choice(negative_templates_quant)
            school = random.choice(self.schools) if self.schools else "清华大学"
            major = random.choice(self.majors) if self.majors else "计算机"

            data.append({
                "question": template["question"].format(school=school, major=major),
                "thought": template["thought"].format(school=school, major=major),
                "tool_call": template["tool_call"].format(school=school, major=major),
                "tool_type": template["correct_tool"],
                "label": "negative",
                "category": "wrong_tool",
                "error_reason": template["error_reason"]
            })

        for _ in range(num_samples // 2):
            template = random.choice(negative_templates_search)
            school = random.choice(self.schools) if self.schools else "清华大学"
            major = random.choice(self.majors) if self.majors else "计算机"

            data.append({
                "question": template["question"].format(school=school, major=major),
                "thought": template["thought"].format(school=school, major=major),
                "tool_call": template["tool_call"].format(school=school, major=major),
                "tool_type": template["correct_tool"],
                "label": "negative",
                "category": "wrong_tool",
                "error_reason": template["error_reason"]
            })

        return data


def main():
    """主函数"""
    print("=" * 60)
    print("GaokaoAgent - SFT 训练数据生成器")
    print("=" * 60)

    generator = SFTDataGenerator(csv_dir="data")
    data = generator.generate_all_data(output_file="data/sft_training_data.jsonl")

    # 统计信息
    positive = len([d for d in data if d['label'] == 'positive'])
    negative = len([d for d in data if d['label'] == 'negative'])

    print("\n统计信息：")
    print(f"- 总样本数: {len(data)}")
    print(f"- 正例: {positive}")
    print(f"- 负例: {negative}")
    print(f"- 定量问题: {len([d for d in data if d.get('category') == 'quantitative'])}")
    print(f"- 研究问题: {len([d for d in data if d.get('category') == 'research'])}")
    print(f"- 多模态问题: {len([d for d in data if d.get('category') == 'multimodal'])}")

    # 展示几个示例
    print("\n示例数据：")
    for i, example in enumerate(random.sample(data, min(3, len(data)))):
        print(f"\n--- 示例 {i+1} ({example['label']}) ---")
        print(f"问题: {example['question']}")
        print(f"思考: {example['thought']}")
        print(f"工具: {example['tool_call']}")


if __name__ == "__main__":
    main()

