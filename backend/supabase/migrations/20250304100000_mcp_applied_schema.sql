-- MoeChef PRD 3.2：Supabase 表结构（已通过 Supabase MCP apply_migration 应用）
-- 安全与用户数据库：禁忌食物清单 + 用户档案 + 猫咪档案
-- 若在新项目执行：按顺序运行下面三段（或整文件）即可

-- =============================================================================
-- 1. 禁忌食物清单（PRD 2.3 铲屎官安全红线，由 AI 每日审计）
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.forbidden_items (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  category text NOT NULL CHECK (category IN ('fatal', 'risk', 'info')),
  description text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(name)
);

COMMENT ON TABLE public.forbidden_items IS '禁忌食物清单：致命类(fatal)/风险类(risk)/提示(info)';
COMMENT ON COLUMN public.forbidden_items.name IS '食物名称，如 洋葱、巧克力、葡萄';
COMMENT ON COLUMN public.forbidden_items.category IS 'fatal=致命类, risk=风险类, info=提示';

CREATE INDEX IF NOT EXISTS idx_forbidden_items_category ON public.forbidden_items(category);

-- 初始数据：14 种猫咪不可食用（fatal / risk）
INSERT INTO public.forbidden_items (name, category, description) VALUES
  ('洋葱', 'fatal', '猫咪不可食用'),
  ('葱', 'fatal', '猫咪不可食用'),
  ('大蒜', 'fatal', '猫咪不可食用'),
  ('韭菜', 'fatal', '猫咪不可食用'),
  ('巧克力', 'fatal', '猫咪不可食用'),
  ('咖啡', 'fatal', '猫咪不可食用'),
  ('浓茶', 'fatal', '猫咪不可食用'),
  ('葡萄及葡萄干', 'fatal', '猫咪不可食用'),
  ('木糖醇（代糖）', 'fatal', '猫咪不可食用'),
  ('酒精', 'fatal', '猫咪不可食用'),
  ('牛奶', 'risk', '猫咪不可食用'),
  ('生面团', 'fatal', '猫咪不可食用'),
  ('夏威夷果', 'fatal', '猫咪不可食用'),
  ('生鸡蛋', 'risk', '猫咪不可食用')
ON CONFLICT (name) DO NOTHING;

-- =============================================================================
-- 2. 用户档案（与 Supabase Auth 一对一，PRD 用户账户）
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.profiles (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  display_name text,
  avatar_url text,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.profiles IS '用户展示信息，与 auth.users 一对一';

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can read own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

-- =============================================================================
-- 3. 猫咪档案（PRD 管理中心-猫咪档案，AI 品种补丁与 RER/DER_snack 计算）
-- =============================================================================
CREATE TABLE IF NOT EXISTS public.cats (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  name text NOT NULL,
  breed text,
  body_weight_kg numeric(4,2),
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now()
);

COMMENT ON TABLE public.cats IS '猫咪档案：名称、品种、体重，用于 DER_snack 与 AI 品种补丁';
COMMENT ON COLUMN public.cats.body_weight_kg IS '体重(kg)，用于 RER=70*weight^0.75 与 DER_snack';

CREATE INDEX IF NOT EXISTS idx_cats_user_id ON public.cats(user_id);

ALTER TABLE public.cats ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can manage own cats" ON public.cats
  FOR ALL USING (auth.uid() = user_id);
