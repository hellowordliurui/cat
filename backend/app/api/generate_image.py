"""
生图 API：根据 prompt 调用豆包 Seedream 生成一张图并返回图片字节。
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.image_generation import generate_image

router = APIRouter()


@router.post("")
def generate_image_endpoint(body: dict):
    """
    请求体：{ "prompt": "英文描述，如 A cute cat food dish" }
    返回：image/jpeg 二进制，或 503（生图不可用/失败）。
    """
    prompt = (body or {}).get("prompt") or ""
    prompt = prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="缺少 prompt")
    result = generate_image(prompt)
    if result is None:
        raise HTTPException(
            status_code=503,
            detail="生图服务不可用（请配置 DOUBAO_IMAGE_API_KEY 或 DOUBAO_API_KEY）或生成失败",
        )
    bytes_data, mime_type = result
    return Response(content=bytes_data, media_type=mime_type)
