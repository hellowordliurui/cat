"""
Vercel 部署入口：在 Dashboard 中将 Root Directory 设为 `backend` 时，
构建器会查找根目录下的 `main.py` 并导出名为 `app` 的 ASGI 应用。

本地开发仍推荐使用：
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

from app.main import app

__all__ = ["app"]
