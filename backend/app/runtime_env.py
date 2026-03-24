"""运行环境探测（Serverless / 本地）。"""
from __future__ import annotations

import os


def is_vercel() -> bool:
    """Vercel 部署时会注入 VERCEL=1。"""
    return os.environ.get("VERCEL", "").lower() in ("1", "true", "yes")
