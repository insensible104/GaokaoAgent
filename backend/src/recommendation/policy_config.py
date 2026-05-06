"""Central policy thresholds for recommendation rules.

These values keep first-pass rule decisions explicit and easy to audit. They are
not learned weights; later evaluation should tune them with real cases.
"""

SMALL_QUOTA_MAX = 10
MEDIUM_QUOTA_MAX = 40

TAIL_RISK_SCORE_PENALTY_WEIGHT = 0.25
HIGH_TAIL_RISK_THRESHOLD = 0.55
LOW_ACCEPTABLE_MAJOR_RATIO = 0.50
MIN_ACCEPTABLE_FOR_ADJUSTMENT = 0.40
HIGH_UTILITY_DISPERSION = 0.45
MILD_UTILITY_DISPERSION = 0.25

DEFAULT_REPORT_TOP_N = 8

