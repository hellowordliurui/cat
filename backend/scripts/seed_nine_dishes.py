#!/usr/bin/env python3
"""
将以下 9 道菜品按入库流程入库：
嘎嘣脆鸡肉干、酥脆三文鱼皮卷、芝士碎碎鸡肉粒、亚麻籽油拌鸭肉丝、海带芽鸡肉暖汤、
鲜美淡菜牛肉汤、嫩煮蛋羹鸡肉杯、温润山药鸭肉糊、蓝莓鸭肝补铁泥。

运行：cd backend && ./.venv/bin/python -m scripts.seed_nine_dishes
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
        "title": "嘎嘣脆鸡肉干",
        "subtitle": "低温烘干的鸡胸薄片，脆香适口，适合当作少量奖励小食。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 80g，切薄片"},
        ],
        "steps": [],
        "aiBreedNote": "无盐无糖低温烘干；脂肪敏感或肥胖猫咪应极少给予，当作偶尔奖励即可。",
        "safetyPassed": True,
    },
    {
        "title": "酥脆三文鱼皮卷",
        "subtitle": "烤至酥脆的三文鱼皮小卷，脂香足、口感轻脆，少量即可。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼皮", "amount": "适量，洗净沥干"},
            {"name": "南瓜", "amount": "约 15g，蒸熟压泥（作少量粘合）"},
        ],
        "steps": [],
        "aiBreedNote": "鱼皮脂肪较高，不宜天天吃；务必烤透，去净刺与硬鳞后再喂。",
        "safetyPassed": True,
    },
    {
        "title": "芝士碎碎鸡肉粒",
        "subtitle": "鸡肉粒搭配羊奶酪碎，咸香感来自奶香而非调味，适口性佳。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 60g，蒸熟切小粒"},
            {"name": "羊奶酪", "amount": "约 5g，切碎"},
            {"name": "南瓜", "amount": "约 15g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "乳糖不耐猫咪可能软便，奶酪仅作点缀；首次尝试请极小份量观察。",
        "safetyPassed": True,
    },
    {
        "title": "亚麻籽油拌鸭肉丝",
        "subtitle": "嫩滑鸭胸撕丝，淋少许亚麻籽油拌匀，凉拌风补水脂餐。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "鸭胸肉", "amount": "约 55g，蒸熟撕丝"},
            {"name": "亚麻籽油", "amount": "2～3 滴"},
            {"name": "胡萝卜", "amount": "约 15g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "亚麻籽油少量即可；油类不宜多，拌好后放至室温再给猫咪。",
        "safetyPassed": True,
    },
    {
        "title": "海带芽鸡肉暖汤",
        "subtitle": "海带芽与鸡肉煮的暖胃清汤，少纤维软烂，适合补水。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 50g，蒸熟撕丝"},
            {"name": "海带芽", "amount": "极少量，泡软切碎"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "海藻碘含量高，仅极少量点缀；甲状腺问题猫咪慎用，请咨询兽医。",
        "safetyPassed": True,
    },
    {
        "title": "鲜美淡菜牛肉汤",
        "subtitle": "淡菜与牛肉煮的鲜味清汤，无盐无调味，暖胃补水。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "牛肉", "amount": "约 45g，蒸熟切小丁"},
            {"name": "淡菜", "amount": "1～2 颗，煮熟取肉切碎"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "贝类首次尝试须极少份量观察过敏；不宜频繁，与其他蛋白轮换更佳。",
        "safetyPassed": True,
    },
    {
        "title": "嫩煮蛋羹鸡肉杯",
        "subtitle": "蒸蛋羹托底铺上鸡丝，嫩滑双口感的一小杯温柔餐。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡蛋", "amount": "1 个，取蛋液"},
            {"name": "鸡胸肉", "amount": "约 35g，蒸熟撕丝"},
            {"name": "羊奶粉", "amount": "1 小勺，用温水平开"},
        ],
        "steps": [],
        "aiBreedNote": "蛋黄蛋白同食需熟透；蛋不宜过量，建议与其他辅食轮换。",
        "safetyPassed": True,
    },
    {
        "title": "温润山药鸭肉糊",
        "subtitle": "山药与鸭肉打成的温润糊，对肠胃友好、易舔食。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸭胸肉", "amount": "约 55g，蒸熟"},
            {"name": "山药", "amount": "约 35g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "鸭肉性凉，体质偏寒的猫咪可减量或搭配南瓜；糊类放凉至室温再喂。",
        "safetyPassed": True,
    },
    {
        "title": "蓝莓鸭肝补铁泥",
        "subtitle": "鸭肝与蓝莓、山药打成细腻泥，铁与维生素的小份补充。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸭肝", "amount": "约 15g，蒸熟"},
            {"name": "蓝莓", "amount": "2～3 颗，压碎"},
            {"name": "山药", "amount": "约 25g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "肝脏维生素 A 高，每周少量即可；蓝莓仅作点缀，不宜多。",
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
