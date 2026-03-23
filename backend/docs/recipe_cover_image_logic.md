# 食谱封面图：生成逻辑与取值逻辑

## 一、什么时候会「生成」封面图？

封面图**只在下面两种时机**被生成（调用豆包文生图）：

1. **新食谱入库时（POST /api/recipes）**  
   - 流程：审计 → 生成步骤 → **若当前食谱没有 `imageURL`** → 调用 `ensure_recipe_cover(recipe)` 生图 → 把返回的 URL 写入 `recipe["imageURL"]` → 再整条食谱写入 Supabase。  
   - 也就是说：**只有「没有带图」的新食谱才会在入库时自动生一张图**。

2. **手动跑 backfill 脚本时**  
   - 脚本：`scripts/backfill_recipe_covers_supabase.py`  
   - 从 Supabase 读出已有食谱，对每一条（或只对缺图的）再调一次 `ensure_recipe_cover(recipe)`，把新生成的图上传后，用 **PATCH** 只更新该条食谱的 `image_url` 字段。  
   - 用来「按新逻辑重画」旧食谱的封面，或给以前没图的补图。

除此之外，**不会**再自动生成图；已有 `imageURL` 的食谱在列表里只会用库里存的地址。

---

## 二、封面图是怎么「生成」的？（生图逻辑）

生成时只走一个入口：**`ensure_recipe_cover(recipe)`**（在 `app/services/recipe_cover.py`）。

1. **输入**  
   当前这一条食谱的完整对象 `recipe`，至少要包含：  
   `title`、`subtitle`、`category`、`ingredients`、`steps`（**步骤必须已有**，因为要用步骤推断成品长什么样）。

2. **生成「生图提示语」**（`_cover_prompt_llm_or_heuristic(recipe)`）  
   - **可选 LLM 生成**：若设置环境变量 `USE_LLM_COVER_PROMPT=1` 且已配置豆包文本 API，则优先用豆包文本模型根据「菜名 + 步骤全文 + 食材列表」生成一段英文生图提示，更贴合具体食谱；失败或未配置时自动退回规则拼接。  
   - **规则拼接**（`_cover_prompt(recipe)`）：提示词按 **「操作步骤总结 + 具体食材总结」** 生成，保证画面与食谱一致。  

   - **硬性约束**：  
     - 画面里**只能是「最终成品」**：步骤全部做完、已经装盘/盛碗、可以上桌的那一道菜。  
     - **不能**出现：生食材、制作过程、手、锅具等。  

   - **操作步骤总结**（`_summarize_steps_for_prompt(steps)`）：  
     - 基于**全部步骤文案**（而非仅首尾一句）推断最终成品的形态与呈现方式。  
     - 遍历步骤中的关键词，例如：  
       - 「脱模」「模具」「慕斯」「布丁」→ 脱模后的慕斯/布丁，小杯或半球在盘上；  
       - 「塔」「叠」「层」→ 分层塔/叠层在盘上；  
       - 「装盘」「盛出」「盛入」「碗」→ 已装盘或在小碗里的成品；  
       - 「浓汤」「羹」「汤」+「碗」→ 一碗成品浓汤/羹；  
       - 「冷藏」「定型」→ 冷藏定型后的成品；  
       - 「蛋糕」「糕」+ 切/片/块 → 小蛋糕或切块在盘上；  
       - 「杯」「杯状」→ 小杯或焗碗在盘上；  
       - 等等。  
     - 输出一句英文的「最终呈现描述」，用于提示中的 “Final presentation (from recipe steps): …”。  

   - **具体食材总结**（`_summarize_ingredients_for_prompt(ingredients)`）：  
     - 从食谱的**具体食材列表**取前 6 种食材名称，拼成一句。  
     - 在提示中写为「成品由这些食材制成、成品中可见」，避免被画成生料堆。  

   - **最终图片提示词**：  
     - 约束 + 菜名 + “Final presentation (from recipe steps):” + 步骤总结 + “The dish is made from and visibly contains these ingredients:” + 食材总结 + 猫用、有食欲、柔光、俯拍或小角度、干净盘/碗。

