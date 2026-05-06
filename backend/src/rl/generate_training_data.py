"""生成GRPO训练数据集脚本

运行此脚本生成1000个真实训练样本，并保存为JSON文件供GRPO训练器使用。

Usage:
    cd backend
    python -m src.rl.generate_training_data
"""

import json
from pathlib import Path
import sys

# 添加路径
sys.path.append(str(Path(__file__).parent.parent))

from rl.realistic_data_generator import RealisticTrainingDataGenerator


def main():
    """主函数"""
    print("\n" + "="*70)
    print("GRPO训练数据生成脚本")
    print("="*70)

    # 配置
    config = {
        "n_cases": 100,  # 先生成100个测试
        "year": 2024,
        "category": "物理",
        "rank_range": (5000, 80000),
        "candidate_pool_size": 100,
        "n_simulations": 1000,  # 测试用少量模拟
        "verbose": False  # 关闭详细输出
    }

    print("\n配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")
    print()

    # 创建生成器
    print("初始化真实数据生成器...")
    generator = RealisticTrainingDataGenerator(data_dir="data")

    # 生成训练数据
    print("\n开始生成训练数据...")
    training_cases = generator.generate_training_cases(**config)

    # 保存到JSON
    output_dir = Path("rl_checkpoints")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "grpo_training_data_realistic.json"

    print(f"\n保存训练数据到: {output_file}")

    # 转换为可序列化的格式
    data_to_save = []
    for case in training_cases:
        data_to_save.append({
            "user_features": {
                "rank": case.user_features.rank,
                "rank_normalized": case.user_features.rank_normalized,
                "risk_tolerance": case.user_features.risk_tolerance,
                "major_priority": case.user_features.major_priority
            },
            "candidate_pool": [
                {
                    "school_tier": c.school_tier,
                    "admission_prob": c.admission_prob,
                    "major_satisfaction": c.major_satisfaction,
                    "adjustment_risk": c.adjustment_risk,
                    "rank_diff_normalized": c.rank_diff_normalized,
                    "comprehensive_score": c.comprehensive_score
                }
                for c in case.candidate_pool
            ]
        })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=2)

    print(f"保存成功！共{len(data_to_save)}个训练样本")

    # 统计信息
    print("\n" + "="*70)
    print("数据集统计:")
    print("="*70)

    total_candidates = sum(len(case.candidate_pool) for case in training_cases)
    avg_candidates = total_candidates / len(training_cases) if training_cases else 0

    ranks = [case.user_features.rank for case in training_cases]
    risk_tolerances = [case.user_features.risk_tolerance for case in training_cases]
    major_priorities = [case.user_features.major_priority for case in training_cases]

    print(f"训练样本数: {len(training_cases)}")
    print(f"平均候选池大小: {avg_candidates:.1f}")
    print(f"\n排位分布:")
    print(f"  最小: {min(ranks) if ranks else 0}")
    print(f"  最大: {max(ranks) if ranks else 0}")
    print(f"  平均: {sum(ranks) / len(ranks) if ranks else 0:.0f}")
    print(f"\n风险偏好分布:")
    print(f"  平均: {sum(risk_tolerances) / len(risk_tolerances) if risk_tolerances else 0:.2f}")
    print(f"\n专业优先度分布:")
    print(f"  平均: {sum(major_priorities) / len(major_priorities) if major_priorities else 0:.2f}")

    print("\n" + "="*70)
    print("完成！可以开始训练GRPO模型了")
    print("="*70)


if __name__ == "__main__":
    main()
