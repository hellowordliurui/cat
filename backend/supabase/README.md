# Supabase 表结构与迁移

根据 PRD 3.2 在 Supabase PostgreSQL 中创建后端所需表与索引。**已通过 Supabase MCP 在项目中建表并应用迁移。**

## 当前表结构（MCP 已应用）

| 表名 | 用途 | 主要字段 |
|------|------|----------|
| `public.forbidden_items` | 禁忌食物清单（PRD 2.3 安全红线） | `id`, `name`, `category`(fatal/risk/info), `description`, 时间戳 |
| `public.profiles` | 用户档案（与 Auth 一对一） | `id`→auth.users, `display_name`, `avatar_url`, 时间戳 |
| `public.cats` | 猫咪档案（AI 品种补丁、RER/DER 计算） | `id`, `user_id`, `name`, `breed`, `body_weight_kg`, 时间戳 |

### 字段说明

- **forbidden_items**  
  - `name`: 食物名称（如 洋葱、巧克力、葡萄），唯一。  
  - `category`: `fatal` 致命类 / `risk` 风险类 / `info` 提示。  
  - 后端冷启动可据此加载到内存做禁忌词匹配。

- **profiles**  
  - `id` 关联 `auth.users(id)`，RLS 已开，用户仅能读写自己的 profile。

- **cats**  
  - `body_weight_kg`: 用于公式 RER = 70×weight^0.75，DER_snack = RER×10%。  
  - `user_id` 关联 `auth.users(id)`，RLS 已开，用户仅能管理自己的猫咪。

### 索引

- `forbidden_items`: `idx_forbidden_items_category`
- `profiles`: 无额外索引（主键查询为主）
- `cats`: `idx_cats_user_id`

## 方式一：Supabase Dashboard

1. 打开 [Supabase Dashboard](https://supabase.com/dashboard) → 选择项目。
2. 左侧 **SQL Editor** → **New query**。
3. 复制粘贴 `migrations/20250304100000_mcp_applied_schema.sql` 全文，点击 **Run**（新项目或未建表时使用）。

## 方式二：Supabase MCP（Cursor）

在 Cursor 中连接 Supabase MCP 后可使用：

- **apply_migration**：应用迁移（上述 SQL 已通过 MCP 应用）。
- **execute_sql**：执行单条查询。
- **list_tables**：查看 `public` 下所有表及列信息。

## 默认数据

- `forbidden_items`：迁移中已插入 6 条示例（洋葱、巧克力、葡萄、牛奶、生蛋白、高盐），与 PRD 示例一致。

## 旧迁移说明

- `migrations/20250303000000_create_tables_and_indexes.sql` 为早期设计（如 `forbidden_items` 曾用 `id` TEXT、`level` 等），当前以 **20250304100000_mcp_applied_schema.sql** 及 MCP 已应用结构为准。
