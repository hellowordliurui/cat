"""
PRD 3.2：PostgreSQL（安全/用户/食谱）
配置从环境变量读取，未设置时可降级为内存 mock。
"""
import os
from pathlib import Path
from typing import Any

# 加载 backend/.env（脚本或 uvicorn 从 backend 运行时生效）
_env_file = Path(__file__).resolve().parent.parent / ".env"
if _env_file.exists():
    try:
        from dotenv import load_dotenv

        load_dotenv(_env_file)
    except ImportError:
        pass

    # 某些包含 URL、百分号或特殊字符的 .env 在 python-dotenv 下可能不会成功注入。
    # 这里做一层兜底，确保本地 backend/.env 中的值可被读取。
    for raw_line in _env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and not os.environ.get(key):
            os.environ[key] = value


def _env(key: str, default: str | None = None) -> str | None:
    return os.environ.get(key, default)


class Settings:
    """DATABASE_URL。可选 pydantic-settings 以支持 .env 与校验。"""
    @property
    def database_url(self) -> str | None:
        return _env("DATABASE_URL")

    @property
    def mongodb_url(self) -> str | None:
        """兼容旧配置，当前食谱链路不再使用。"""
        return _env("MONGODB_URL")

    @property
    def mongodb_db(self) -> str:
        """兼容旧配置，当前食谱链路不再使用。"""
        return _env("MONGODB_DB") or "moechef"

    # PRD 3.3：豆包（火山方舟）- 文本生成与生图
    @property
    def doubao_api_key(self) -> str | None:
        return _env("DOUBAO_API_KEY")

    @property
    def doubao_image_api_key(self) -> str | None:
        """生图专用 Key；未设置时使用 DOUBAO_API_KEY"""
        return _env("DOUBAO_IMAGE_API_KEY") or _env("DOUBAO_API_KEY")

    @property
    def doubao_chat_model(self) -> str:
        """对话模型 / 推理接入点 ID，如 doubao-pro-32k 或 ep-xxx"""
        return _env("DOUBAO_CHAT_MODEL") or "doubao-pro-32k"

    @property
    def doubao_image_model(self) -> str:
        """文生图模型，如 doubao-seedream-4-0-250828"""
        return _env("DOUBAO_IMAGE_MODEL") or "doubao-seedream-4-0-250828"

    @property
    def use_llm_cover_prompt(self) -> bool:
        """为 true 时封面图提示词优先用豆包文本模型生成，更准确；否则用规则拼接。"""
        v = (_env("USE_LLM_COVER_PROMPT") or "").strip().lower()
        return v in ("1", "true", "yes")

    @property
    def api_base_url(self) -> str:
        """后端 API 根地址，用于生成图片等静态资源的完整 URL"""
        return _env("API_BASE_URL") or "http://127.0.0.1:8000"

    # Supabase Storage
    @property
    def supabase_url(self) -> str | None:
        """Supabase 项目 URL，如 https://xxxx.supabase.co"""
        return _env("SUPABASE_URL")

    @property
    def supabase_anon_key(self) -> str | None:
        """Supabase anon/publishable key"""
        return _env("SUPABASE_ANON_KEY")

    @property
    def supabase_service_role_key(self) -> str | None:
        """Supabase service_role key，仅用于后端上传 Storage 以绕过 RLS。严禁暴露到前端。"""
        return _env("SUPABASE_SERVICE_ROLE_KEY")

    @property
    def supabase_storage_bucket(self) -> str:
        """食谱封面图 Bucket 名称"""
        return _env("SUPABASE_STORAGE_BUCKET") or "recipe-covers"


settings = Settings()
