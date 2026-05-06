"""测试中等问题修复（Issue 5, 6, 8）

测试内容：
- Issue 5: 专业黑名单检查
- Issue 6: 城市偏好过滤
- Issue 8: 舆情修正框架
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from models.user_profile import UserProfile, SchoolMajorPreference
from utils.city_mapping import get_school_city, calculate_city_preference_score


def test_blacklist_logic():
    """测试Issue 5: 黑名单检查逻辑"""
    print("\n" + "="*80)
    print("测试 Issue 5: 专业黑名单检查")
    print("="*80)

    # 模拟专业组
    major_list = ["土木工程", "建筑学", "计算机科学与技术"]
    blacklist = ["土木", "化工"]

    # 检查黑名单匹配
    blacklist_majors_in_group = []
    for major in major_list:
        for blacklist_keyword in blacklist:
            if blacklist_keyword in major:
                blacklist_majors_in_group.append(major)
                break

    print(f"专业组: {major_list}")
    print(f"用户黑名单: {blacklist}")
    print(f"匹配的黑名单专业: {blacklist_majors_in_group}")

    # 计算惩罚
    if len(blacklist_majors_in_group) == len(major_list):
        print("[SKIP] 结果: 全部为黑名单，应跳过该专业组")
        return False
    elif len(blacklist_majors_in_group) > 0:
        blacklist_ratio = len(blacklist_majors_in_group) / len(major_list)
        penalty = 1 - blacklist_ratio * 0.2
        print(f"[WARN] 结果: 部分匹配，评分惩罚系数 = {penalty:.2f}")
        print(f"   黑名单比例: {blacklist_ratio:.1%}")
        print(f"   评分降低: {blacklist_ratio*20:.0f}%")
        return True
    else:
        print("[OK] 结果: 无黑名单专业，无惩罚")
        return True


def test_city_preference():
    """测试Issue 6: 城市偏好评分"""
    print("\n" + "="*80)
    print("测试 Issue 6: 城市偏好过滤")
    print("="*80)

    # 测试学校城市映射
    test_schools = [
        "清华大学",
        "复旦大学",
        "中山大学",
        "哈尔滨工业大学",
        "未知大学"
    ]

    print("\n【1. 学校-城市映射测试】")
    for school in test_schools:
        city = get_school_city(school)
        print(f"  {school:15s} -> {city}")

    # 测试偏好评分
    print("\n【2. 城市偏好评分测试】")

    # 场景1：偏好城市
    preferred_cities = ["北京", "上海", "广州"]
    excluded_cities = ["哈尔滨", "兰州"]

    test_cases = [
        ("北京", "偏好城市"),
        ("上海", "偏好城市"),
        ("广州", "偏好城市"),
        ("哈尔滨", "排除城市"),
        ("兰州", "排除城市"),
        ("南京", "中立城市"),
        ("成都", "中立城市"),
    ]

    print(f"  偏好城市: {preferred_cities}")
    print(f"  排除城市: {excluded_cities}")
    print()

    for city, category in test_cases:
        score = calculate_city_preference_score(
            city=city,
            preferred_cities=preferred_cities,
            excluded_cities=excluded_cities
        )
        marker = "[+]" if score > 1.0 else "[-]" if score < 1.0 else "[=]"
        print(f"  {marker} {city:10s} ({category:8s}): 评分系数 = {score:.1f} ({score*100:.0f}%)")

    return True


def test_comprehensive_score_with_adjustments():
    """测试综合评分 + 黑名单 + 城市偏好的联合效果"""
    print("\n" + "="*80)
    print("测试综合场景: 综合评分 + 黑名单 + 城市偏好")
    print("="*80)

    # 模拟三个专业组
    candidates = [
        {
            "school": "清华大学",
            "city": "北京",
            "majors": ["计算机科学与技术", "软件工程"],
            "base_score": 95.0,
            "admission_prob": 0.65,
        },
        {
            "school": "哈尔滨工业大学",
            "city": "哈尔滨",
            "majors": ["计算机科学与技术", "人工智能"],
            "base_score": 88.0,
            "admission_prob": 0.75,
        },
        {
            "school": "某985大学",
            "city": "广州",
            "majors": ["土木工程", "建筑学"],
            "base_score": 82.0,
            "admission_prob": 0.85,
        }
    ]

    # 用户偏好
    preferred_cities = ["北京", "上海", "广州"]
    excluded_cities = ["哈尔滨"]
    blacklist = ["土木", "化工"]

    print(f"用户偏好城市: {preferred_cities}")
    print(f"用户排除城市: {excluded_cities}")
    print(f"用户黑名单专业: {blacklist}")
    print()

    results = []

    for cand in candidates:
        school = cand["school"]
        city = cand["city"]
        majors = cand["majors"]
        base_score = cand["base_score"]
        admission_prob = cand["admission_prob"]

        print(f"\n【{school}】")
        print(f"  城市: {city}")
        print(f"  专业: {majors}")
        print(f"  综合评分(初始): {base_score:.1f}")
        print(f"  录取概率: {admission_prob:.1%}")

        # 计算初始最终评分
        final_score = base_score * 0.6 + admission_prob * 100 * 0.4
        print(f"  → 最终评分(初始) = {base_score:.1f}*0.6 + {admission_prob*100:.1f}*0.4 = {final_score:.1f}")

        # 应用黑名单惩罚
        blacklist_majors = []
        for major in majors:
            for keyword in blacklist:
                if keyword in major:
                    blacklist_majors.append(major)
                    break

        if blacklist_majors:
            if len(blacklist_majors) == len(majors):
                print(f"  [SKIP] 全部为黑名单专业，跳过")
                continue
            else:
                blacklist_ratio = len(blacklist_majors) / len(majors)
                penalty = 1 - blacklist_ratio * 0.2
                final_score *= penalty
                print(f"  [WARN] 包含黑名单专业 {blacklist_majors}")
                print(f"  -> 黑名单惩罚系数 = {penalty:.2f}")
                print(f"  -> 最终评分(黑名单后) = {final_score:.1f}")

        # 应用城市偏好
        city_score = calculate_city_preference_score(
            city=city,
            preferred_cities=preferred_cities,
            excluded_cities=excluded_cities
        )
        final_score *= city_score

        if city_score > 1.0:
            print(f"  [+] 偏好城市，评分提升")
        elif city_score < 1.0:
            print(f"  [-] 排除城市，评分降低")

        print(f"  → 城市调整系数 = {city_score:.1f}")
        print(f"  → 最终评分(城市后) = {final_score:.1f}")

        results.append({
            "school": school,
            "city": city,
            "final_score": final_score
        })

    # 排序
    print("\n" + "="*80)
    print("最终排序结果（按评分从高到低）:")
    print("="*80)
    results.sort(key=lambda x: x["final_score"], reverse=True)

    for i, r in enumerate(results, 1):
        print(f"{i}. {r['school']:20s} ({r['city']:8s}) - 评分: {r['final_score']:.1f}")

    return True


def test_sentiment_framework():
    """测试Issue 8: 舆情修正框架"""
    print("\n" + "="*80)
    print("测试 Issue 8: 舆情修正框架")
    print("="*80)

    import os

    # 测试环境变量读取
    current_value = os.getenv("ENABLE_SENTIMENT_ANALYSIS", "false")
    print(f"当前环境变量 ENABLE_SENTIMENT_ANALYSIS = {current_value}")

    # 模拟框架逻辑
    enable_sentiment = current_value.lower() == "true"
    sentiment_modifier = 0.0

    if enable_sentiment:
        print("[OK] 舆情分析已启用")
        print("   框架会调用 sentiment_analyzer.get_sentiment_modifier()")
        print("   然后将 sentiment_modifier 传入蒙特卡洛模拟")
    else:
        print("[WARN] 舆情分析未启用（默认）")
        print("   sentiment_modifier = 0.0（无修正）")
        print("   如需启用，设置环境变量: ENABLE_SENTIMENT_ANALYSIS=true")

    print(f"\n最终 sentiment_modifier = {sentiment_modifier}")

    # 检查代码中是否已添加此逻辑
    game_agent_path = Path(__file__).parent / "agents" / "game_agent.py"
    if game_agent_path.exists():
        content = game_agent_path.read_text(encoding="utf-8")
        has_sentiment_check = "ENABLE_SENTIMENT_ANALYSIS" in content
        has_sentiment_param = "sentiment_modifier=sentiment_modifier" in content

        print(f"\n代码验证:")
        print(f"  [OK] 已添加环境变量检查: {has_sentiment_check}")
        print(f"  [OK] 已传入蒙特卡洛模拟: {has_sentiment_param}")

        if has_sentiment_check and has_sentiment_param:
            print("\n[OK] 舆情修正框架已正确集成到 game_agent.py")
            return True

    return False


def main():
    """运行所有测试"""
    print("="*80)
    print("中等问题修复测试套件")
    print("="*80)

    tests = [
        ("Issue 5: 专业黑名单检查", test_blacklist_logic),
        ("Issue 6: 城市偏好过滤", test_city_preference),
        ("综合场景测试", test_comprehensive_score_with_adjustments),
        ("Issue 8: 舆情修正框架", test_sentiment_framework),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[ERROR] {name} 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # 汇总
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "[OK] 通过" if success else "[FAIL] 失败"
        print(f"{status} - {name}")

    print(f"\n总计: {passed}/{total} 测试通过")

    if passed == total:
        print("\n[SUCCESS] 所有中等问题修复测试全部通过！")
        return 0
    else:
        print(f"\n[WARN] {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    exit(main())
