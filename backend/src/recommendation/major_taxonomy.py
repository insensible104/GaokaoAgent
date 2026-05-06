"""Rule-based major taxonomy for first-pass preference and risk analysis."""

from __future__ import annotations


CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "computer": ("计算机", "软件", "人工智能", "数据科学", "网络空间", "信息安全", "智能科学", "物联网"),
    "electronic_info": ("电子", "通信", "集成电路", "微电子", "自动化", "机器人工程", "智能感知"),
    "math_physics": ("数学", "统计", "物理", "力学", "信息与计算科学"),
    "finance": ("金融", "经济", "会计", "财务", "保险", "信用管理", "财政"),
    "law": ("法学", "知识产权", "政治学"),
    "medicine": ("临床医学", "口腔医学", "医学", "药学", "护理", "中医学"),
    "teacher": ("师范", "教育"),
    "language": ("英语", "日语", "法语", "德语", "俄语", "西班牙语", "外国语言", "翻译"),
    "civil_architecture": ("土木", "建筑", "城乡规划", "给排水", "道路", "桥梁", "地下空间"),
    "materials_chem_env": ("材料", "化学", "化工", "环境", "能源化学", "高分子", "无机非金属"),
    "bio_food_agri": ("生物", "食品", "农学", "林学", "植物", "动物", "水产"),
    "mechanical_energy": ("机械", "能源", "动力", "车辆", "制造", "储能", "新能源"),
    "transportation": ("交通", "航海", "轮机", "飞行", "航空", "航天"),
    "management": ("管理", "工商", "公共管理", "物流", "电子商务"),
    "art_design": ("设计", "美术", "音乐", "戏剧", "影视", "播音"),
}


def classify_major(major_name: str) -> str:
    """Classify a major name into a coarse domain category."""
    name = major_name or ""
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in name for keyword in keywords):
            return category
    return "other"


def infer_preferred_categories(preferred_majors: list[str]) -> set[str]:
    """Infer preferred categories from user-provided major keywords."""
    categories = set()
    for major in preferred_majors or []:
        category = classify_major(major)
        if category != "other":
            categories.add(category)
    return categories

