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
import time
import urllib.error
import urllib.request

from app.config import settings
from app.runtime_env import is_vercel

_STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "static", "generated")
logger = logging.getLogger(__name__)


def _slug_from_title(title: str, with_timestamp: bool = False) -> str:
    """with_timestamp=True 时文件名带时间戳，重生成时用新路径，避免 CDN 返回旧图。"""
    h = hashlib.md5(title.encode("utf-8")).hexdigest()[:12]
    if with_timestamp:
        return f"{h}_{int(time.time())}.jpg"
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
    后端上传时优先使用 service_role key 以绕过 RLS；未配置时使用 anon key。
    """
    project_url = settings.supabase_url
    bucket = settings.supabase_storage_bucket
    # 优先使用 service_role key（仅后端、绕过 RLS），否则用 anon key
    key = settings.supabase_service_role_key or settings.supabase_anon_key
    if not project_url or not key:
        return None

    upload_url = f"{project_url.rstrip('/')}/storage/v1/object/{bucket}/{filename}"
    req = urllib.request.Request(
        upload_url,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
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


def _save_to_local(filename: str, data: bytes) -> str | None:
    """降级方案：保存到 static/generated，返回本地 URL。"""
    if is_vercel():
        logger.warning(
            "Vercel 无持久磁盘，无法保存本地封面；请配置 Supabase Storage 与 service_role/anon 上传权限"
        )
        return None
    os.makedirs(_STATIC_DIR, exist_ok=True)
    path = os.path.join(_STATIC_DIR, filename)
    with open(path, "wb") as f:
        f.write(data)
    base = (settings.api_base_url or "http://127.0.0.1:8000").rstrip("/")
    url = f"{base}/static/generated/{filename}"
    logger.info("封面图已保存到本地（降级）: %s", url)
    return url


def _steps_text(steps: list) -> str:
    """把步骤列表拼成一段连续文案，便于做关键词与形态推断。"""
    if not steps:
        return ""
    texts = []
    for s in steps:
        if isinstance(s, str) and s.strip():
            texts.append(s.strip())
        elif isinstance(s, dict) and (s.get("text") or s.get("content")):
            texts.append(str(s.get("text") or s.get("content") or "").strip())
    return " ".join(texts)


def _summarize_steps_for_prompt(steps: list) -> str:
    """
    根据操作步骤总结出「最终成品」的形态与呈现方式，用于生图提示。
    优先看最后 1～2 步（装盘/脱模多在最后），再结合全文关键词。
    """
    full = _steps_text(steps)
    if not full:
        return "finished cat food dish on a plate, ready to serve"

    # 最后一步往往最能体现成品形态
    last_step = ""
    if steps:
        s = steps[-1]
        last_step = (s.get("text", s) if isinstance(s, dict) else str(s)).strip()

    combined = (last_step + " " + full).strip()

    # 根据步骤中出现的操作与形态关键词，总结成品描述（英文）
    if "脱模" in combined or "模具" in combined or "慕斯" in full or "布丁" in full:
        return "finished mousse or set pudding, unmolded, in a small cup or dome on a plate"
    if "塔" in combined or "叠" in combined or "层" in combined:
        return "finished layered tower or stack on a plate"
    if "冷藏" in full or "定型" in full:
        return "chilled finished dish, set shape on plate"
    if "装盘" in combined or "盛出" in combined or "盛入" in combined:
        return "finished dish plated or in a small bowl, ready to serve"
    if "浓汤" in full or "羹" in full or ("汤" in full and "碗" in full):
        return "finished creamy soup or thick broth in a small bowl"
    if "蛋糕" in full or ("糕" in full and ("切" in full or "片" in full or "块" in full)):
        return "finished small cake or slice on a plate"
    if "冷汤" in full or "冷饮" in full or "奶昔" in full or "冰" in full:
        return "finished cold soup or smoothie in a small bowl or cup"
    if "肉丸" in full or "串" in full or "丸" in full:
        return "finished small meatballs or skewered bites on a plate"
    if "切块" in combined or "切块" in full or "丁" in last_step:
        return "finished dish with small cubes or diced pieces on a plate"
    if "碗" in combined and "锅" not in full:
        return "finished dish in a small bowl, ready to serve"
    if "杯" in full or "杯状" in full:
        return "finished dish in a small cup or ramekin on a plate"
    return "finished cat food dish on a plate, ready to serve"


def _summarize_ingredients_for_prompt(ingredients: list) -> str:
    """
    从食谱的具体食材列表总结出一句用于生图提示的英文描述。
    强调「成品中可见或由这些食材制成」，避免被画成生料堆。
    """
    names = []
    for ing in ingredients[:6]:  # 取前 6 种以覆盖主要食材
        if isinstance(ing, dict):
            name = str(ing.get("name") or "").strip()
        else:
            name = str(ing).strip()
        if name:
            names.append(name)
    if not names:
        return ""
    return ", ".join(names)


def _cover_prompt_via_llm(recipe: dict) -> str | None:
    """
    用豆包文本模型根据「步骤 + 食材」生成一段英文生图提示词，更贴合具体食谱。
    失败或未配置时返回 None，由规则生成的提示词兜底。
    """
    try:
        from app.services.doubao_client import generate_text
    except ImportError:
        return None
    if not settings.doubao_api_key:
        return None

    title = (recipe.get("title") or "").strip()
    steps = recipe.get("steps") or []
    ingredients = recipe.get("ingredients") or []
    steps_str = _steps_text(steps)
    ing_names = []
    for ing in ingredients[:8]:
        if isinstance(ing, dict):
            ing_names.append(str(ing.get("name") or "").strip())
        else:
            ing_names.append(str(ing).strip())
    ingredients_str = "、".join(n for n in ing_names if n)

    system = (
        "You are an expert at writing English prompts for image generation. "
        "Given a cat food recipe, output ONE short paragraph in English that describes "
        "ONLY the final plated dish as served (no raw ingredients, no cooking process, no hands or utensils). "
        "Include: dish name, presentation (e.g. in a bowl, on a plate, unmolded), "
        "main visible ingredients in the finished dish, and style: cat-friendly, appetizing, "
        "soft lighting, top-down or slight angle, clean plate or bowl. Output only the prompt, no explanation."
    )
    user = (
        f"Recipe title: {title}\n"
        f"Steps: {steps_str}\n"
        f"Ingredients: {ingredients_str}\n"
        "Write the image prompt in English:"
    )

    out = generate_text(user, system_instruction=system, generation_config={"max_tokens": 256, "temperature": 0.3})
    if not out or not (out := out.strip()):
        return None
    # 限制长度，避免生图 API 超长
    if len(out) > 600:
        out = out[:597] + "..."
    return out


def _cover_prompt(recipe: dict) -> str:
    """
    按「操作步骤总结 + 具体食材总结」生成封面图提示词。
    步骤总结：根据全部步骤文案推断最终成品的形态与呈现方式；
    食材总结：列出主要具体食材，说明成品由这些食材制成、成品中可见。
    二者组合成一句清晰的英文生图提示，保证画面与食谱一致且仅为最终成品。
    """
    title = recipe.get("title") or ""
    category = (recipe.get("category") or "").strip().lower()
    ingredients = recipe.get("ingredients") or []
    steps = recipe.get("steps") or []

    # 1）操作步骤总结：从步骤推断最终成品形态
    steps_summary = _summarize_steps_for_prompt(steps)
    if not steps_summary:
        type_map = {
            "cake": "small cake or molded cake slice",
            "mousse": "mousse or set pudding in cup or dome",
            "cold": "cold dish or smoothie in bowl/cup",
        }
        steps_summary = f"finished {type_map.get(category, 'cat food dish')}"

    # 2）具体食材总结：主要食材列表，用于描述成品内容
    ingredients_summary = _summarize_ingredients_for_prompt(ingredients)

    # 硬性约束：画面只能是成品，不能是生食材或制作过程
    constraint = (
        "The image must show ONLY the final plated dish as served, "
        "no raw ingredients, no cooking process, no hands. "
    )
    # 用「步骤总结 + 食材总结」拼出最终图片提示词
    main_desc = (
        f"One single dish: {title}. "
        f"Final presentation (from recipe steps): {steps_summary}. "
    )
    if ingredients_summary:
        main_desc += (
            f"The dish is made from and visibly contains these ingredients: {ingredients_summary}. "
        )
    main_desc += (
        "Cat-friendly, appetizing, soft lighting, top-down or slight angle view, clean plate or bowl."
    )

    return (constraint + main_desc).strip()


def _cover_prompt_llm_or_heuristic(recipe: dict) -> str:
    """
    优先用豆包 LLM 生成生图提示（更准）；未配置或失败时用规则拼接。
    可通过环境变量 USE_LLM_COVER_PROMPT=1 开启 LLM。
    """
    if settings.use_llm_cover_prompt:
        llm_out = _cover_prompt_via_llm(recipe)
        if llm_out:
            constraint = (
                "The image must show ONLY the final plated dish as served, "
                "no raw ingredients, no cooking process, no hands. "
            )
            return (constraint + llm_out).strip()
        logger.warning("LLM cover prompt failed or empty, fallback to heuristic.")
    return _cover_prompt(recipe)


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

    prompt = _cover_prompt_llm_or_heuristic(recipe)
    result = generate_image(prompt)
    if result is None:
        return None
    bytes_data, _ = result
    # 固定文件名（仅按标题 hash），重生成时覆盖旧图，不堆积文件
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
