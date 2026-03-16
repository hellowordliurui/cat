-- MoeChef PRD 3.2：Supabase PostgreSQL 表结构与索引
-- 安全与用户数据库：禁忌食物清单 + 用户账户相关表
-- 执行方式：Supabase Dashboard → SQL Editor 粘贴执行，或通过 Supabase MCP apply_migration

-- =============================================================================
-- 1. 禁忌食物清单（后端冷启动加载到内存，API 返回）
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.forbidden_items (
    id   TEXT NOT NULL PRIMARY KEY,
    name TEXT NOT NULL,
    level TEXT NOT NULL
);

COMMENT ON TABLE public.forbidden_items IS '禁忌食物清单：PRD 2.3 致命类/风险类，由 AI 每日审计更新';
COMMENT ON COLUMN public.forbidden_items.level IS 'fatal | risk';

-- 按 level 过滤（列表/API 常用）
CREATE INDEX IF NOT EXISTS idx_forbidden_items_level
    ON public.forbidden_items (level);

-- 按 level + id 排序（与后端 ORDER BY level, id 一致）
CREATE INDEX IF NOT EXISTS idx_forbidden_items_level_id
    ON public.forbidden_items (level, id);

-- 默认数据（与后端 mock 一致，可选执行）
INSERT INTO public.forbidden_items (id, name, level)
VALUES
    ('f1', '洋葱、巧克力、葡萄', 'fatal'),
    ('f2', '牛奶、生蛋白、高盐', 'risk')
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- 2. 用户账户扩展（可选：与 Supabase Auth 联动，存应用层用户信息）
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id           UUID NOT NULL PRIMARY KEY REFERENCES auth.users (id) ON DELETE CASCADE,
    display_name TEXT,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.profiles IS '用户账户扩展：PRD 3.2 安全与用户数据库，与 auth.users 一对一';

CREATE INDEX IF NOT EXISTS idx_profiles_updated_at
    ON public.profiles (updated_at DESC);

-- RLS：仅允许用户读写自己的 profile
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile"
    ON public.profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile"
    ON public.profiles FOR INSERT
    WITH CHECK (auth.uid() = id);

-- =============================================================================
-- 3. forbidden_items 对 API 只读（可选：若需通过 MCP/后台写，可单独开 service role）
-- 此处不启用 RLS，由后端 FastAPI 使用 service role 或 anon + 策略控制访问
-- =============================================================================
