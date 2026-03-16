"""
PRD 3.2 / Phase 3：MongoDB 存储通过审计的高颜值食谱。
"""
from __future__ import annotations

import logging
import time
from typing import Any

from app.config import settings

_collection = None
logger = logging.getLogger(__name__)
_last_mongo_error: str | None = None
_mongo_cooldown_until = 0.0
_COOLDOWN_SECONDS = 30.0


def _get_collection():
    global _last_mongo_error
    global _mongo_cooldown_until
    global _collection
    if _collection is not None:
        return _collection
    if time.monotonic() < _mongo_cooldown_until:
        return None
    if not settings.mongodb_url:
        _last_mongo_error = "MONGODB_URL 未配置"
        return None
    from pymongo import MongoClient
    try:
        import certifi  # type: ignore
        client = MongoClient(
            settings.mongodb_url,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
        )
    except Exception:
        client = MongoClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000,
            socketTimeoutMS=5000,
        )
    _last_mongo_error = None
    db = client[settings.mongodb_db]
    _collection = db["recipes"]
    return _collection


def get_recipes_from_mongo(category: str | None = None) -> list[dict[str, Any]]:
    """从 MongoDB 读取已审计食谱；未配置或空时返回空列表（由调用方用 mock 兜底）。"""
    global _collection
    global _last_mongo_error
    global _mongo_cooldown_until
    coll = _get_collection()
    if coll is None:
        return []
    q = {} if not category or category == "all" else {"category": category}
    try:
        cursor = coll.find(q)
        items = []
        for doc in cursor:
            d = dict(doc)
            d["id"] = str(d.pop("_id", ""))
            items.append(d)
        _last_mongo_error = None
        return items
    except Exception as e:
        _last_mongo_error = str(e)
        _mongo_cooldown_until = time.monotonic() + _COOLDOWN_SECONDS
        _collection = None
        logger.error("Mongo read failed, fallback to mock: %s", e)
        return []


def insert_recipe(recipe: dict[str, Any]) -> str | None:
    """将通过审计的食谱写入 MongoDB，返回插入的 id。未配置则返回 None。"""
    global _collection
    global _last_mongo_error
    global _mongo_cooldown_until
    coll = _get_collection()
    if coll is None:
        return None
    try:
        doc = {k: v for k, v in recipe.items() if k != "id"}
        r = coll.insert_one(doc)
        _last_mongo_error = None
        return str(r.inserted_id) if r.inserted_id else None
    except Exception as e:
        _last_mongo_error = str(e)
        _mongo_cooldown_until = time.monotonic() + _COOLDOWN_SECONDS
        _collection = None
        logger.error("Mongo write failed, skip persistence: %s", e)
        return None


def get_last_mongo_error() -> str | None:
    return _last_mongo_error
