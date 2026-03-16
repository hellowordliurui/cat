"""健康检查"""
from fastapi import APIRouter

router = APIRouter()


@router.get("")
def health():
    return {"status": "ok", "service": "MoeChef API"}
