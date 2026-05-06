"""
用户输入验证器
验证分数、位次、选科组合等信息的合法性
"""
from typing import Dict, Any, Tuple, Optional
from utils.yifenyiduan import YiFenYiDuanManager


class UserInputValidator:
    """用户输入验证器"""

    def __init__(self, data_dir: str = "data"):
        """
        初始化验证器

        Args:
            data_dir: 数据目录路径
        """
        self.yifenyiduan = YiFenYiDuanManager(data_dir)

    def validate_user_input(
        self,
        data: Dict[str, Any]
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        验证用户输入数据

        Args:
            data: 用户输入数据字典

        Returns:
            (是否通过验证, 错误信息, 修正后的数据)
        """
        # 提取关键字段
        score = data.get('score')
        rank = data.get('rank')
        subject_group = data.get('subject_group', '物理')

        # 标准化选科组合
        if '物' in subject_group or 'physics' in subject_group.lower():
            category = '物理'
        elif '历' in subject_group or '史' in subject_group or 'history' in subject_group.lower():
            category = '历史'
        else:
            return False, f"不支持的选科组合：{subject_group}，请选择物理类或历史类", None

        # 情况1: 只提供位次（推荐方式）
        if rank is not None and score is None:
            # 根据位次推算分数
            estimated_score = self.yifenyiduan.rank_to_score(rank, category)
            if estimated_score is None:
                return False, f"无法根据位次 {rank} 推算分数，请检查位次是否在合理范围内", None

            print(f"[INFO] 根据位次 {rank} 推算分数：{estimated_score}")

            # 返回修正后的数据
            corrected_data = data.copy()
            corrected_data['score'] = estimated_score
            corrected_data['rank'] = rank
            corrected_data['subject_group'] = category

            return True, None, corrected_data

        # 情况2: 同时提供分数和位次（需要验证一致性）
        elif score is not None and rank is not None:
            # 验证分数和位次是否匹配
            is_valid, error_msg = self.yifenyiduan.validate_score_rank_match(
                score, rank, category, tolerance=1000
            )

            if not is_valid:
                # 优先以位次为准，推算正确的分数
                correct_score = self.yifenyiduan.rank_to_score(rank, category)

                return False, (
                    f"[WARN] 分数与位次不匹配！\n\n"
                    f"{error_msg}\n\n"
                    f"[建议] 我们将优先使用您的位次 {rank}，对应的分数约为 {correct_score} 分\n"
                    f"请确认是否继续？"
                ), None

            # 验证通过
            corrected_data = data.copy()
            corrected_data['subject_group'] = category
            return True, None, corrected_data

        # 情况3: 只提供分数（不推荐，但允许）
        elif score is not None and rank is None:
            # 根据分数推算位次
            estimated_rank = self.yifenyiduan.score_to_rank(score, category)
            if estimated_rank is None:
                return False, f"无法根据分数 {score} 推算位次，请检查分数是否在合理范围内", None

            print(f"[INFO] 根据分数 {score} 推算位次：{estimated_rank}")

            # 返回修正后的数据
            corrected_data = data.copy()
            corrected_data['score'] = score
            corrected_data['rank'] = estimated_rank
            corrected_data['subject_group'] = category

            return True, None, corrected_data

        # 情况4: 分数和位次都没有
        else:
            return False, "请提供分数或位次信息", None

    def get_validation_hints(self, subject_group: str) -> str:
        """
        获取验证提示信息

        Args:
            subject_group: 选科组合

        Returns:
            提示信息
        """
        # 标准化选科组合
        if '物' in subject_group or 'physics' in subject_group.lower():
            category = '物理'
        elif '历' in subject_group or '史' in subject_group or 'history' in subject_group.lower():
            category = '历史'
        else:
            category = '物理'

        # 获取分数和位次范围
        score_min, score_max = self.yifenyiduan.get_score_range(category)
        rank_min, rank_max = self.yifenyiduan.get_rank_range(category)

        return (
            f"📊 {category}类考生数据范围（2024年参考）：\n"
            f"  • 分数范围：{score_min} - {score_max} 分\n"
            f"  • 位次范围：{rank_min} - {rank_max}\n\n"
            f"💡 建议：优先提供位次信息，系统会自动推算对应分数"
        )
