#!/usr/bin/env python3
"""把草莓蛋糕写入 MongoDB（通过审计后入库）。在 backend 目录执行：python -m scripts.seed_strawberry_cake"""
import sys

sys.path.insert(0, ".")

from app.services.ingestion_guard import audit_recipe
from app.db.mongo import insert_recipe

RECIPE = {
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
}


def main():
    passed, recipe = audit_recipe(RECIPE)
    if not passed:
        print("审计未通过：含禁忌食材，未入库")
        return 1
    rid = insert_recipe(recipe)
    if rid:
        print(f"草莓蛋糕已入库，id: {rid}")
    else:
        print("未配置 MongoDB，未写入数据库；列表接口会从 mock 返回草莓蛋糕。")
    return 0


if __name__ == "__main__":
    exit(main())
