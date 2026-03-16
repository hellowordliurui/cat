"""
PRD Phase 2：AI 审计接口，入库即检测。
PRD 3.3：Gemini 1.5 Flash 入库审计 + 美学润色（当前为静态过滤，可扩展）。
"""
from fastapi import APIRouter, HTTPException

from app.services.ingestion_guard import audit_recipe

router = APIRouter()


@router.post("")
def audit_recipe_endpoint(raw: dict):
    """
    提交待入库食谱，执行审计。
    返回 { "passed": bool, "recipe": dict }，不通过则 400。
    """
    passed, result = audit_recipe(raw)
    if not passed:
        raise HTTPException(status_code=400, detail="食谱含禁忌食材，拒绝入库")
    return {"passed": True, "recipe": result}
