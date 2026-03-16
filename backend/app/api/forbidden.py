"""
禁忌清单 API - PRD 3.2 从 PostgreSQL 冷启动加载到内存，本接口返回内存缓存
"""
from fastapi import APIRouter

from app.db.postgres import get_forbidden_list

router = APIRouter()


@router.get("")
def list_forbidden():
    """获取禁忌清单（启动时自 PostgreSQL 加载，内存返回）"""
    return {"items": get_forbidden_list()}
