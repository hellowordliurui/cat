"""
食谱封面图：入库时若无 imageURL 则用豆包生图，
优先上传到 Supabase Storage（公开 CDN），
若未配置 Supabase 则降级保存到 static/generated 本地目录。
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import ssl
import urllib.error
import urllib.request

from app.config import settings

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "generated")
logger = logging.getLogger(__name__)


def _slug_from_title(title: str) -> str:
    h = hashlib.md5(title.encode("utf-8")).hexdigest()[:12]
    return f"{h}.jpg"


def _ssl_ctx() -> ssl.SSLContext | None:
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def _upload_to_supabase(filename: str, data: bytes) -> str | None:
    """
    把图片字节上传到 Supabase Storage，返回公开 CDN URL；失败返回 None。
    """
    project_url = settings.supabase_url
    anon_key = settings.supabase_anon_key
    bucket = settings.supabase_storage_bucket
    if not project_url or not anon_key:
        return None

    upload_url = f"{project_url.rstrip('/')}/storage/v1/object/{bucket}/{filename}"
    req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            "Authorization": f"Bearer {anon_key}",
            "Content-Type": "image/jpeg",
            "x-upsert": "true",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30, context=_ssl_ctx()) as resp:
            resp.read()
        public_url = f"{project_url.rstrip('/')}/storage/v1/object/public/{bucket}/{filename}"
        logger.info("封面图已上传到 Supabase Storage: %s", public_url)
        return public_url
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            pass
        logger.warning("Supabase Storage 上传失败 %s: %s", e.code, body[:300])
        return None
    except Exception as e:
        logger.warning("Supabase Storage 上传异常: %s", e)
        return None


def _save_to_local(filename: str, data: bytes) -> str:
    """降级方案：保存到 static/generated，返回本地 URL。"""
    os.makedirs(_STATIC_DIR, exist_ok=True)
    path = os.path.join(_STATIC_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    base = (settings.api_base_url or "http://127.0.0.1:8000").rstrip("/")
    url = f"{base}/static/generated/{filename}"
    logger.info("封面图已保存到本地（降级）: %s", url)
    return url


def _final_shape_from_steps(steps: list) -> str:
    """
    从步骤文案推断成品的形态与呈现方式，用于生图提示。
    最后一步通常包含装盘/脱模/盛出/冷藏等，最能体现最终样子。
    """
    if not steps or not isinstance(steps[0], str):
        return ""
    last = (steps[-1] if steps else "").strip()
    first = (steps[0] if steps else "").strip()
    # 根据关键词推断成品形态（英文，便于生图模型）
    if "脱模" in last or "模具" in last or "慕斯" in first + last:
        return "finished mousse or set pudding, unmolded, in a small cup or dome shape on a plate"
    if "塔" in last or "叠" in last or "层" in last:
        return "finished layered tower or stack on a plate"
    if "冷藏" in last or "定型" in last:
        return "chilled finished dish, set shape on plate"
    if "装盘" in last or "盛出" in last or "碗" in last:
        return "finished dish plated or in a small bowl, ready to serve"
    if "浓汤" in first + last or "羹" in first + last or "汤" in last:
        return "finished creamy soup or thick broth in a small bowl"
    if "蛋糕" in first + last or "糕" in last:
        return "finished small cake or slice on a plate"
    if "冷汤" in first + last or "冷饮" in first + last:
        return "finished cold soup or smoothie in a small bowl or cup"
    if "肉丸" in first + last or "串" in last:
        return "finished small meatballs or skewered bites on a plate"
    return "finished cat food dish on a plate, ready to serve"


def _cover_prompt(recipe: dict) -> str:
    """
    生成封面图描述：强调「最终成品」与步骤一致，避免出现生食材或与步骤无关的画面。
    生图模型得到的必须是：步骤全部完成后的、可上桌的那一道菜。
    """
    title = recipe.get("title") or ""
    subtitle = (recipe.get("subtitle") or "").strip()
    category = (recipe.get("category") or "").strip().lower()
    ingredients = recipe.get("ingredients") or []
    steps = recipe.get("steps") or []

    # 品类 → 成品形态（英文）
    type_map = {
        "cake": "small cake or molded cake slice",
        "mousse": "mousse or set pudding in cup or dome",
        "cold": "cold dish or smoothie in bowl/cup",
    }
    dish_type = type_map.get(category, "cat food dish")

    # 主要食材（成品中应能体现的颜色/质地，而非生料）
    key_ingredients = []
    for ing in ingredients[:4]:
        if isinstance(ing, dict):
            name = str(ing.get("name") or "").strip()
        else:
            name = str(ing).strip()
        if name:
            key_ingredients.append(name)
    ingredients_phrase = ", ".join(key_ingredients) if key_ingredients else ""

    # 从步骤推断最终形态
    shape_desc = _final_shape_from_steps(steps)
    if not shape_desc:
        shape_desc = f"finished {dish_type}"

    # 硬性约束：画面只能是成品，不能是生食材或半成品
    constraint = (
        "The image must show ONLY the final plated dish as served, "
        "no raw ingredients, no cooking process, no hands. "
    )
    # 中文菜名 + 成品描述，让模型对齐
    main_desc = (
        f"One single dish: {title}. "
        f"It is a {shape_desc}. "
        f"The dish visibly contains or is made from: {ingredients_phrase}. "
        f"Cat-friendly, appetizing, soft lighting, top-down or slight angle view, clean plate or bowl."
    )

    return (constraint + main_desc).strip()


def ensure_recipe_cover(recipe: dict) -> str | None:
    """
    若食谱没有 imageURL，则调用豆包生图并存储，返回完整 URL。
    优先 Supabase Storage，不可用时降级到本地 static/generated。
    生图提示强调「仅最终成品」：根据步骤推断装盘形态，避免出现生食材或与步骤不符的画面。
    返回 None 表示未配置生图或生成失败。
    """
    title = recipe.get("title") or ""
    if not title:
        return None
    from app.services.image_generation import generate_image

    prompt = _cover_prompt(recipe)
    result = generate_image(prompt)
    if result is None:
        return None
    bytes_data, _ = result
    filename = _slug_from_title(title)

    cdn_url = _upload_to_supabase(filename, bytes_data)
    if cdn_url:
        return cdn_url
    return _save_to_local(filename, bytes_data)


def get_cover_url_for_title(title: str) -> str:
    """返回该标题对应的封面图 URL（Storage 优先，否则本地）。"""
    filename = _slug_from_title(title)
    project_url = settings.supabase_url
    bucket = settings.supabase_storage_bucket
    if project_url:
        return f"{project_url.rstrip('/')}/storage/v1/object/public/{bucket}/{filename}"
    base = (settings.api_base_url or "http://127.0.0.1:8000").rstrip("/")
    return f"{base}/static/generated/{filename}"
