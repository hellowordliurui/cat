"""
PRD 3.2：通过 Supabase REST API (PostgREST/HTTPS) 读写数据。
改用 REST API 原因：macOS 环境下 asyncpg 直连 db.*.supabase.co TCP 存在 DNS 解析问题；
HTTPS REST 接口可正常访问，无需额外依赖。
"""
from __future__ import annotations

import json
import logging
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from app.config import settings

forbidden_words_set: set[str] = set()
forbidden_list_cache: list[dict[str, Any]] = []
_last_recipe_db_error: str | None = None
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# 内部：Supabase REST API 辅助
# ──────────────────────────────────────────────

def _ssl_ctx() -> ssl.SSLContext | None:
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def _rest_headers() -> dict[str, str]:
    key = settings.supabase_anon_key or ""
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _rest_url(table: str, query: str = "") -> str:
    base = (settings.supabase_url or "").rstrip("/")
    url = f"{base}/rest/v1/{table}"
    if query:
        url = f"{url}?{query}"
    return url


def _http(method: str, url: str, body: dict | None = None, extra_headers: dict | None = None) -> Any:
    """发送 HTTP 请求，返回解析后的 JSON（或 None）。失败时抛出异常。"""
    data = json.dumps(body).encode() if body is not None else None
    headers = {**_rest_headers(), **(extra_headers or {})}
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    ctx = _ssl_ctx()
    with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
        raw = resp.read()
        return json.loads(raw) if raw else None


# ──────────────────────────────────────────────
# 禁忌清单
# ──────────────────────────────────────────────

_DEFAULT_FORBIDDEN = [
    {"id": "f1", "name": "洋葱、巧克力、葡萄", "level": "fatal", "description": ""},
    {"id": "f2", "name": "牛奶、生蛋白、高盐", "level": "risk", "description": ""},
]


async def init_postgres() -> None:
    """FastAPI 启动时：从 Supabase REST API 读取禁忌清单到内存。"""
    global forbidden_list_cache
    if not settings.supabase_url or not settings.supabase_anon_key:
        forbidden_list_cache = _DEFAULT_FORBIDDEN
        _refresh_forbidden_set_from_list(forbidden_list_cache)
        return
    try:
        query = "select=id,name,category,description&order=category.asc,id.asc"
        rows = _http("GET", _rest_url("forbidden_items", query))
        if rows:
            forbidden_list_cache = [
                {
                    "id": str(r.get("id", "")),
                    "name": r.get("name", ""),
                    "level": r.get("level") or r.get("category") or "",
                    "description": r.get("description") or "",
                }
                for r in rows
            ]
            _refresh_forbidden_set_from_list(forbidden_list_cache)
            logger.info("禁忌清单已从 Supabase 加载 %d 条", len(forbidden_list_cache))
            return
    except Exception as e:
        logger.warning("禁忌清单加载失败，使用默认值: %s", e)
    forbidden_list_cache = _DEFAULT_FORBIDDEN
    _refresh_forbidden_set_from_list(forbidden_list_cache)


def _refresh_forbidden_set_from_list(items: list[dict[str, Any]]) -> None:
    s: set[str] = set()
    for item in items:
        name = item.get("name") or ""
        for part in re.split(r"[、,，\s]+", name):
            t = part.strip().lower()
            if t:
                s.add(t)
    forbidden_words_set.clear()
    forbidden_words_set.update(s)


def get_forbidden_list() -> list[dict[str, Any]]:
    return list(forbidden_list_cache)


# ──────────────────────────────────────────────
# 食谱 CRUD
# ──────────────────────────────────────────────

async def get_recipes_from_postgres(category: str | None = None) -> list[dict[str, Any]]:
    """通过 Supabase REST API 读取食谱列表。"""
    global _last_recipe_db_error
    if not settings.supabase_url or not settings.supabase_anon_key:
        _last_recipe_db_error = "SUPABASE_URL / SUPABASE_ANON_KEY 未配置"
        return []
    try:
        cols = "id,title,subtitle,category,image_url,ingredients,steps,ai_breed_note,safety_passed"
        parts = [f"select={cols}", "order=created_at.desc"]
        if category and category != "all":
            parts.append(f"category=eq.{urllib.parse.quote(category)}")
        rows = _http("GET", _rest_url("recipes", "&".join(parts)))
        _last_recipe_db_error = None
        if not rows:
            return []
        return [
            {
                "id": str(r["id"]),
                "title": r["title"],
                "subtitle": r.get("subtitle") or "",
                "category": r.get("category") or "all",
                "imageURL": r.get("image_url"),
                "ingredients": r.get("ingredients") or [],
                "steps": r.get("steps") or [],
                "aiBreedNote": r.get("ai_breed_note"),
                "safetyPassed": bool(r.get("safety_passed", True)),
            }
            for r in rows
        ]
    except Exception as e:
        _last_recipe_db_error = str(e)
        logger.error("Supabase REST recipe read failed: %s", e)
        return []


