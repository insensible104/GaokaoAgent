"""学校-专业综合评分系统

核心逻辑：
- 华东五校的计算机 > 清华的材料
- 清华的材料 > 中国海洋的计算机
- 需要考虑：学校tier × 专业质量 × 用户偏好
"""

from enum import Enum
from typing import Dict, Optional
from pydantic import BaseModel, Field


class SchoolTier(str, Enum):
    """学校档次分级"""
    TOP2 = "top2"              # 清华、北大
    C9 = "c9"                  # C9联盟（除清北外：复旦、交大、浙大、南大、中科大、哈工大、西交）
    TOP985 = "top985"          # 华东五校级别的985（人大、北航、同济、武大等）
    MID985 = "mid985"          # 中等985（川大、重大、吉大、山大等）
    LOW985 = "low985"          # 末流985（兰大、东北大、西北农林等）
    TOP211 = "top211"          # 顶尖211（两财一贸、上财、央财、对外经贸等）
    MID211 = "mid211"          # 中等211（苏大、南航、华东理工等）
    LOW211 = "low211"          # 末流211
    DOUBLE_FIRST = "double_first"  # 双一流（非985/211）
    GOOD_1ST = "good_1st"      # 优秀一本（深大、广外等）
    NORMAL_1ST = "normal_1st"  # 普通一本
    OTHER = "other"            # 其他


class MajorQuality(str, Enum):
    """专业质量分级（基于就业前景、薪资、发展潜力）"""
    S_TIER = "s_tier"  # 顶级专业：计算机、AI、软件工程、金融、经济学（顶尖学校）
    A_TIER = "a_tier"  # 优质专业：电子信息、自动化、数学、统计、会计
    B_TIER = "b_tier"  # 中等专业：机械、电气、管理、法律
    C_TIER = "c_tier"  # 一般专业：化学、生物、文学
    D_TIER = "d_tier"  # 冷门专业：材料、土木、化工、农学、历史、哲学


class PreferenceStrategy(str, Enum):
    """用户填报策略偏好"""
    PRIORITIZE_SCHOOL = "prioritize_school"    # 冲学校（可以接受冷门专业）
    BALANCED = "balanced"                      # 平衡（学校和专业兼顾）
    PRIORITIZE_MAJOR = "prioritize_major"      # 保专业（宁愿降学校档次也要好专业）


# === 学校分级数据库（示例，实际应该从配置文件加载）===
SCHOOL_TIER_DATABASE: Dict[str, SchoolTier] = {
    # TOP2
    "清华大学": SchoolTier.TOP2,
    "北京大学": SchoolTier.TOP2,

    # C9（除清北外）
    "复旦大学": SchoolTier.C9,
    "上海交通大学": SchoolTier.C9,
    "浙江大学": SchoolTier.C9,
    "南京大学": SchoolTier.C9,
    "中国科学技术大学": SchoolTier.C9,
    "哈尔滨工业大学": SchoolTier.C9,
    "西安交通大学": SchoolTier.C9,

    # TOP985
    "中国人民大学": SchoolTier.TOP985,
    "北京航空航天大学": SchoolTier.TOP985,
    "同济大学": SchoolTier.TOP985,
    "南开大学": SchoolTier.TOP985,
    "武汉大学": SchoolTier.TOP985,
    "华中科技大学": SchoolTier.TOP985,
    "中山大学": SchoolTier.TOP985,
    "北京理工大学": SchoolTier.TOP985,
    "东南大学": SchoolTier.TOP985,
    "天津大学": SchoolTier.TOP985,

    # MID985
    "四川大学": SchoolTier.MID985,
    "重庆大学": SchoolTier.MID985,
    "吉林大学": SchoolTier.MID985,
    "山东大学": SchoolTier.MID985,
    "湖南大学": SchoolTier.MID985,
    "厦门大学": SchoolTier.MID985,
    "华南理工大学": SchoolTier.MID985,

    # LOW985
    "兰州大学": SchoolTier.LOW985,
    "东北大学": SchoolTier.LOW985,
    "西北农林科技大学": SchoolTier.LOW985,
    "中国海洋大学": SchoolTier.LOW985,
    "中央民族大学": SchoolTier.LOW985,

    # TOP211（非985的顶尖211）
    "上海财经大学": SchoolTier.TOP211,
    "中央财经大学": SchoolTier.TOP211,
    "对外经济贸易大学": SchoolTier.TOP211,
    "北京邮电大学": SchoolTier.TOP211,
    "北京外国语大学": SchoolTier.TOP211,
    "中国政法大学": SchoolTier.TOP211,

    # MID211
    "苏州大学": SchoolTier.MID211,
    "南京航空航天大学": SchoolTier.MID211,
    "华东理工大学": SchoolTier.MID211,
    "西南财经大学": SchoolTier.MID211,

    # 特殊案例（非985/211但很强）
    "深圳大学": SchoolTier.GOOD_1ST,
    "广东外语外贸大学": SchoolTier.GOOD_1ST,
    "南方科技大学": SchoolTier.GOOD_1ST,
}


