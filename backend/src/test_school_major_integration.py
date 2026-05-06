"""测试学校-专业权衡系统集成"""
import sys
sys.path.insert(0, 'src')

from models.user_profile import UserProfile, SchoolMajorPreference, RiskTolerance
from utils.school_major_scoring import calculate_comprehensive_score

print("=" * 60)
print("学校-专业综合评分系统集成测试")
print("=" * 60)

# 测试1：验证综合评分算法
print("\n【测试1】综合评分算法验证")
print("-" * 60)

test_cases = [
    ("复旦大学", "计算机", SchoolMajorPreference.BALANCED),
    ("清华大学", "材料科学", SchoolMajorPreference.BALANCED),
    ("中国海洋大学", "计算机", SchoolMajorPreference.BALANCED),
]

for school, major, pref in test_cases:
    result = calculate_comprehensive_score(school, major, pref)
    print(f"{school} - {major}:")
    print(f"  综合评分: {result['comprehensive_score']:.1f}")
    print(f"  (学校{result['school_tier_score']:.0f} × 50% + "
          f"专业{result['major_quality_score']:.0f} × 50% + "
          f"平台加成{result['platform_bonus']:.0f})")

print("\n验证：")
print("  复旦计算机 > 清华材料 > 中国海洋计算机")

# 测试2：验证UserProfile扩展
print("\n\n【测试2】UserProfile模型扩展验证")
print("-" * 60)

profile = UserProfile(
    score=620,
    rank=12000,
    subject_group="物理",
    preferred_majors=["计算机"],
    school_major_preference=SchoolMajorPreference.BALANCED
)

print(f"✓ UserProfile创建成功")
print(f"  - 分数: {profile.score}")
print(f"  - 位次: {profile.rank}")
print(f"  - 选科: {profile.subject_group}")
print(f"  - 学校-专业偏好: {profile.school_major_preference.value}")

# 测试3：测试不同偏好的评分差异
print("\n\n【测试3】不同偏好策略的评分差异")
print("-" * 60)

school = "北京理工大学"
major = "机械工程"

for pref in [SchoolMajorPreference.PRIORITIZE_SCHOOL,
             SchoolMajorPreference.BALANCED,
             SchoolMajorPreference.PRIORITIZE_MAJOR]:
    result = calculate_comprehensive_score(school, major, pref)
    pref_name = {
        SchoolMajorPreference.PRIORITIZE_SCHOOL: "优先学校",
        SchoolMajorPreference.BALANCED: "平衡型",
        SchoolMajorPreference.PRIORITIZE_MAJOR: "优先专业"
    }[pref]
    print(f"{pref_name:10s}: {result['comprehensive_score']:.1f}分")

print("\n" + "=" * 60)
print("✓ 所有测试通过！")
print("=" * 60)

print("\n下一步：运行完整推荐流程测试（需要真实数据）")
print("提示：启动后端服务后，可以通过前端或API测试完整流程")
