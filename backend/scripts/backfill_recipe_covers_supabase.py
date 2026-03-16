#!/usr/bin/env python3
"""
批量为 Supabase 中已有食谱重新生成封面图（使用最新「成品一致」生图逻辑）。

用法（在 backend 目录）:
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --dry-run
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --limit 5
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --refresh-all
"""
from __future__ import annotations

import argparse
import asyncio
import sys

sys.path.insert(0, ".")

from app.db.postgres import (
    get_recipes_from_postgres,
    init_postgres,
    update_recipe_image_url,
)
from app.services.recipe_cover import ensure_recipe_cover


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Backfill recipe cover images (Supabase, 成品一致生图)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="最多处理多少条（0 表示不限制）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要处理的记录，不落库",
    )
    parser.add_argument(
        "--refresh-all",
        action="store_true",
        help="全部食谱都重生成封面（默认只处理缺少 imageURL 的）",
    )
    args = parser.parse_args()

    await init_postgres()

    recipes = await get_recipes_from_postgres(None)
    if not recipes:
        print("Supabase 中暂无食谱，或未配置 SUPABASE_URL/SUPABASE_ANON_KEY。")
        return 1

    # 筛选：未传 --refresh-all 时只处理没有封面或封面为空的
    if not args.refresh_all:
        recipes = [
            r
            for r in recipes
            if not (r.get("imageURL") and str(r.get("imageURL", "")).strip())
        ]
    if not recipes:
        print("没有需要补图/重生成封面的食谱。")
        return 0

    if args.limit and args.limit > 0:
        recipes = recipes[: args.limit]

    print(f"待处理 {len(recipes)} 条食谱（dry-run={args.dry_run}）")
    success = 0
    failed = 0

    for recipe in recipes:
        rid = recipe.get("id", "")
        title = (recipe.get("title") or "").strip()
        if not title:
            print(f"- 跳过 {rid}: 缺少 title")
            failed += 1
            continue

        if args.dry_run:
            print(f"- [dry-run] 将处理 {rid}: {title}")
            success += 1
            continue

        # 生图会用 recipe 的 steps 推断成品形态，保证与步骤一致
        new_url = ensure_recipe_cover(recipe)
        if not new_url:
            print(f"- 失败 {rid}: {title}（生图失败或未返回 URL）")
            failed += 1
            continue

        ok = update_recipe_image_url(rid, new_url)
        if not ok:
            print(f"- 失败 {rid}: {title}（更新 Supabase 失败）")
            failed += 1
            continue

        print(f"- 成功 {rid}: {title}")
        success += 1

    print(f"完成：success={success}, failed={failed}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
