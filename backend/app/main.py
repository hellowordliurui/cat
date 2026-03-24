"""
MoeChef 后端 - AI 内容审计引擎
PRD 3.2: PostgreSQL(禁忌+食谱), 冷启动加载禁忌到内存
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from app.api import recipes, forbidden, health, audit, generate_image as generate_image_router
from app.db.postgres import init_postgres, get_forbidden_list, get_recipes_from_postgres
from app.api.recipes import MOCK_RECIPES
from app.runtime_env import is_vercel


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动时从 PostgreSQL 加载禁忌清单到内存（PRD 无 Redis）。"""
    await init_postgres()
    yield
    # shutdown 可做清理


app = FastAPI(
    title="MoeChef API",
    description="猫咪精致辅食指南 - 已审计食谱与禁忌清单",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/health", tags=["健康检查"])
app.include_router(recipes.router, prefix="/api/recipes", tags=["食谱"])
app.include_router(forbidden.router, prefix="/api/forbidden", tags=["禁忌清单"])
app.include_router(audit.router, prefix="/api/audit", tags=["入库审计"])
app.include_router(generate_image_router.router, prefix="/api/generate-image", tags=["生图"])

# 生成图片存放目录：本地可写；Vercel Serverless 无持久磁盘，仅依赖 Supabase Storage
import os

_static_dir = os.path.join(os.path.dirname(__file__), "..", "static", "generated")
if not is_vercel():
    os.makedirs(_static_dir, exist_ok=True)
    app.mount("/static/generated", StaticFiles(directory=_static_dir), name="generated")

# 在 Cursor 里查看当前「数据库」数据：启动后端后浏览器打开 /db-view


@app.get("/")
async def root():
    """根路径：避免部署后打开 / 出现「无路由」；正式环境请用 /docs、/health。"""
    return {
        "service": "MoeChef API",
        "docs": "/docs",
        "health": "/health",
        "db_view": "/db-view",
    }


@app.get("/db-view", response_class=HTMLResponse)
async def db_view():
    """当前后端可见的数据：禁忌清单（内存/PostgreSQL）+ 食谱（PostgreSQL 或 mock）。"""
    forbidden_items = get_forbidden_list()
    recipe_items = await get_recipes_from_postgres(None)
    if not recipe_items:
        recipe_items = MOCK_RECIPES
    rows_f = "".join(
        f'<tr><td>{x.get("id","")}</td><td>{x.get("name","")}</td><td>{x.get("level","")}</td></tr>'
        for x in forbidden_items
    )
    def _recipe_row(r):
        img_url = r.get("imageURL") or r.get("image_url") or ""
        img_cell = (
            f'<td><a href="{img_url}" target="_blank" rel="noopener">'
            f'<img src="{img_url}" alt="" style="width:80px;height:80px;object-fit:cover;border-radius:8px;display:block;" '
            f'onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\';" />'
            f'<span style="display:none;font-size:12px;color:#999;">无图</span></a></td>'
        ) if img_url else '<td style="color:#999;">无图</td>'
        return f'<tr><td>{r.get("id","")}</td>{img_cell}<td>{r.get("title","")}</td><td>{r.get("category","")}</td></tr>'

    rows_r = "".join(_recipe_row(x) for x in recipe_items)
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"/><title>MoeChef 数据视图</title>
<style>
  body {{ font-family: system-ui; padding: 20px; background: #f7f9fc; }}
  h1 {{ color: #333; }}
  h2 {{ color: #ff7e5f; margin-top: 24px; }}
  table {{ border-collapse: collapse; width: 100%; max-width: 900px; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 12px rgba(0,0,0,.06); }}
  th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #eee; }}
  th {{ background: #ff7e5f; color: #fff; }}
  td img {{ vertical-align: middle; }}
  p.meta {{ color: #666; font-size: 14px; }}
</style>
</head>
<body>
  <h1>📊 MoeChef 当前数据</h1>
  <p class="meta">后端内存/PostgreSQL（或 mock）。刷新本页即最新。食谱封面为库中最新 imageURL。</p>
  <h2>🚫 禁忌清单 (forbidden_items)</h2>
  <table><thead><tr><th>id</th><th>name</th><th>level</th></tr></thead><tbody>{rows_f}</tbody></table>
  <h2>📖 食谱 (recipes) — 封面图</h2>
  <table><thead><tr><th>id</th><th>封面</th><th>title</th><th>category</th></tr></thead><tbody>{rows_r}</tbody></table>
</body>
</html>"""
    return HTMLResponse(html)