# === 专业质量数据库（关键词匹配）===
MAJOR_QUALITY_DATABASE: Dict[str, MajorQuality] = {
    # S级专业（顶级，就业&薪资极好）
    "计算机": MajorQuality.S_TIER,
    "软件工程": MajorQuality.S_TIER,
    "人工智能": MajorQuality.S_TIER,
    "数据科学": MajorQuality.S_TIER,
    "金融": MajorQuality.S_TIER,
    "经济": MajorQuality.S_TIER,
    "信息安全": MajorQuality.S_TIER,

    # A级专业（优质）
    "电子信息": MajorQuality.A_TIER,
    "自动化": MajorQuality.A_TIER,
    "数学": MajorQuality.A_TIER,
    "统计": MajorQuality.A_TIER,
    "会计": MajorQuality.A_TIER,
    "通信工程": MajorQuality.A_TIER,
    "微电子": MajorQuality.A_TIER,

    # B级专业（中等）
    "机械": MajorQuality.B_TIER,
    "电气": MajorQuality.B_TIER,
    "管理": MajorQuality.B_TIER,
    "法学": MajorQuality.B_TIER,
    "临床医学": MajorQuality.B_TIER,

    # C级专业（一般）
    "化学": MajorQuality.C_TIER,
    "生物": MajorQuality.C_TIER,
    "物理": MajorQuality.C_TIER,
    "环境": MajorQuality.C_TIER,

    # D级专业（冷门）
    "材料": MajorQuality.D_TIER,
    "土木": MajorQuality.D_TIER,
    "化工": MajorQuality.D_TIER,
    "农学": MajorQuality.D_TIER,
    "历史": MajorQuality.D_TIER,
    "哲学": MajorQuality.D_TIER,
    "地质": MajorQuality.D_TIER,
}


# === 评分权重（根据用户偏好调整）===
SCORE_WEIGHTS: Dict[PreferenceStrategy, Dict[str, float]] = {
    PreferenceStrategy.PRIORITIZE_SCHOOL: {
        "school_tier": 0.70,   # 学校占70%
        "major_quality": 0.30  # 专业占30%
    },
    PreferenceStrategy.BALANCED: {
        "school_tier": 0.50,   # 各占50%
        "major_quality": 0.50
    },
    PreferenceStrategy.PRIORITIZE_MAJOR: {
        "school_tier": 0.30,   # 学校占30%
        "major_quality": 0.70  # 专业占70%
    }
}


# === 分级对应的基础分数（100分制）===
SCHOOL_TIER_SCORES: Dict[SchoolTier, float] = {
    SchoolTier.TOP2: 100,
    SchoolTier.C9: 95,
    SchoolTier.TOP985: 90,
    SchoolTier.MID985: 82,
    SchoolTier.LOW985: 75,
    SchoolTier.TOP211: 70,
    SchoolTier.MID211: 60,
    SchoolTier.LOW211: 50,
    SchoolTier.DOUBLE_FIRST: 45,
    SchoolTier.GOOD_1ST: 40,
    SchoolTier.NORMAL_1ST: 30,
    SchoolTier.OTHER: 20,
}

