#!/usr/bin/env python3
"""
将以下 5 道菜品按入库流程入库：
克莱因蓝鳕鱼慕斯、惠灵顿嫩牛肉排、香榭丽舍三文鱼塔、勃艮第风味红肉烩、白松露风味鸡丝浓汤。
运行：cd backend && ./.venv/bin/python -m scripts.seed_five_dishes
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
        "title": "克莱因蓝鳕鱼慕斯",
        "subtitle": "鳕鱼与蓝莓的慕斯，一抹克莱因蓝，清新又温柔。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鳕鱼", "amount": "约 60g，蒸熟去刺"},
            {"name": "蓝莓", "amount": "3～4 颗，压碎去皮"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "蓝莓仅作天然色与点缀，鳕鱼细嫩易消化；慕斯质地适合夏季。",
        "safetyPassed": True,
    },
    {
        "title": "惠灵顿嫩牛肉排",
        "subtitle": "嫩牛肉与南瓜、山药做成的小排造型，外酥里嫩感。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "牛肉", "amount": "约 65g，蒸熟切碎"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "猫咪版惠灵顿无酥皮与调味，以肉与南瓜山药为主，适口性好。",
        "safetyPassed": True,
    },
    {
        "title": "香榭丽舍三文鱼塔",
        "subtitle": "三文鱼与南瓜叠成的小塔，像香榭丽舍的精致小点。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约 60g，去刺蒸熟"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "三文鱼与南瓜分层口感丰富，塔形适合分餐；注意控制鱼类频次。",
        "safetyPassed": True,
    },
    {
        "title": "勃艮第风味红肉烩",
        "subtitle": "牛肉与胡萝卜、南瓜的温柔烩煮，无酒精版红肉风味。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "牛肉", "amount": "约 60g，蒸熟切小块"},
            {"name": "胡萝卜", "amount": "约 20g，蒸熟压泥"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "猫咪版勃艮第无红酒与洋葱，以红肉与蔬菜为主，烩煮质地易入口。",
        "safetyPassed": True,
    },
    {
        "title": "白松露风味鸡丝浓汤",
        "subtitle": "鸡丝与山药熬成的浓汤，淡淡奶香像白松露般细腻。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 60g，蒸熟撕丝"},
            {"name": "山药", "amount": "约 25g，蒸熟压泥"},
            {"name": "南瓜", "amount": "约 15g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "无真实松露与调味，以鸡丝与羊奶香营造浓郁口感，适合秋冬暖胃。",
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
