#!/usr/bin/env python3
"""
将以下 4 道菜品按入库流程入库：牛气冲天补膘堡、深海红钻亮毛餐、黄金铠甲蛋黄餐、大力士牛肉塔塔。
运行：cd backend && ./.venv/bin/python -m scripts.seed_four_dishes
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
        "title": "牛气冲天补膘堡",
        "subtitle": "牛肉与南瓜做成的小堡造型，营养扎实、元气满满。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "牛肉", "amount": "约 60g，蒸熟切碎"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "牛肉高蛋白适合增膘期；做成小堡造型适口性好，注意控制单次份量。",
        "safetyPassed": True,
    },
    {
        "title": "深海红钻亮毛餐",
        "subtitle": "三文鱼与胡萝卜的搭配，像深海红钻一样亮泽毛发。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约 60g，去刺蒸熟"},
            {"name": "胡萝卜", "amount": "约 20g，蒸熟压泥"},
            {"name": "南瓜", "amount": "约 15g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "三文鱼 Omega 与胡萝卜有益毛色；适量即可，不宜长期单一摄入。",
        "safetyPassed": True,
    },
    {
        "title": "黄金铠甲蛋黄餐",
        "subtitle": "蛋黄与鸡肉、南瓜的黄金组合，像小铠甲一样营养满满。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "熟蛋黄", "amount": "1 个"},
            {"name": "鸡胸肉", "amount": "约 50g，蒸熟撕碎"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "蛋黄卵磷脂与南瓜搭配温和；蛋黄不宜过量，建议每周 2～3 次为佳。",
        "safetyPassed": True,
    },
    {
        "title": "大力士牛肉塔塔",
        "subtitle": "牛肉与山药的塔塔造型，口感扎实、力量感十足。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "牛肉", "amount": "约 70g，蒸熟剁碎"},
            {"name": "山药", "amount": "约 25g，蒸熟压泥"},
            {"name": "熟蛋黄", "amount": "半个"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "牛肉高蛋白适合需要增肌的猫咪；塔塔形态方便分餐，注意熟透无生肉。",
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
