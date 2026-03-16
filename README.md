# MoeChef — 猫咪精致辅食（下午茶）指南

**核心理念**：用 AI 过滤风险，用美学治愈生活。  
**目标平台**：iOS（SwiftUI）+ 后端 AI 审计引擎（FastAPI）。

---

## 项目结构

```
cat/
├── prd/                 # 产品需求文档
├── ios/                  # iOS 客户端 (SwiftUI)
│   └── MoeChef/         # 源码
│   └── MoeChef.xcodeproj
├── backend/              # 后端 API (FastAPI)
│   ├── app/
│   │   ├── api/         # 路由：食谱、禁忌清单、健康检查
│   │   ├── services/   # 入库审计、营养计算
│   │   └── main.py
│   └── requirements.txt
└── README.md
```

---

## 一、iOS 端（Phase 1 UI & Local）

- **框架**：SwiftUI，iOS 17+，Observation 状态管理，SwiftData 本地持久化
- **已实现**：
  - 首页：顶部 Tab（全部 / 冷饮 / 慕斯 / 蛋糕）+ 瀑布流卡片，标题展示当前猫咪名（SwiftData）
  - 详情页：极简食材、3 步制作、AI 品种建议、安全检测标签
  - 管理中心（右上角 👤）：**猫咪档案（SwiftData 本地存储）**、禁忌清单、账户设置
  - 温馨治愈配色 + 28pt 大圆角（见 `Theme.swift`）

### 运行方式

1. 用 **Xcode** 打开 `ios/MoeChef.xcodeproj`
2. 选择模拟器或真机，运行 (⌘R)

若 Xcode 报错「找不到项目」或「缺少文件」：  
可在 Xcode 中新建 iOS App 项目，将 `ios/MoeChef` 目录下除 `xcodeproj` 外的所有源码与资源拖入新项目的对应分组中，并确保 Deployment Target 为 iOS 17.0。

---

## 二、后端（PRD 3.2 / Phase 2 & 3）

- **框架**：Python 3.10+，FastAPI；**PostgreSQL**（禁忌清单/用户），**MongoDB**（食谱）；无 Redis，冷启动将禁忌加载到内存
- **已实现**：
  - `GET /health` — 健康检查
  - `GET /api/recipes?category=` — 食谱列表（**优先 MongoDB**，未配置则 mock）
  - `GET /api/forbidden` — 禁忌清单（**启动时自 PostgreSQL 加载到内存**，未配置则内置默认）
  - `POST /api/audit` — **入库审计接口**：提交食谱即检测，含禁忌则拒绝（PRD 3.3）
  - `app/services/ingestion_guard.py` — 静态过滤使用**内存禁忌 set**；可扩展豆包语义审计与美学润色
  - `app/services/nutrition.py` — RER / DER_snack（**PRD 3.4**）科学计算

可选环境变量（见 `backend/.env.example`）：`DATABASE_URL`（PostgreSQL）、`MONGODB_URL`、`MONGODB_DB`。

### 运行方式

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
若提示 `uvicorn: command not found`，说明依赖未装全，请先确保 `pip install -r requirements.txt` 成功，再改用：`python -m uvicorn app.main:app --reload`

API 文档：<http://127.0.0.1:8000/docs>

### 让别人连接你本机后端做测试

需要别人用你电脑上跑的后端数据时，有两种常见方式：

**方式一：同一 WiFi（局域网）**

1. 本机启动后端时加上 `--host 0.0.0.0`，允许同网段访问：
   ```bash
   cd backend && uvicorn app.main:app --reload --host 0.0.0.0
   ```
2. 在 Mac 上查本机 IP：`ifconfig | grep "inet " | grep -v 127.0.0.1`，记下如 `192.168.1.100`。
3. 把 **web 预览** 的链接发给对方，并在 URL 里带上你本机地址：
   - 例如：`file:///path/to/web-preview/index.html?api=http://192.168.1.100:8000`
   - 若你把 `web-preview` 部署到任意可访问的静态托管，链接形如：`https://xxx.com/index.html?api=http://192.168.1.100:8000`（对方需能访问该 IP，一般仅限同一局域网）。

**方式二：内网穿透（对方不在同一网络）**

用 [ngrok](https://ngrok.com/) 或 [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) 把本机 8000 端口暴露到公网，得到一个临时 HTTPS 地址，任何人可访问。

- **ngrok**（需注册）：`ngrok http 8000`，会得到类似 `https://xxxx.ngrok.io`。
- **cloudflared**：`cloudflared tunnel --url http://localhost:8000`，会得到临时 URL。

然后让对方打开 web 预览时带上该地址，例如：  
`index.html?api=https://xxxx.ngrok.io`  
（若用静态托管放 web-preview，就发：`https://你的静态站/index.html?api=https://xxxx.ngrok.io`。）

这样对方看到的就是连你本机数据的页面。

### 批量补齐食谱封面图（MongoDB）

当历史食谱缺少 `imageURL` 时，可批量调用豆包生图并回写数据库：

```bash
cd backend
./.venv/bin/python -m scripts.backfill_recipe_covers --dry-run
./.venv/bin/python -m scripts.backfill_recipe_covers --limit 20
```

可选参数：
- `--dry-run`：只预览不落库
- `--limit N`：限制处理数量
- `--refresh-all`：忽略已有封面，全部重生成

**在 Cursor 里直接看当前数据库数据（无需安装任何软件）**  
1. 在终端执行：`cd backend && source .venv/bin/activate && pip install -r requirements.txt && python -m uvicorn app.main:app --reload`  
2. 在 Cursor 按 `⌘+Shift+P`（或 `Ctrl+Shift+P`）→ 输入 **Simple Browser: Show** → 回车  
3. 在地址栏输入：**http://127.0.0.1:8000/db-view** → 回车  
即可看到当前「禁忌清单」和「食谱」两张表的数据（来自内存/PostgreSQL 与 MongoDB 或 mock）。  
注：猫咪档案存在 iOS 端 SwiftData，只能在 App 内「管理中心 → 猫咪档案」查看。

---

## 三、开发路线图（来自 PRD）

| Phase | 内容 |
|-------|------|
| **Phase 1 (UI & Local)** | ✅ Cool Porcelain + Sunset Coral 首页瀑布流；✅ **SwiftData 本地猫咪档案存储** |
| **Phase 2 (FastAPI & PostgreSQL)** | ✅ **PostgreSQL 存储禁忌食物，启动时内存加载**；✅ **AI 审计接口，入库即检测** |
| **Phase 3 (MongoDB)** | ✅ **通过审计的食谱存入 / 从 MongoDB 读取** |
| **Phase 4 (Final Polish)** | 调试 iOS 与后端 API 对接，实现「AI 品种补丁」实时显示 |
