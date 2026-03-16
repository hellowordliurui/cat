"""
PRD 3.3：豆包（火山方舟）文本生成客户端
- 未配置 DOUBAO_API_KEY 时所有方法返回 None，便于静态逻辑降级。
- 供入库审计、食谱生成等模块复用。
"""
from __future__ import annotations

import ssl
from typing import Any

from app.config import settings

# 火山方舟 Chat Completions
_CHAT_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"


def _ssl_ctx() -> ssl.SSLContext | None:
    try:
        import certifi  # type: ignore

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def is_available() -> bool:
    """是否已配置并可调用豆包（有 API Key）。"""
    return bool(settings.doubao_api_key)


def generate_text(
    prompt: str,
    *,
    system_instruction: str | None = None,
    generation_config: dict[str, Any] | None = None,
) -> str | None:
    """
    调用豆包生成文本。
    无 API Key 或调用失败时返回 None。
    """
    if not settings.doubao_api_key:
        return None
    try:
        import urllib.request
        import json

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": settings.doubao_chat_model,
            "messages": messages,
        }
        if generation_config:
            if "temperature" in generation_config:
                body["temperature"] = generation_config["temperature"]
            if "max_tokens" in generation_config:
                body["max_tokens"] = generation_config["max_tokens"]

        req = urllib.request.Request(
            _CHAT_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.doubao_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60, context=_ssl_ctx()) as resp:
            data = json.loads(resp.read().decode())
        text = (data.get("choices") or [{}])[0].get("message", {}).get("content")
        return text.strip() if text else None
    except Exception:
        return None


def generate_content(
    prompt: str,
    *,
    system_instruction: str | None = None,
) -> Any | None:
    """
    调用豆包并返回完整 response 对象（便于解析）。
    无 API Key 或失败时返回 None。
    """
    if not settings.doubao_api_key:
        return None
    try:
        import urllib.request
        import json

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": settings.doubao_chat_model,
            "messages": messages,
        }
        req = urllib.request.Request(
            _CHAT_URL,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.doubao_api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60, context=_ssl_ctx()) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None
