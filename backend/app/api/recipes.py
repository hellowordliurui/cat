"""
食谱 API - PRD Phase 3：通过审计的食谱存 PostgreSQL（Supabase）
"""
from fastapi import APIRouter, HTTPException

from app.db.postgres import get_last_recipe_db_error, get_recipes_from_postgres, insert_recipe
from app.services.ingestion_guard import audit_recipe
from app.services.recipe_cover import ensure_recipe_cover
from app.services.recipe_steps import ensure_recipe_steps

router = APIRouter()

# 未配置 PostgreSQL 或库为空时的占位数据
MOCK_RECIPES = [
    {
        "id": "1",
        "title": "海风三文鱼慕斯 (护心版)",
        "subtitle": "一份充满大海味道的轻盈慕斯。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约手掌大小"},
            {"name": "羊奶粉", "amount": "1小勺"},
        ],
        "steps": [
            "将鱼肉蒸熟，与奶粉一同压成泥状。",
            "倒入猫爪模具，冷藏 2 小时。",
        ],
        "aiBreedNote": "针对其易胖体质，本配方已自动剔除原始数据中的[糖分]，建议额外添加鸭心。",
        "safetyPassed": True,
    },
    {
        "id": "2",
        "title": "草莓蛋糕",
        "subtitle": "猫咪可食的草莓风味小蛋糕，无糖无添加。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 50g"},
            {"name": "草莓", "amount": "2～3 颗（切碎）"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "南瓜", "amount": "一小块蒸熟"},
            {"name": "熟蛋黄", "amount": "半个"},
        ],
        "steps": [
            "鸡胸肉蒸熟撕丝，南瓜蒸熟压泥，草莓洗净去蒂切小粒。",
            "将肉丝、南瓜泥、羊奶粉、熟蛋黄混合拌匀，拌入草莓粒。",
            "填入模具压实，冷藏 1～2 小时后脱模即可。",
        ],
        "aiBreedNote": "草莓与鸡肉搭配适口性好，南瓜助消化；注意草莓仅作点缀，不宜过多。",
        "safetyPassed": True,
    },
    {
        "id": "3",
        "title": "芒果蛋糕",
        "subtitle": "猫咪可食的芒果风味小蛋糕，无糖无添加。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 50g"},
            {"name": "芒果", "amount": "一小块（约 20g，去核切丁）"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "南瓜", "amount": "一小块蒸熟"},
            {"name": "熟蛋黄", "amount": "半个"},
        ],
        "steps": [
            "鸡胸肉蒸熟撕丝，南瓜蒸熟压泥，芒果取肉切小丁。",
            "将肉丝、南瓜泥、羊奶粉、熟蛋黄混合拌匀，拌入芒果丁。",
            "填入模具压实，冷藏 1～2 小时后脱模即可。",
        ],
        "aiBreedNote": "芒果少量即可提香，与鸡肉搭配适口；注意芒果仅作点缀，不宜过多。",
        "safetyPassed": True,
    },
]


@router.get("")
async def list_recipes(category: str | None = None):
    """获取已审计食谱列表。数据库异常时直接报错，不再静默回退 mock。"""
    items = await get_recipes_from_postgres(category)
    db_error = get_last_recipe_db_error()
    if db_error:
        raise HTTPException(status_code=503, detail=f"recipes db unavailable: {db_error}")
    return {
        "items": items,
        "source": "postgres",
        "dbError": db_error,
    }


@router.post("")
async def create_recipe(raw: dict):
    """
    提交食谱：先审计，通过后写入 PostgreSQL（Supabase）。
    返回 201 及完整食谱（含 id，若入库成功）。
    """
    passed, recipe = audit_recipe(raw)
    if not passed:
        raise HTTPException(status_code=400, detail="食谱含禁忌食材，拒绝入库")
    recipe.pop("id", None)
    if not recipe.get("steps"):
        steps = ensure_recipe_steps(recipe)
        if not steps:
            raise HTTPException(status_code=503, detail="食谱步骤生成失败，请检查豆包文本模型配置")
    # 若无封面图则用豆包生图并保存到 /static/generated
    if not recipe.get("imageURL"):
        cover_url = ensure_recipe_cover(recipe)
        if not cover_url:
            raise HTTPException(status_code=503, detail="食谱图片生成失败，请检查豆包生图配置")
        recipe["imageURL"] = cover_url
    rid = await insert_recipe(recipe)
    if rid:
        recipe["id"] = rid
    recipe.setdefault("safetyPassed", True)
    return {"passed": True, "recipe": recipe}
