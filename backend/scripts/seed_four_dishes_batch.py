#!/usr/bin/env python3
"""
将「鹌鹑蛋爆浆肉排、南瓜羊奶流沙浓汤、羊奶酪碎碎肉杯、黄金肉肉汉堡」按入库流程入库：
1. 安全审计 2. 豆包生成步骤 3. 豆包生成封面 4. 写入 Supabase

运行：cd backend && ./.venv/bin/python -m scripts.seed_four_dishes_batch
"""
from __future__ import annotations

import asyncio
import copy
import sys

sys.path.insert(0, ".")

from app.db.postgres import init_postgres, insert_recipe
from app.services.ingestion_guard import audit_recipe
from app.services.recipe_cover import ensure_recipe_cover
from app.services.recipe_steps import ensure_recipe_steps


RECIPE_BLUEPRINTS = [
    {
        "title": "鹌鹑蛋爆浆肉排",
        "subtitle": "鹌鹑蛋与肉排的爆浆口感，小小一颗营养满满。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 60g，蒸熟剁泥"},
            {"name": "鹌鹑蛋", "amount": "2～3 个，煮熟取蛋黄（蛋白可少量）"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "鹌鹑蛋营养密度高，与鸡肉搭配适口性好；注意熟透、少量为宜。",
        "safetyPassed": True,
    },
    {
        "title": "南瓜羊奶流沙浓汤",
        "subtitle": "南瓜与羊奶煮成流沙般浓汤，暖胃又顺滑。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "南瓜", "amount": "约 40g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "2 小勺，温水调开"},
            {"name": "鸡胸肉", "amount": "约 30g，蒸熟撕丝"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "南瓜羊奶浓汤温和易消化，流沙质地适合不爱嚼的猫咪；放至室温再喂。",
        "safetyPassed": True,
    },
    {
        "title": "羊奶酪碎碎肉杯",
        "subtitle": "羊奶酪与碎肉的杯状小食，像迷你甜品一样可爱。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 50g，蒸熟切碎"},
            {"name": "羊奶酪", "amount": "约 15g，无盐或低盐"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "羊奶酪部分猫咪可能乳糖敏感，首次少量试喂；无盐为佳。",
        "safetyPassed": True,
    },
    {
        "title": "黄金肉肉汉堡",
        "subtitle": "肉饼与南瓜的黄金小堡，一口一个元气满满。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 70g，蒸熟剁泥"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "熟蛋黄", "amount": "半个"},
        ],
        "steps": [],
        "aiBreedNote": "小堡造型方便控制份量，南瓜与蛋黄增色增香，适合作为加餐。",
        "safetyPassed": True,
    },
]


async def ingest_one(base_recipe: dict) -> tuple[bool, str]:
    recipe = copy.deepcopy(base_recipe)
    title = recipe["title"]

    passed, audited = audit_recipe(recipe)
    if not passed:
        return False, f"{title}: 审计未通过（含禁忌食材），已跳过"

    steps = ensure_recipe_steps(audited)
    if not steps:
        return False, f"{title}: 豆包步骤生成失败"

    cover_url = ensure_recipe_cover(audited)
    if not cover_url:
        return False, f"{title}: 豆包图片生成失败"
    audited["imageURL"] = cover_url

    rid = await insert_recipe(audited)
    if not rid:
        return False, f"{title}: 数据库写入失败"

    return True, f"{title}: 入库成功，id={rid}"


async def main() -> int:
    await init_postgres()

    success_count = 0
    for recipe in RECIPE_BLUEPRINTS:
        ok, message = await ingest_one(recipe)
        print(message)
        if ok:
            success_count += 1

    total = len(RECIPE_BLUEPRINTS)
    print(f"完成：{success_count}/{total}")
    return 0 if success_count == total else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
