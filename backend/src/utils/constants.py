"""项目常量定义

修复：消除重复代码，将常量集中管理
"""
from models.user_profile import SchoolMajorPreference, RiskTolerance


# 学校-专业偏好映射（用于用户输入解析）
PREFERENCE_MAP = {
    # 数字映射
    '1': SchoolMajorPreference.PRIORITIZE_SCHOOL,
    '2': SchoolMajorPreference.BALANCED,
    '3': SchoolMajorPreference.PRIORITIZE_MAJOR,

    # 中文映射
    '优先学校': SchoolMajorPreference.PRIORITIZE_SCHOOL,
    '学校优先': SchoolMajorPreference.PRIORITIZE_SCHOOL,
    '均衡': SchoolMajorPreference.BALANCED,
    '平衡': SchoolMajorPreference.BALANCED,
    '优先专业': SchoolMajorPreference.PRIORITIZE_MAJOR,
    '专业优先': SchoolMajorPreference.PRIORITIZE_MAJOR,

    # 英文映射
    'school': SchoolMajorPreference.PRIORITIZE_SCHOOL,
    'balanced': SchoolMajorPreference.BALANCED,
    'major': SchoolMajorPreference.PRIORITIZE_MAJOR,
}

# 风险偏好映射
RISK_TOLERANCE_MAP = {
    # 中文映射
    '保守': RiskTolerance.CONSERVATIVE,
    '稳健': RiskTolerance.BALANCED,
    '激进': RiskTolerance.AGGRESSIVE,
    '谨慎': RiskTolerance.CONSERVATIVE,
    '平衡': RiskTolerance.BALANCED,
    '进取': RiskTolerance.AGGRESSIVE,

    # 英文映射
    'conservative': RiskTolerance.CONSERVATIVE,
    'balanced': RiskTolerance.BALANCED,
    'aggressive': RiskTolerance.AGGRESSIVE,
}

# 选科组合规范化映射
SUBJECT_GROUP_MAP = {
    '物': '物理',
    '物理': '物理',
    'physics': '物理',
    '历': '历史',
    '历史': '历史',
    'history': '历史',
}

# API配置
DEFAULT_API_PORT = 8000
DEFAULT_API_HOST = "127.0.0.1"
DEFAULT_RATE_LIMIT = 10  # 每分钟请求数

# 数据路径
DEFAULT_DATA_DIR = "data"

# 缓存配置
CACHE_SIZE = 1000  # LRU缓存大小
CACHE_TTL = 3600  # 缓存过期时间（秒）

# 录取概率阈值
PROB_RUSH_THRESHOLD = 0.6    # 冲刺概率阈值（<60%为冲）
PROB_TARGET_THRESHOLD = 0.9  # 稳妥概率阈值（60-90%为稳）
# >=90%为保

# 推荐数量配置
RECOMMENDED_COUNT = 30       # 总推荐数
RECOMMENDED_RUSH = 10        # 冲刺推荐数
RECOMMENDED_TARGET = 10      # 稳妥推荐数
RECOMMENDED_SAFE = 10        # 保底推荐数

# 蒙特卡洛模拟配置
MONTE_CARLO_SAMPLES = 10000  # 采样次数
MIN_HISTORICAL_YEARS = 2     # 最少历史数据年数

# 分数范围
MIN_SCORE = 0
MAX_SCORE = 900
MIN_RANK = 1
MAX_RANK = 1000000

# 科目分数范围
SUBJECT_SCORE_RANGES = {
    'chinese': (0, 150),
    'math': (0, 150),
    'english': (0, 150),
    'physics': (0, 100),
    'chemistry': (0, 100),
    'biology': (0, 100),
    'politics': (0, 100),
    'history': (0, 100),
    'geography': (0, 100),
}
