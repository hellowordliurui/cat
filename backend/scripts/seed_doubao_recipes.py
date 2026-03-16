#!/usr/bin/env python3
"""
根据既有入库流程批量写入食谱：
1. 安全审计
2. 豆包生成制作步骤
3. 豆包生成封面图
4. 写入 Supabase recipes 表

运行方式：
cd backend && ./.venv/bin/python -m scripts.seed_doubao_recipes
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
        "title": "落日三文鱼舒芙蕾",
        "subtitle": "像晚霞一样柔软蓬松的三文鱼小点心，适合猫咪的轻盈一餐。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约 60g，去刺蒸熟"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "熟蛋黄", "amount": "半个"},
        ],
        "steps": [],
        "aiBreedNote": "三文鱼脂香足，适口性高；体重控制中的猫咪建议分次少量喂食。",
        "safetyPassed": True,
    },
    {
        "title": "云朵奶香鸡肉泥",
        "subtitle": "绵密顺滑的鸡肉奶香泥，入口像云朵一样轻柔。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 70g，蒸熟撕碎"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "鸡肉高蛋白、负担轻，适合作为日常辅食；首次尝试奶香配方可先从小份开始。",
        "safetyPassed": True,
    },
    {
        "title": "初雪兔肉慕斯",
        "subtitle": "清淡细腻的兔肉慕斯，像初雪一样轻盈安静。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "兔腿肉", "amount": "约 60g，蒸熟去筋膜"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "兔肉相对清爽，适合想换口味的猫咪；肠胃敏感时建议减量试吃。",
        "safetyPassed": True,
    },
    {
        "title": "樱花虾色三文鱼浓汤",
        "subtitle": "带着柔粉海味的暖心浓汤，颜色像樱花映上海面。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约 50g，去刺蒸熟"},
            {"name": "熟虾仁", "amount": "约 10g，切碎"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "虾仁只作少量提鲜，若猫咪首次接触甲壳类食材，请观察是否有不耐受反应。",
        "safetyPassed": True,
    },
    {
        "title": "海洋之息蓝莓鳕鱼泥",
        "subtitle": "清新海味里点缀一丝果香，颜色层次像海风拂过的清晨。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鳕鱼", "amount": "约 60g，蒸熟去刺"},
            {"name": "蓝莓", "amount": "2 颗，压碎去皮"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "蓝莓仅作少量点缀提香，不宜过量；鳕鱼细嫩，适合作为换口味的小份辅食。",
        "safetyPassed": True,
    },
    {
        "title": "和风鸭肉燕麦塔",
        "subtitle": "带着温和谷香的鸭肉小塔，口感扎实却依旧细腻。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸭胸肉", "amount": "约 60g，蒸熟切碎"},
            {"name": "燕麦", "amount": "约 10g，煮软压细"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "鸭肉风味浓郁，适口性较高；首次添加燕麦时建议少量尝试，观察排便状态。",
        "safetyPassed": True,
    },
    {
        "title": "芝士鸡肉肉肉甜甜圈",
        "subtitle": "肉感十足的小甜甜圈造型点心，带有轻柔奶香与鸡肉鲜味。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 70g，蒸熟撕碎"},
            {"name": "羊奶粉", "amount": "1.5 小勺"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "熟蛋黄", "amount": "半个"},
        ],
        "steps": [],
        "aiBreedNote": "这道配方以鸡肉为主、奶香为辅，适合作为高适口性加餐；若猫咪对乳制品敏感，可减少奶粉比例。",
        "safetyPassed": True,
    },
    {
        "title": "元气三文鱼波奇饭",
        "subtitle": "像小小能量饭碗一样丰富柔和，适合作为猫咪的元气加餐。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "三文鱼", "amount": "约 60g，去刺蒸熟"},
            {"name": "南瓜", "amount": "约 20g，蒸熟切小丁"},
            {"name": "西兰花", "amount": "少量，焯熟切碎"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "三文鱼与少量蔬菜组合更有层次，适合作为视觉感更强的辅食；西兰花请控制在点缀量。",
        "safetyPassed": True,
    },
    {
        "title": "缤纷海陆千层派",
        "subtitle": "海味与肉香层层叠叠，像节日小派一样精致饱满。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 40g，蒸熟撕碎"},
            {"name": "鳕鱼", "amount": "约 40g，蒸熟去刺"},
            {"name": "南瓜", "amount": "约 20g，蒸熟压泥"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "海陆双拼能提升适口性，但初次尝试多种蛋白时建议控制份量，避免一次摄入过杂。",
        "safetyPassed": True,
    },
    {
        "title": "森林风鹿肉泥泥杯",
        "subtitle": "鹿肉香气清冽，盛在小杯中像森林系的安静小甜品。",
        "category": "mousse",
        "imageURL": None,
        "ingredients": [
            {"name": "鹿肉", "amount": "约 60g，蒸熟切碎"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "蓝莓", "amount": "1~2 颗，压碎点缀"},
        ],
        "steps": [],
        "aiBreedNote": "鹿肉属于相对少见的蛋白来源，换口味时更有新鲜感；敏感体质猫咪建议先少量试吃。",
        "safetyPassed": True,
    },
    {
        "title": "南瓜鸡肉小奶砖",
        "subtitle": "带着南瓜暖意与奶香的鸡肉小方砖，口感柔软又扎实。",
        "category": "cake",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 70g，蒸熟撕碎"},
            {"name": "南瓜", "amount": "约 25g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "山药", "amount": "约 15g，蒸熟压泥"},
        ],
        "steps": [],
        "aiBreedNote": "鸡肉与南瓜搭配温和易接受，适合作为日常辅食；若猫咪肠胃偏敏感，可先从小份尝试。",
        "safetyPassed": True,
    },
    {
        "title": "清凉椰子鸡肉冻",
        "subtitle": "像夏日小点心一样清爽的鸡肉冻，口感轻盈、视觉清透。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "鸡胸肉", "amount": "约 60g，蒸熟切碎"},
            {"name": "椰子水", "amount": "少量，用于调和口感"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
        ],
        "steps": [],
        "aiBreedNote": "椰子元素仅作风味点缀，建议控制比例，第一次尝试时注意观察猫咪肠胃反应。",
        "safetyPassed": True,
    },
    {
        "title": "深海金枪鱼冰激凌",
        "subtitle": "灵感来自冰激凌造型的金枪鱼小点，带着海洋风味与趣味感。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "金枪鱼", "amount": "约 60g，蒸熟压碎"},
            {"name": "山药", "amount": "约 20g，蒸熟压泥"},
            {"name": "羊奶粉", "amount": "1 小勺"},
            {"name": "南瓜", "amount": "约 10g，蒸熟作点缀"},
        ],
        "steps": [],
        "aiBreedNote": "金枪鱼风味鲜明，适口性通常较高；建议控制食用频次，避免长期单一鱼类蛋白摄入。",
        "safetyPassed": True,
    },
    {
        "title": "红豆沙色鸭肉羊奶冻",
        "subtitle": "色调温柔像红豆沙奶冻，鸭肉香气与奶香交织得很柔和。",
        "category": "cold",
        "imageURL": None,
        "ingredients": [
            {"name": "鸭胸肉", "amount": "约 60g，蒸熟切碎"},
            {"name": "羊奶粉", "amount": "1.5 小勺"},
            {"name": "南瓜", "amount": "约 15g，蒸熟压泥"},
            {"name": "甜菜根", "amount": "极少量，蒸熟取色点缀"},
        ],
        "steps": [],
        "aiBreedNote": "这道配方以鸭肉和奶香为主，颜色灵感食用量应控制在点缀级别，避免一次摄入过多辅助食材。",
        "safetyPassed": True,
    },
]


async def ingest_one(base_recipe: dict) -> tuple[bool, str]:
    recipe = copy.deepcopy(base_recipe)
    title = recipe["title"]

    passed, audited = audit_recipe(recipe)
    if not passed:
        return False, f"{title}: 审计未通过，已跳过"

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
