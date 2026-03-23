#!/usr/bin/env python3
"""
批量为 Supabase 中已有食谱重新生成封面图（使用最新「成品一致」生图逻辑）。

用法（在 backend 目录）:
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --dry-run
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --limit 5
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --refresh-all
  ./.venv/bin/python -m scripts.backfill_recipe_covers_supabase --refresh-all --title "白松露风味鸡丝浓汤"
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import time

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
    parser.add_argument(
        "--title",
        type=str,
        default="",
        help="只处理标题包含该字符串的食谱，如 --title \"白松露\"；需配合 --refresh-all 使用",
    )
    args = parser.parse_args()

    await init_postgres()

    recipes = await get_recipes_from_postgres(None)
    if not recipes:
        print("Supabase 中暂无食谱，或未配置 SUPABASE_URL/SUPABASE_ANON_KEY。")
        return 1

    # 按标题筛选：--title 时只处理包含该关键词的食谱（可单独重生成某一道）
    if args.title and args.title.strip():
        title_key = args.title.strip()
        recipes = [r for r in recipes if title_key in (r.get("title") or "")]
        if not recipes:
            print(f"没有标题包含「{title_key}」的食谱。")
            return 0
        print(f"按标题筛选「{title_key}」，共 {len(recipes)} 条")
    else:
        # 未按标题筛选时：未传 --refresh-all 则只处理没有封面的
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

        # 追加 ?v=时间戳 破坏 App/CDN 缓存，使客户端拉取最新图
        sep = "&" if "?" in new_url else "?"
        url_with_cache_bust = f"{new_url}{sep}v={int(time.time())}"
        ok = update_recipe_image_url(rid, url_with_cache_bust)
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
