"""
生图：使用豆包（火山方舟）Seedream 文生图。
未配置 DOUBAO_API_KEY 或调用失败时返回 None。
"""
from __future__ import annotations

import base64
import json
import logging
import ssl
import urllib.request
import urllib.error

from app.config import settings

# 火山方舟 文生图
_IMAGE_URL = "https://ark.cn-beijing.volces.com/api/v3/images/generations"

# 默认尺寸需满足模型最小像素要求（>= 921600）
_DEFAULT_SIZE = "1024x1024"

logger = logging.getLogger(__name__)


def _ssl_context() -> ssl.SSLContext | None:
    """
    构造 HTTPS 证书上下文。
    优先使用 certifi，避免部分 Python 环境缺少系统根证书导致 SSL 校验失败。
    """
    try:
        import certifi  # type: ignore
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def generate_image(
    prompt: str,
    *,
    number_of_images: int = 1,
    output_mime_type: str = "image/jpeg",
) -> tuple[bytes, str] | None:
    """
    根据文本 prompt 生成一张图。
    返回 (图片字节, mime_type) 或 None（未配置/失败）。
    """
    if not settings.doubao_image_api_key:
        return None
    try:
        body = {
            "model": settings.doubao_image_model,
            "prompt": prompt,
            "n": number_of_images,
            "size": _DEFAULT_SIZE,
            "response_format": "b64_json",
        }
        req = urllib.request.Request(
            _IMAGE_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.doubao_image_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120, context=_ssl_context()) as resp:
            data = json.loads(resp.read().decode())
        items = data.get("data") or []
        if not items:
            logger.warning("Ark image API returned empty data field.")
            return None
        first = items[0]
        b64 = first.get("b64_json")
        if b64:
            raw = base64.b64decode(b64)
            return raw, output_mime_type
        url = first.get("url")
        if url:
            with urllib.request.urlopen(url, timeout=60, context=_ssl_context()) as img_resp:
                return img_resp.read(), output_mime_type
        logger.warning("Ark image API response has neither b64_json nor url.")
        return None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = "<unreadable>"
        logger.error("Ark image HTTP error: %s, body=%s", e.code, body[:1000])
        return None
    except urllib.error.URLError as e:
        logger.error("Ark image URL error: %s", e)
        return None
    except Exception as e:
        logger.exception("Ark image unexpected error: %s", e)
        return None


def is_available() -> bool:
    """生图是否可用（已配置 DOUBAO_API_KEY 或 DOUBAO_IMAGE_API_KEY）。"""
    return bool(settings.doubao_image_api_key)
