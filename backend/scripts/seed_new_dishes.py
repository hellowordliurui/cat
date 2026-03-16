#!/usr/bin/env python3
"""
将指定菜品按入库流程批量入库：
1. 安全审计（禁忌食材检测）
2. 豆包生成制作步骤
3. 豆包生成封面图
4. 写入 Supabase recipes 表

运行方式：
cd backend && ./.venv/bin/python -m scripts.seed_new_dishes
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
        "title": "翡翠猫草冷汤",
        "subtitle": "清新猫草与鸡肉的冷汤，像清晨露珠一样清爽。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "猫草", "amount": "一小把，洗净切碎"},
            {"name": "鸡胸肉", "amount": "约 50g，蒸熟撕丝"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "猫草助消化、化毛；冷汤形式适合夏季补水，注意不宜过凉。",
        "safetyPassed": True,
    },
    {
        "title": "原野鹿肉能量碗",
        "subtitle": "鹿肉与南瓜、山药的组合，像原野上的能量小碗。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鹿肉", "amount": "约 60g，蒸熟切碎"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "鹿肉蛋白优质、风味独特，适合换口味；首次尝试建议少量。",
        "safetyPassed": True,
    },
    {
        "title": "晨曦南瓜鸡肉羹",
        "subtitle": "南瓜与鸡肉的温柔羹汤，像晨曦一样暖胃。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 60g，蒸熟撕碎"},
            {"name": "南瓜", "amount": "约 30g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "南瓜鸡肉羹温和易消化，适合作为日常辅食或病后调理。",
        "safetyPassed": True,
    },
    {
        "title": "森林奇遇肉丸串",
        "subtitle": "鸡肉与山药做成的小肉丸，像森林里的小惊喜。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 70g，蒸熟剁泥"},
            {"name": "山药", "amount": "约 25g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "熟蛋黄", "amount": "半个"},
        ],
        "steps": [],
        "aiBreedNote": "肉丸形态增加趣味性，山药有助成型；可做成小串方便喂食。",
        "safetyPassed": True,
    },
    {
        "title": "露水清晨补水餐",
        "subtitle": "含水量充足的鸡肉与瓜类小食，适合清晨补水。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 50g，蒸熟撕丝"},
            {"name": "冬瓜", "amount": "约 30g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "黄瓜", "amount": "少量，去皮去籽切碎"},
        ],
        "steps": [],
        "aiBreedNote": "冬瓜、黄瓜含水量高，适合不爱喝水的猫咪；黄瓜仅作点缀，不宜多。",
        "safetyPassed": True,
    },
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