3. **调用豆包文生图**  
   - 用上面这段提示语调 `generate_image(prompt)`（豆包/火山方舟），得到一张图（字节）。

4. **存图并得到 URL**  
   - 文件名：`md5(标题)[:12].jpg`，**只跟标题有关**，同一标题多次生成会覆盖同一名。  
   - **优先**：上传到 Supabase Storage → 得到公开 CDN 地址。  
   - **降级**：若未配置或上传失败，则保存到后端 `static/generated/`，返回「后端 base URL + /static/generated/文件名」。

5. **返回值**  
   - 成功：返回**可访问的封面图 URL**（Supabase 或本地）。  
   - 失败：返回 `None`（未配置生图 key、生图接口报错、上传失败等）。

总结：**生成逻辑 = 按「操作步骤总结 + 具体食材总结」得到图片提示词（只画最终成品）→ 豆包生图 → 存到 Storage 或本地 → 得到 URL**。

---

## 三、封面图是怎么「被用到」的？（取值逻辑）

这里说的「取值」= 前端/App 展示某道菜的封面时，**这个图片地址是从哪儿来的**。

1. **数据从哪来**  
   - 列表：**GET /api/recipes** → 后端从 Supabase 查 `recipes` 表，每行里有一个字段 **`image_url`**。  
   - 后端返回时把这个字段映射成 **`imageURL`**（驼峰）给前端。  
   - 也就是说：**前端拿到的封面地址，唯一来源就是 Supabase 里这条食谱的 `image_url`**。

2. **`image_url` 是什么时候写进去的**  
   - **新食谱入库**：上面说过，入库时若没有 `imageURL`，会先 `ensure_recipe_cover(recipe)` 得到 URL，再 `recipe["imageURL"] = cover_url`，然后整条 insert/upsert 进 Supabase，表里存的就是 **`image_url`**。  
   - **Backfill 重生成**：脚本对某条食谱调 `ensure_recipe_cover(recipe)` 得到新 URL，再用 **PATCH** 只更新这条在 Supabase 里的 **`image_url`** 字段，别的字段不动。

3. **前端怎么用**  
   - 列表/详情里用：`recipe.imageURL`（或兼容 `recipe.image_url`）。  
   - 若 `imageURL` 为空/null：前端自己显示占位图（如「暂无封面」）。  
   - 若不为空：直接把这个 URL 当图片 src 用（Supabase 公开地址或后端 `/static/generated/xxx`）。

4. **同一道菜多张图？**  
   - 当前逻辑里**没有「多张图选一张」**：  
   - 每条食谱在库里**只有一个** `image_url`；  
   - 生图时的文件名只跟**标题**有关（`md5(标题)[:12].jpg`），所以同一标题再次生成会覆盖同一名文件，但**库里**要等 backfill 或重新入库才会更新为新的 URL（若 CDN 地址不变则还是同一个 URL）。

总结：**取值逻辑 = 列表/详情接口从 Supabase 读 `image_url` → 以 `imageURL` 给前端 → 前端用这个 URL 显示封面，没有就显示占位**；**没有任何地方会「实时再算一次」图，都是读库里已存的那一个地址**。

---

## 四、流程简图

```
新食谱入库 (POST /api/recipes)
  → 审计
  → 生成步骤 (豆包)
  → 若 recipe.imageURL 为空：
       → _cover_prompt(recipe) 用「操作步骤总结+具体食材总结」生成提示
       → 豆包文生图
       → 上传 Supabase Storage（或落本地 static/generated）
       → recipe["imageURL"] = 返回的 URL
  → insert_recipe(recipe) 整条写入 Supabase（含 image_url）

列表/详情 (GET /api/recipes 等)
  → 从 Supabase 读 recipes 表（含 image_url）
  → 映射成 imageURL 返回前端
  → 前端用 recipe.imageURL 显示封面
```

Backfill 脚本可以理解为：**把「从 Supabase 读出的每条 recipe」再走一遍「生成提示 → 豆包生图 → 上传」**，然后用 **PATCH 只更新这条的 image_url**，不改其他字段。