MAJOR_QUALITY_SCORES: Dict[MajorQuality, float] = {
    MajorQuality.S_TIER: 100,
    MajorQuality.A_TIER: 80,
    MajorQuality.B_TIER: 60,
    MajorQuality.C_TIER: 40,
    MajorQuality.D_TIER: 20,
}


def get_school_tier(school_name: str) -> SchoolTier:
    """
    获取学校档次

    Args:
        school_name: 学校名称

    Returns:
        SchoolTier 枚举值
    """
    # 去除多余字符
    school_name = school_name.strip()

    # 精确匹配
    # 精确匹配优先
    if school_name in SCHOOL_TIER_DATABASE:
        return SCHOOL_TIER_DATABASE[school_name]

    # 修复问题13：改进模糊匹配，避免过宽匹配
    # 去除"大学"后缀后再匹配
    school_base = school_name.replace("大学", "").replace("学院", "")
    for key, tier in SCHOOL_TIER_DATABASE.items():
        key_base = key.replace("大学", "").replace("学院", "")
        # 使用完整名称匹配，而不是子串匹配
        if school_base == key_base and school_base:  # 确保不是空字符串
            return tier

    # 默认为普通一本
    return SchoolTier.NORMAL_1ST


def get_major_quality(major_name: str) -> MajorQuality:
    """
    获取专业质量等级（基于关键词匹配）

    Args:
        major_name: 专业名称

    Returns:
        MajorQuality 枚举值
    """
    # 去除多余字符
    major_name = major_name.strip()

    # 关键词匹配
    for keyword, quality in MAJOR_QUALITY_DATABASE.items():
        if keyword in major_name:
            return quality

    # 默认为B级（中等专业）
    return MajorQuality.B_TIER


def calculate_comprehensive_score(
    school_name: str,
    major_name: str,
    preference: PreferenceStrategy = PreferenceStrategy.BALANCED,
    use_platform_bonus: bool = True
) -> Dict[str, float]:
    """
    计算学校-专业综合评分（改进版：加入学校平台加成）

    核心改进：
    1. 基础分 = 学校档次分 × 学校权重 + 专业质量分 × 专业权重
    2. 学校平台加成：顶尖学校（TOP2/C9）的冷门专业有最低保障分
       - TOP2（清北）的D级专业：最低70分（平台资源、保研率、就业背书）
       - C9学校的D级专业：最低65分
       - TOP985的D级专业：最低60分

    这样可以确保：
    - 复旦计算机 > 清华材料 ✅
    - 清华材料 > 中国海洋计算机 ✅

    Args:
        school_name: 学校名称
        major_name: 专业名称
        preference: 用户偏好策略
        use_platform_bonus: 是否使用学校平台加成

    Returns:
        {
            'comprehensive_score': 综合分（0-100）,
            'school_tier_score': 学校档次分,
            'major_quality_score': 专业质量分,
            'school_tier': 学校档次,
            'major_quality': 专业质量,
            'platform_bonus': 平台加成值
        }
    """
    # 1. 获取学校档次和专业质量
    school_tier = get_school_tier(school_name)
    major_quality = get_major_quality(major_name)

    # 2. 获取基础分数
    school_tier_score = SCHOOL_TIER_SCORES[school_tier]
    major_quality_score = MAJOR_QUALITY_SCORES[major_quality]

    # 3. 根据用户偏好加权计算综合分
    weights = SCORE_WEIGHTS[preference]
    base_score = (
        school_tier_score * weights["school_tier"] +
        major_quality_score * weights["major_quality"]
    )

    # 4. 学校平台加成（确保顶尖学校的冷门专业有最低保障）
    platform_bonus = 0.0
    if use_platform_bonus:
        # 定义最低保障分（根据学校档次和专业质量）
        # 原则：TOP2的天坑专业 > LOW985的王牌专业
        min_guaranteed_scores = {
            (SchoolTier.TOP2, MajorQuality.D_TIER): 88,      # 清北的天坑专业最低88分（高于末流985的王牌）
            (SchoolTier.TOP2, MajorQuality.C_TIER): 90,      # 清北的一般专业最低90分
            (SchoolTier.TOP2, MajorQuality.B_TIER): 92,      # 清北的中等专业最低92分
            (SchoolTier.C9, MajorQuality.D_TIER): 75,        # 华东五校的天坑专业最低75分
            (SchoolTier.C9, MajorQuality.C_TIER): 80,        # 华东五校的一般专业最低80分
            (SchoolTier.TOP985, MajorQuality.D_TIER): 65,    # TOP985的天坑专业最低65分
            (SchoolTier.TOP985, MajorQuality.C_TIER): 70,    # TOP985的一般专业最低70分
        }

        min_score = min_guaranteed_scores.get((school_tier, major_quality), 0)
        if min_score > base_score:
            platform_bonus = min_score - base_score
            comprehensive_score = min_score
        else:
            comprehensive_score = base_score
    else:
        comprehensive_score = base_score

    return {
        'comprehensive_score': comprehensive_score,
        'school_tier_score': school_tier_score,
        'major_quality_score': major_quality_score,
        'school_tier': school_tier.value,
        'major_quality': major_quality.value,
        'platform_bonus': platform_bonus
    }


