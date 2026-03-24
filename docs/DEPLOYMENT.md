# MoeChef 正式环境部署清单

把项目部署到正式服务器时，按下面清单逐项准备即可。

---

## 一、服务器与运行环境

| 项目 | 说明 |
|------|------|
| **服务器** | 一台可公网访问的 Linux 主机（如阿里云 / 腾讯云 / AWS，1 核 1G 起步即可） |
| **系统** | 推荐 Ubuntu 22.04 或 Debian 12 |
| **Python** | 3.10 或以上（`python3 --version` 确认） |
| **域名（可选）** | 为 API 准备域名，如 `api.yourdomain.com`，便于 HTTPS 与 iOS/Web 配置 |

---

## 二、后端 (FastAPI) 部署

### 2.1 环境变量（必须准备）

在服务器上创建 `backend/.env`（**不要**把本地含密钥的 `.env` 提交到 Git），按需填写：

| 变量名 | 必填 | 说明 |
|--------|------|------|
| `SUPABASE_URL` | ✅ | Supabase 项目 URL，如 `https://xxxx.supabase.co` |
| `SUPABASE_ANON_KEY` | ✅ | Supabase 的 anon/public Key（API → Project API keys） |
| `SUPABASE_STORAGE_BUCKET` | 可选 | 食谱封面图存储桶，默认 `recipe-covers` |
| `API_BASE_URL` | ✅ 生产必设 | 正式环境 API 的完整地址，如 `https://api.yourdomain.com`（用于生成图片等静态资源的完整 URL） |
| `DOUBAO_API_KEY` | 可选 | 豆包 API Key（启用 AI 审计、生图时必填） |
| `DOUBAO_IMAGE_API_KEY` | 可选 | 生图专用 Key，不设则用 `DOUBAO_API_KEY` |
| `DOUBAO_CHAT_MODEL` | 可选 | 对话模型，默认 `doubao-pro-32k` |
| `DOUBAO_IMAGE_MODEL` | 可选 | 文生图模型，默认 `doubao-seedream-4-0-250828` |

说明：当前食谱与禁忌清单均通过 **Supabase REST API** 读写，无需在服务器上单独安装 PostgreSQL/MongoDB。若你仍使用 MongoDB 做脚本或备份，可保留 `MONGODB_URL` / `MONGODB_DB`。

### 2.2 后端部署步骤（示例）

```bash
# 1. 上传代码到服务器（git clone 或 rsync/scp）
cd /opt/moechef  # 或你的项目目录

# 2. 创建虚拟环境并安装依赖
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. 在服务器上创建 .env，填入上述环境变量（不要用本机带密钥的 .env 直接拷贝到公网）

# 4. 用进程管理器跑 uvicorn（示例：监听 0.0.0.0:8000）
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

生产环境建议用 **systemd** 或 **supervisord** 管理进程，以便崩溃自启、开机自启。若用 Docker，可再加一层 Dockerfile 与 docker-compose。

### 2.3 生产运行建议

- **进程管理**：用 systemd/supervisord 跑 `uvicorn app.main:app --host 0.0.0.0 --port 8000`，不要用 `--reload`。
- **反向代理**：用 Nginx 或 Caddy 做反向代理，配置 HTTPS（如 Let's Encrypt），把 `https://api.yourdomain.com` 转到 `http://127.0.0.1:8000`。
- **API_BASE_URL**：在 `.env` 中设为 `https://api.yourdomain.com`，与对外访问的域名一致。

### 2.4 将 API 部署到 Vercel（Serverless）

仓库已在 `backend/` 下提供 **`main.py`（根目录）**、`vercel.json`、`.python-version`，与 [Vercel FastAPI 说明](https://vercel.com/docs/frameworks/backend/fastapi) 对齐。

1. **Vercel 控制台**：导入本 Git 仓库，在 **Project → Settings → General → Root Directory** 填 **`backend`**，保存后重新部署。
2. **环境变量**：在 Vercel **Settings → Environment Variables** 中逐项添加与 `backend/.env.example` 对应的生产变量（至少 `SUPABASE_URL`、`SUPABASE_ANON_KEY`；封面入库需 Storage 时加 `SUPABASE_SERVICE_ROLE_KEY` 与桶配置）。
3. **`API_BASE_URL`**：设为 Vercel 提供的正式域名（如 `https://xxx.vercel.app`），与生图/回写完整图片 URL 一致。
4. **限制**：Vercel 实例**无持久磁盘**，`/static/generated` 不会在云端挂载；封面图须 **成功上传到 Supabase Storage**。生图、豆包等接口受 **Function 超时** 限制，若频繁 504 需缩短链路或改用常驻进程托管（见 2.2）。
5. **验证**：部署成功后访问 **`/`** 应返回 JSON 引导；**`/docs`**、**`/health`**、**`/api/recipes`** 应可用。

本地开发仍使用：`cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`（与根目录 `main.py` 导出同一 `app` 实例）。

---

## 三、Web 预览 (web-preview) 部署

- `web-preview` 是纯静态（`index.html` + `placeholder.png`）。
- 可放在同一台机的 Nginx 静态目录，或任意静态托管（如 Vercel、Netlify、对象存储 + CDN）。

访问方式二选一：

1. **URL 参数指定后端**：  
   `https://你的静态站/index.html?api=https://api.yourdomain.com`
2. **同域部署**：若把静态站和 API 放在同一域名下（如 `/` 静态，`/api` 反代到后端），则无需带 `?api=`，前端会请求同源。

---

## 四、iOS 客户端

- iOS 应用不“部署到服务器”，只需在 App 内把 **接口根地址** 配成正式环境 API 地址（如 `https://api.yourdomain.com`）。
- 若当前写死为本地或测试地址，需在工程里改为从配置/环境读取，或打包前改成正式 API 地址。

---

## 五、安全与运维检查

| 项目 | 说明 |
|------|------|
| **不要提交 .env** | 确保 `backend/.env` 在 `.gitignore` 中，生产密钥只在服务器或密钥管理服务中配置 |
| **HTTPS** | 正式环境务必用 HTTPS（Nginx/Caddy + Let's Encrypt） |
| **CORS** | 当前为 `allow_origins=["*"]`，若只允许自己的前端，可在 `main.py` 中改为具体域名列表 |
| **Supabase** | 在 Supabase 控制台检查 RLS 策略与 anon key 权限，避免数据被误删或越权访问 |
| **豆包 Key** | 仅在需要 AI 审计/生图时配置；Key 不要写进前端或公开仓库 |

---

## 六、清单小结

1. 准备一台 Linux 服务器（Python 3.10+）。
2. 准备/确认 Supabase 项目（URL + anon key + 可选 Storage bucket）。
3. 在服务器上配置 `backend/.env`（至少 `SUPABASE_*`、`API_BASE_URL`，按需豆包 Key）。
4. 用 uvicorn + systemd/supervisord 跑后端，并用 Nginx/Caddy 做 HTTPS 反代。
5. 部署 web-preview 静态资源，通过 `?api=` 或同域方式指到正式 API。
6. iOS 端把接口地址改为正式 API 根地址。
7. 检查 CORS、RLS、密钥不泄露与 HTTPS。

按上述步骤即可把 MoeChef 部署到正式环境。若你提供当前用的系统（如 Ubuntu + Nginx），可以再写一份对应的 systemd 与 Nginx 配置示例。
