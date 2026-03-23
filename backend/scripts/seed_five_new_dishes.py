#!/usr/bin/env python3
"""
将 5 道新菜品按入库流程批量入库（不与现有菜品重复）：
1. 安全审计（禁忌食材检测）
2. 豆包生成制作步骤
3. 豆包生成封面图
4. 写入 Supabase recipes 表

运行方式：
cd backend && ./.venv/bin/python -m scripts.seed_five_new_dishes
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


# 5 道新菜品，title 与 seed_new_dishes / seed_four_dishes / seed_five_dishes 中已有菜品均不重复
RECIPE_BLUEPRINTS = [
    {
        "title": "碧波青瓜鸡丝卷",
        "subtitle": "鸡丝与青瓜的清爽小卷，像碧波一样清新适口。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 50g，蒸熟撕丝"},
            {"name": "黄瓜", "amount": "约 20g，去皮去籽切丝"},
            {"name": "南瓜", "amount": "约 15g，蒸熟压泥作粘合"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "黄瓜仅少量点缀补水，不宜多；卷状造型方便手持喂食。",
        "safetyPassed": True,
    },
    {
        "title": "暖阳胡萝卜牛肉泥",
        "subtitle": "牛肉与胡萝卜的绵密肉泥，像暖阳一样温和饱腹。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "牛肉", "amount": "约 60g，蒸熟剁泥"},
            {"name": "胡萝卜", "amount": "约 25g，蒸熟压泥"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "胡萝卜有益毛色与视力，与牛肉搭配适口性好；泥状易消化。",
        "safetyPassed": True,
    },
    {
        "title": "星空鳕鱼南瓜盅",
        "subtitle": "鳕鱼与南瓜装在小盅里，像星空下的温柔一餐。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鳕鱼", "amount": "约 55g，蒸熟去刺压碎"},
            {"name": "南瓜", "amount": "约 30g，蒸熟压泥"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "鳕鱼细嫩低敏，南瓜增甜增稠；盅装份量可控，适合分餐。",
        "safetyPassed": True,
    },
    {
        "title": "森林鸡茸山药球",
        "subtitle": "鸡肉与山药捏成的小球，像森林里的小团子。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 65g，蒸熟剁茸"},
            {"name": "山药", "amount": "约 28g，蒸熟压泥"},
            {"name": "熟蛋黄", "amount": "半个"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "山药助成型，小球方便控制单次食量；可一次多做冷藏分次回温。",
        "safetyPassed": True,
    },
    {
        "title": "金汤三文鱼南瓜羹",
        "subtitle": "三文鱼与南瓜熬成的金汤羹，色泽暖黄、口感顺滑。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约 55g，去刺蒸熟碾碎"},
            {"name": "南瓜", "amount": "约 30g，蒸熟压泥"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "三文鱼 Omega 与南瓜搭配亮毛又暖胃；羹状适合不爱嚼的猫咪。",
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