async def insert_recipe(recipe: dict[str, Any]) -> str | None:
    """通过 Supabase REST API upsert 食谱，返回 id。"""
    global _last_recipe_db_error
    if not settings.supabase_url or not settings.supabase_anon_key:
        _last_recipe_db_error = "SUPABASE_URL / SUPABASE_ANON_KEY 未配置"
        return None
    try:
        body = {
            "title": recipe.get("title"),
            "subtitle": recipe.get("subtitle"),
            "category": recipe.get("category"),
            "image_url": recipe.get("imageURL"),
            "ingredients": recipe.get("ingredients") or [],
            "steps": recipe.get("steps") or [],
            "ai_breed_note": recipe.get("aiBreedNote"),
            "safety_passed": bool(recipe.get("safetyPassed", True)),
        }
        extra = {
            "Prefer": "return=representation,resolution=merge-duplicates",
        }
        rows = _http("POST", _rest_url("recipes", "on_conflict=title"), body, extra)
        _last_recipe_db_error = None
        if rows and isinstance(rows, list):
            return str(rows[0].get("id"))
        return None
    except Exception as e:
        _last_recipe_db_error = str(e)
        logger.error("Supabase REST recipe write failed: %s", e)
        return None


def get_last_recipe_db_error() -> str | None:
    return _last_recipe_db_error


def update_recipe_image_url(recipe_id: str, image_url: str | None) -> bool:
    """仅更新食谱的封面图 URL（用于 backfill 重生成封面）。"""
    if not settings.supabase_url or not settings.supabase_anon_key:
        return False
    if not recipe_id or not (image_url or "").strip():
        return False
    try:
        url = _rest_url("recipes", f"id=eq.{urllib.parse.quote(str(recipe_id))}")
        _http(
            "PATCH",
            url,
            {"image_url": (image_url or "").strip()},
            extra_headers={"Prefer": "return=minimal"},
        )
        return True
    except Exception as e:
        logger.warning("Supabase PATCH image_url failed: %s", e)
        return False


def update_recipe_steps(recipe_id: str, steps: list[str]) -> bool:
    """仅更新食谱的 steps 字段。"""
    if not settings.supabase_url or not settings.supabase_anon_key:
        return False
    if not recipe_id or not isinstance(steps, list):
        return False
    try:
        url = _rest_url("recipes", f"id=eq.{urllib.parse.quote(str(recipe_id))}")
        _http(
            "PATCH",
            url,
            {"steps": steps},
            extra_headers={"Prefer": "return=minimal"},
        )
        return True
    except Exception as e:
        logger.warning("Supabase PATCH steps failed: %s", e)
        return False


def delete_recipe_by_id(recipe_id: str) -> bool:
    """按 id 删除一条食谱。"""
    if not settings.supabase_url or not settings.supabase_anon_key:
        return False
    if not recipe_id:
        return False
    try:
        url = _rest_url("recipes", f"id=eq.{urllib.parse.quote(str(recipe_id))}")
        req = urllib.request.Request(url, headers=_rest_headers(), method="DELETE")
        ctx = _ssl_ctx()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            pass
        return True
    except Exception as e:
        logger.warning("Supabase DELETE recipe failed: %s", e)
        return False


def delete_recipe_by_title(title: str) -> bool:
    """按 title 精确匹配删除一条食谱。"""
    t = str(title).strip() if title else ""
    if not t:
        return False
    try:
        url = _rest_url("recipes", f"title=eq.{urllib.parse.quote(t)}")
        req = urllib.request.Request(url, headers=_rest_headers(), method="DELETE")
        ctx = _ssl_ctx()
        with urllib.request.urlopen(req, timeout=15, context=ctx) as resp:
            pass
        return True
    except Exception as e:
        logger.warning("Supabase DELETE recipe by title failed: %s", e)
        return False
