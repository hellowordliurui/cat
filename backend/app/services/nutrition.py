"""
PRD 3.4 科学计算逻辑 - 辅食热量约束，作为 AI 建议的约束
RER = 70 * (body_weight ** 0.75)
DER_snack = RER * 10%（下午茶不超过每日总需求 10%）
"""


def rer_kcal_per_day(body_weight_kg: float) -> float:
    """静息能量需求 (Resting Energy Requirement)，单位 kcal/天"""
    return 70.0 * (body_weight_kg ** 0.75)


def der_snack_kcal(rer: float, fraction: float = 0.10) -> float:
    """下午茶/辅食热量上限 (DER_snack)，默认 RER 的 10%"""
    return rer * fraction
