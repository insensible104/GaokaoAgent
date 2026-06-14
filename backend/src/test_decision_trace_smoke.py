"""Smoke tests for student-facing recommendation decision traces."""

from types import SimpleNamespace

from recommendation.decision_trace import build_decision_trace


row = SimpleNamespace(
    tradeoff_breakdown={
        "school_value": 0.82,
        "major_value": 0.91,
        "city_value": 0.65,
        "tail_risk_penalty": 0.12,
        "crowding_penalty": 0.04,
        "blacklist_penalty": 0.18,
        "quant_score": 0.73,
        "data_confidence_score": 0.42,
    },
    quant_evidence=["位次缓冲 +1200 名", "历史跨度约 800 名"],
    risk_reasons=["组内包含用户明确排斥的专业"],
    audit_flags=["blacklist_major_in_group"],
    is_blacklist_risk=True,
    worst_case_major="土木工程",
)

trace = build_decision_trace(row)

assert trace["verdict"] == "recommended_with_caution"
assert trace["confidence_level"] == "low"
assert trace["supporting_factors"][0]["code"] == "major_value"
assert any(item["code"] == "blacklist_penalty" for item in trace["risk_factors"])
assert any("土木工程" in item for item in trace["warnings"])
assert all(item["status"] == "passed" for item in trace["eligibility_checks"])

print("decision trace smoke tests passed")
