"""
一次性迁移脚本：把 static/generated 里的食谱封面图上传到 Supabase Storage，
并把数据库中对应的 image_url 更新为 Supabase 公开 CDN 地址。
"""
import os
import sys
from pathlib import Path

# 让脚本能 import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from app.config import settings

SUPABASE_URL = "https://jqigumxkgbkxccvymotd.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpxaWd1bXhrZ2JreGNjdnltb3RkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI1OTIxNzMsImV4cCI6MjA4ODE2ODE3M30"
    ".gZ5MiHsov_AZYqMb8o-1KQciFDHejl8Za9WIetoHsmw"
)
BUCKET = "recipe-covers"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static" / "generated"


def public_url(filename: str) -> str:
    return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{filename}"


def upload_file(filename: str, data: bytes) -> bool:
    """上传单张图片，已存在则覆盖（upsert=true）。"""
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{filename}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "image/jpeg",
        "x-upsert": "true",
    }
    resp = requests.post(url, data=data, headers=headers, timeout=30)
    if resp.status_code in (200, 201):
        print(f"  ✓ 上传成功: {filename}")
        return True
    else:
        print(f"  ✗ 上传失败: {filename}  [{resp.status_code}] {resp.text[:200]}")
        return False


def update_db_image_url(old_url: str, new_url: str) -> None:
    """通过 Supabase REST API 把旧 image_url 替换成新的 Storage 地址。"""
    import urllib.parse
    url = (
        f"{SUPABASE_URL}/rest/v1/recipes"
        f"?image_url=eq.{urllib.parse.quote(old_url, safe='')}"
    )
    headers = {
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    resp = requests.patch(url, json={"image_url": new_url}, headers=headers, timeout=15)
    if resp.status_code in (200, 204):
        rows = resp.json() if resp.text else []
        print(f"  DB 更新 ({len(rows)} 行): {old_url!r} → {new_url!r}")
    else:
        print(f"  DB 更新失败 [{resp.status_code}]: {resp.text[:200]}")


def main():
    if not STATIC_DIR.exists():
        print("static/generated 目录不存在，退出。")
        return

    jpg_files = list(STATIC_DIR.glob("*.jpg")) + list(STATIC_DIR.glob("*.png"))
    if not jpg_files:
        print("没有找到本地图片文件。")
        return

    print(f"找到 {len(jpg_files)} 个图片文件，开始上传...\n")

    for path in jpg_files:
        filename = path.name
        data = path.read_bytes()
        print(f"[{filename}]")
        if upload_file(filename, data):
            old_url_variants = [
                f"http://127.0.0.1:8000/static/generated/{filename}",
                f"http://localhost:8000/static/generated/{filename}",
            ]
            new_url = public_url(filename)
            for old_url in old_url_variants:
                update_db_image_url(old_url, new_url)
        print()

    print("迁移完成！")


if __name__ == "__main__":
    main()
