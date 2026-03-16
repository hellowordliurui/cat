#!/usr/bin/env python3
"""把芒果蛋糕写入 MongoDB（通过审计后入库）。在 backend 目录执行：python -m scripts.seed_mango_cake"""
import sys

sys.path.insert(0, ".")

from app.services.ingestion_guard import audit_recipe
from app.db.mongo import insert_recipe
from app.services.recipe_cover import ensure_recipe_cover

RECIPE = {
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
}


def main():
    passed, recipe = audit_recipe(RECIPE)
    if not passed:
        print("审计未通过：含禁忌食材，未入库")
        return 1
    # 用豆包生成封面图并保存到 static/generated
    cover_url = ensure_recipe_cover(recipe)
    if cover_url:
        recipe["imageURL"] = cover_url
        print(f"已生成封面图: {cover_url}")
    else:
        print("未配置豆包 Key 或生图失败，未设置封面图")
    rid = insert_recipe(recipe)
    if rid:
        print(f"芒果蛋糕已入库，id: {rid}")
    else:
        print("未配置 MongoDB，未写入数据库；列表接口会从 mock 返回芒果蛋糕。")
    return 0


if __name__ == "__main__":
    exit(main())
