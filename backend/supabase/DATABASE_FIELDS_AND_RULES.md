# MoeChef 数据库字段与规则文档

本文档描述 Supabase PostgreSQL（`public` schema）中所有表的字段定义、约束、索引与业务规则。对应 PRD 3.2「安全与用户数据库」。

---

## 一、表概览

| 表名 | 说明 | 行级安全(RLS) |
|------|------|----------------|
| `public.forbidden_items` | 禁忌食物清单（铲屎官安全红线） | 否 |
| `public.profiles` | 用户档案（与 Auth 一对一） | 是 |
| `public.cats` | 猫咪档案（品种补丁、热量计算） | 是 |

---

## 二、表与字段定义

### 2.1 `public.forbidden_items`

**用途**：存储由 AI 每日审计的禁忌食物清单，供后端冷启动加载到内存做入库安全拦截。对应 PRD 2.3「禁忌清单：铲屎官安全红线」。

| 字段名 | 类型 | 可空 | 默认值 | 约束/说明 |
|--------|------|------|--------|-----------|
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 |
| `name` | `text` | 否 | — | 食物名称，**唯一**。如：洋葱、巧克力、葡萄 |
| `category` | `text` | 否 | — | 见下方「枚举规则」 |
| `description` | `text` | 是 | — | 可选说明（如「致命类」「风险类」） |
| `created_at` | `timestamptz` | 否 | `now()` | 创建时间 |
| `updated_at` | `timestamptz` | 否 | `now()` | 更新时间 |

**表级约束**

- `PRIMARY KEY (id)`
- `UNIQUE (name)`
- `CHECK (category IN ('fatal', 'risk', 'info'))`

**索引**

- `idx_forbidden_items_category`：`(category)`，用于按类别筛选与冷启动加载。

**业务规则**

- `name` 建议按「单一种类」录入（如「洋葱」而非「洋葱、大蒜」），便于精确匹配。
- 后端启动时按 `category` 或全表加载到内存 set，做禁忌词匹配，无需 Redis。

---

### 2.2 `public.profiles`

**用途**：扩展 Supabase Auth 用户信息，存储展示名、头像等。与 `auth.users` 一对一。对应 PRD 3.2「用户账户」。

| 字段名 | 类型 | 可空 | 默认值 | 约束/说明 |
|--------|------|------|--------|-----------|
| `id` | `uuid` | 否 | — | 主键，**外键** → `auth.users(id) ON DELETE CASCADE` |
| `display_name` | `text` | 是 | — | 用户展示名称 |
| `avatar_url` | `text` | 是 | — | 头像 URL |
| `created_at` | `timestamptz` | 否 | `now()` | 创建时间 |
| `updated_at` | `timestamptz` | 否 | `now()` | 更新时间 |

**表级约束**

- `PRIMARY KEY (id)`
- `FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE`

**索引**

- 无额外索引（主键查询为主）。

**RLS 策略**

- `Users can read own profile`：`SELECT`，`USING (auth.uid() = id)`
- `Users can update own profile`：`UPDATE`，`USING (auth.uid() = id)`
- `Users can insert own profile`：`INSERT`，`WITH CHECK (auth.uid() = id)`

**业务规则**

- 一行对应一个已注册用户；通常在用户首次登录或完善资料时插入/更新。
- 仅当前登录用户可读、插、改自己的 profile。

---

### 2.3 `public.cats`

**用途**：猫咪档案，用于详情页「AI 品种建议」及辅食热量计算（RER、DER_snack）。对应 PRD 管理中心「猫咪档案」与科学计算逻辑。

| 字段名 | 类型 | 可空 | 默认值 | 约束/说明 |
|--------|------|------|--------|-----------|
| `id` | `uuid` | 否 | `gen_random_uuid()` | 主键 |
| `user_id` | `uuid` | 否 | — | **外键** → `auth.users(id) ON DELETE CASCADE`，归属用户 |
| `name` | `text` | 否 | — | 猫咪名字，如：大黄 |
| `breed` | `text` | 是 | — | 品种，如：英短（用于 AI 品种补丁） |
| `body_weight_kg` | `numeric(4,2)` | 是 | — | 体重(kg)，用于 RER/DER 公式 |
| `created_at` | `timestamptz` | 否 | `now()` | 创建时间 |
| `updated_at` | `timestamptz` | 否 | `now()` | 更新时间 |

**表级约束**

- `PRIMARY KEY (id)`
- `FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE`

**索引**

- `idx_cats_user_id`：`(user_id)`，用于「某用户的全部猫咪」查询。

**RLS 策略**

- `Users can manage own cats`：`ALL`（SELECT/INSERT/UPDATE/DELETE），`USING (auth.uid() = user_id)`

**业务规则**

- 仅当前登录用户可对自己名下的猫咪进行增删改查。
- `body_weight_kg` 参与 PRD 中的科学计算（见下文「计算规则」）。

---

## 三、枚举与取值规则

### 3.1 `forbidden_items.category`

| 取值 | 含义 | 展示示例 |
|------|------|----------|
| `fatal` | 致命类 | 🔴 致命类：洋葱、巧克力、葡萄 |
| `risk` | 风险类 | 🟡 风险类：牛奶、生蛋白、高盐 |
| `info` | 提示 | 💡 提示类说明 |

数据库仅允许以上三值，由 `CHECK` 约束保证。

---

## 四、计算与业务规则（与 PRD 一致）

### 4.1 静息能量需求（RER）

$$RER = 70 \times (body\_weight)^{0.75}$$

- `body_weight` 来自 `cats.body_weight_kg`（单位：kg）。
- 用于评估猫咪每日基础能量需求。

### 4.2 辅食热量上限（DER_snack）

$$DER_{snack} = RER \times 10\%$$

- 下午茶/辅食热量不超过每日总需求的 10%。
- 后端或前端在展示「一餐份」建议时可据此校验。

### 4.3 禁忌清单使用方式

- **冷启动**：FastAPI 启动时从 `forbidden_items` 读取全部或按 `category` 读取，写入内存 set。
- **入库审计**：AI 或静态逻辑在食谱入库前做禁忌词匹配，命中则拒绝入库。
- **展示**：可按 `category` 分组展示（致命 / 风险 / 提示）。

---

## 五、外键与删除规则

| 表 | 外键 | 引用 | 删除规则 |
|----|------|------|----------|
| `profiles` | `id` | `auth.users(id)` | `ON DELETE CASCADE`（用户删除则 profile 删除） |
| `cats` | `user_id` | `auth.users(id)` | `ON DELETE CASCADE`（用户删除则其猫咪记录删除） |

---

## 六、默认数据

- **forbidden_items**：14 种猫咪不可食用  
  fatal：洋葱、葱、大蒜、韭菜、巧克力、咖啡、浓茶、葡萄及葡萄干、木糖醇（代糖）、酒精、生面团、夏威夷果。  
  risk：牛奶、生鸡蛋。

---

## 七、文档与迁移对应关系

- 本文档与迁移文件 `migrations/20250304100000_mcp_applied_schema.sql` 一致。
- 表结构变更时请同步更新本文档及该迁移（或新增迁移并在此注明）。
