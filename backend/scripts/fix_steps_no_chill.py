#!/usr/bin/env python3
"""
批量修正库中食谱步骤：不需要冷藏定型的菜品（羹/汤/糊/碗等），若当前步骤里含「冷藏」或「定型」，
则用新规则重新生成步骤并写回数据库；需要冷藏定型的（蛋糕/慕斯/冷饮）保留不动。

运行方式：
  cd backend && ./.venv/bin/python -m scripts.fix_steps_no_chill           # 执行更新
  cd backend && ./.venv/bin/python -m scripts.fix_steps_no_chill --dry-run # 仅预览
"""
from __future__ import annotations

import argparse
import asyncio
import sys

sys.path.insert(0, ".")

from app.db.postgres import get_recipes_from_postgres, update_recipe_steps
from app.services.recipe_steps import ensure_recipe_steps

# 需要保留「冷藏定型」的品类（步骤不改）
NEED_CHILL_CATEGORIES = {"cake", "mousse", "cold"}


def _steps_contain_chill(steps: list) -> bool:
    if not steps:
        return False
    return any("冷藏" in str(s) or "定型" in str(s) for s in steps)


async def main() -> None:
    parser = argparse.ArgumentParser(description="修正不需要冷藏定型的食谱步骤")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要修改的食谱，不写库")
    args = parser.parse_args()

    recipes = await get_recipes_from_postgres(None)
    if not recipes:
        print("未获取到任何食谱，请检查 Supabase 配置与 recipes 表。")
        return

    to_fix = []
    for r in recipes:
        cat = (r.get("category") or "").strip().lower()
        if cat in NEED_CHILL_CATEGORIES:
            continue
        steps = r.get("steps") or []
        if not _steps_contain_chill(steps):
            continue
        to_fix.append(r)

    if not to_fix:
        print("没有需要修改的食谱（非蛋糕/慕斯/冷饮且步骤含冷藏或定型的条目为 0）。")
        return

    print(f"共 {len(to_fix)} 条食谱需要修正步骤（去掉不必要的冷藏定型）：")
    for r in to_fix:
        print(f"  - [{r.get('category')}] {r.get('title')} (id={r.get('id')})")
    if args.dry_run:
        print("\n[--dry-run] 未写入数据库。去掉 --dry-run 将执行更新。")
        return

    print()
    updated = 0
    for r in to_fix:
        title = r.get("title", "")
        # 清空步骤以触发「重新生成」
        r["steps"] = []
        new_steps = ensure_recipe_steps(r)
        if new_steps and update_recipe_steps(r["id"], new_steps):
            updated += 1
            print(f"已更新: {title}")
            for i, s in enumerate(new_steps, 1):
                print(f"    {i}. {s}")
        else:
            print(f"跳过（生成或写入失败）: {title}")
    print(f"\n完成，共更新 {updated}/{len(to_fix)} 条。")


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)
