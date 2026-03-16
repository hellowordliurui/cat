"""
PRD 3.3 AI 引擎：Gemini 1.5 Flash
- 入库审计 (Ingestion Guard)：检测危险食材，不安全则拒绝入库
- 美学润色：将食材步骤重构为「温馨治愈」描述
PRD 3.2：实时拦截在内存 set 中匹配（冷启动从 PostgreSQL 加载），无 Redis。
"""
from __future__ import annotations

from typing import Any

# 使用启动时从 PostgreSQL 加载的内存 set（≈0 延迟）
def _get_forbidden_set() -> set[str]:
    from app.db.postgres import forbidden_words_set
    return forbidden_words_set


def static_filter(ingredients: list[str], forbidden_words: set[str] | None = None) -> bool:
    """静态过滤：任一食材命中禁忌词则返回 False（不通过）。默认用内存 set。"""
    words = forbidden_words if forbidden_words is not None else _get_forbidden_set()
    lower_ing = [s.lower() for s in ingredients]
    for w in words:
        if any(w in i for i in lower_ing):
            return False
    return True


def audit_recipe(raw: dict) -> tuple[bool, dict]:
    """
    对爬取/录入的食谱做审计。
    返回 (是否通过, 审计后食谱)。不通过则拒绝入库。
    PRD 3.3：Gemini 1.5 Flash 语义审计 + 美学润色（可选接入）。
    """
    raw_ing = raw.get("ingredients", [])
    if raw_ing and isinstance(raw_ing[0], dict):
        ingredients = [x.get("name", "") for x in raw_ing]
    else:
        ingredients = [str(x) for x in raw_ing]
    if not static_filter(ingredients):
        return False, raw
    # TODO: 调用 Gemini 1.5 Flash 做语义审计与治愈系重写
    return True, raw
