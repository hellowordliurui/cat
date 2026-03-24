"""
Vercel 入口（与官方示例一致）：在 Root Directory = backend 时，构建器优先识别
「根目录 main.py」里导出的 ASGI 变量 `app`。

应用逻辑仍在 app/main.py；此处仅转发，避免 Vercel 未命中 app/main.py 导致全站 NOT_FOUND。

本地：uvicorn app.main:app --reload
Vercel：识别本文件中的 app（与 app.main.app 为同一实例）
"""
from __future__ import annotations

from app.main import app

__all__ = ["app"]