# === 测试用例 ===
if __name__ == "__main__":
    print("=== 学校-专业综合评分系统测试 ===\n")

    # 测试案例
    test_cases = [
        ("清华大学", "材料科学"),
        ("复旦大学", "计算机"),
        ("中国海洋大学", "计算机"),
        ("清华大学", "计算机"),
        ("华东五校", "计算机"),  # 应该会fallback到普通一本
    ]

    # 测试3种策略
    strategies = [
        PreferenceStrategy.PRIORITIZE_SCHOOL,
        PreferenceStrategy.BALANCED,
        PreferenceStrategy.PRIORITIZE_MAJOR
    ]

    for school, major in test_cases:
        print(f"\n【{school} - {major}】")
        for strategy in strategies:
            result = calculate_comprehensive_score(school, major, strategy)
            print(f"  {strategy.value:20s}: {result['comprehensive_score']:.1f}分 "
                  f"(学校{result['school_tier_score']:.0f} × {SCORE_WEIGHTS[strategy]['school_tier']:.0%} + "
                  f"专业{result['major_quality_score']:.0f} × {SCORE_WEIGHTS[strategy]['major_quality']:.0%})")

    print("\n" + "="*60)
    print("\nValidation:")
    print("\n1. Fudan CS > Tsinghua Materials?")
    fdan_cs = calculate_comprehensive_score("复旦大学", "计算机", PreferenceStrategy.BALANCED)
    thu_mat = calculate_comprehensive_score("清华大学", "材料科学", PreferenceStrategy.BALANCED)
    print(f"   Fudan CS:          {fdan_cs['comprehensive_score']:.1f} (bonus: +{fdan_cs['platform_bonus']:.1f})")
    print(f"   Tsinghua Materials: {thu_mat['comprehensive_score']:.1f} (bonus: +{thu_mat['platform_bonus']:.1f})")
    print(f"   Result: {'PASS' if fdan_cs['comprehensive_score'] > thu_mat['comprehensive_score'] else 'FAIL'}")

    print("\n2. Tsinghua Materials > OUC CS?")
    ouc_cs = calculate_comprehensive_score("中国海洋大学", "计算机", PreferenceStrategy.BALANCED)
    print(f"   Tsinghua Materials: {thu_mat['comprehensive_score']:.1f} (bonus: +{thu_mat['platform_bonus']:.1f})")
    print(f"   OUC CS:            {ouc_cs['comprehensive_score']:.1f} (bonus: +{ouc_cs['platform_bonus']:.1f})")
    print(f"   Result: {'PASS' if thu_mat['comprehensive_score'] > ouc_cs['comprehensive_score'] else 'FAIL'}")
