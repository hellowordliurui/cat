#!/usr/bin/env python3
"""
批量为 MongoDB 中缺少 imageURL 的食谱补封面图。

用法（在 backend 目录）:
  python -m scripts.backfill_recipe_covers --dry-run
  python -m scripts.backfill_recipe_covers --limit 20
"""
from __future__ import annotations

import argparse
import sys
from typing import Any

sys.path.insert(0, ".")

from pymongo import MongoClient

from app.config import settings
from app.services.recipe_cover import ensure_recipe_cover


def _has_cover(image_url: Any) -> bool:
    return isinstance(image_url, str) and image_url.strip() != ""


def _build_query(refresh_all: bool) -> dict[str, Any]:
    if refresh_all:
        return {}
    return {
        "$or": [
            {"imageURL": {"$exists": False}},
            {"imageURL": None},
            {"imageURL": ""},
        ]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill recipe cover images")
    parser.add_argument("--limit", type=int, default=0, help="最多处理多少条（0 表示不限制）")
    parser.add_argument("--dry-run", action="store_true", help="只打印将要处理的记录，不落库")
    parser.add_argument("--refresh-all", action="store_true", help="忽略 imageURL 状态，全部重生成")
    args = parser.parse_args()

    if not settings.mongodb_url:
        print("未配置 MONGODB_URL，无法批量补封面。")
        return 1
    if not settings.doubao_image_api_key:
        print("未配置 DOUBAO_IMAGE_API_KEY / DOUBAO_API_KEY，无法调用生图。")
        return 1

    try:
        import certifi  # type: ignore
        client = MongoClient(settings.mongodb_url, tlsCAFile=certifi.where())
    except Exception:
        client = MongoClient(settings.mongodb_url)
    coll = client[settings.mongodb_db]["recipes"]

    query = _build_query(refresh_all=args.refresh_all)
    cursor = coll.find(query)
    if args.limit and args.limit > 0:
        cursor = cursor.limit(args.limit)
    docs = list(cursor)
    if not docs:
        print("没有需要补图的食谱。")
        return 0

    print(f"待处理 {len(docs)} 条食谱（dry-run={args.dry_run}）")
    success = 0
    failed = 0
    skipped = 0

    for doc in docs:
        rid = str(doc.get("_id", ""))
        title = (doc.get("title") or "").strip()
        old_url = doc.get("imageURL")
        if not title:
            print(f"- 跳过 {rid}: 缺少 title")
            skipped += 1
            continue

        if not args.refresh_all and _has_cover(old_url):
            print(f"- 跳过 {rid}: 已有 imageURL")
            skipped += 1
            continue

        if args.dry_run:
            print(f"- [dry-run] 将处理 {rid}: {title}")
            continue

        new_url = ensure_recipe_cover(doc)
        if not new_url:
            print(f"- 失败 {rid}: {title}（生图失败或未返回 URL）")
            failed += 1
            continue

        coll.update_one({"_id": doc["_id"]}, {"$set": {"imageURL": new_url}})
        print(f"- 成功 {rid}: {title} -> {new_url}")
        success += 1

    print(f"完成：success={success}, failed={failed}, skipped={skipped}")
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
