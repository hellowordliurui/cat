"""
食谱步骤生成：根据菜名和食材调用豆包生成制作步骤。
"""
from __future__ import annotations

import json
import re

from app.services.doubao_client import generate_text


_SYSTEM_PROMPT = """
你是资深猫咪辅食顾问，擅长为猫咪友好型辅食编写简洁、安全、可执行的制作步骤。
输出必须符合以下要求：
1. 仅返回 JSON 数组，不要加解释、标题、代码块。
2. 数组内每一项都是一个字符串步骤。
3. 默认生成 3 步，最多 4 步。
4. 步骤要体现蒸熟、压泥、混合、装盘/盛出等关键动作，避免生食、调味料、糖盐。
5. 文风温柔，但要明确易执行。
6. 重要：步骤描述的成品必须与「菜名」完全一致，不能写成别的菜品（例如菜名是草莓蛋糕，步骤就必须是做草莓蛋糕的步骤，不能写成慕斯、冷饮或其他菜）。
7. 猫咪不宜吃刚从冰箱拿出的食物，只有真正需要定型的品类（如慕斯、蛋糕、冻类）才写冷藏定型，且须注明「食用前回温至室温」；羹、汤、碗、糊等用盛出/装盘即可，不要强行加冷藏。
""".strip()


def _ingredient_lines(ingredients: list[dict] | list[str]) -> str:
    lines: list[str] = []
    for item in ingredients:
        if isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            amount = str(item.get("amount") or "").strip()
            if name and amount:
                lines.append(f"- {name}: {amount}")
            elif name:
                lines.append(f"- {name}")
        else:
            text = str(item).strip()
            if text:
                lines.append(f"- {text}")
    return "\n".join(lines)


def _clean_step(step: str) -> str:
    text = step.strip()
    text = re.sub(r"^[\-\d\.\)\s一二三四五六七八九十、]+", "", text)
    return text.strip(" \"'")


def _parse_steps(text: str | None) -> list[str] | None:
    if not text:
        return None

    body = text.strip()
    body = re.sub(r"^```(?:json)?\s*", "", body)
    body = re.sub(r"\s*```$", "", body)

    try:
        data = json.loads(body)
        if isinstance(data, list):
            steps = [_clean_step(str(item)) for item in data if str(item).strip()]
            return steps[:4] or None
    except Exception:
        pass

    match = re.search(r"\[[\s\S]*\]", body)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, list):
                steps = [_clean_step(str(item)) for item in data if str(item).strip()]
                return steps[:4] or None
        except Exception:
            pass

    candidates = [
        _clean_step(line)
        for line in body.splitlines()
        if _clean_step(line)
    ]
    return candidates[:4] or None


def ensure_recipe_steps(recipe: dict) -> list[str] | None:
    """
    若 recipe 未提供 steps，则调用豆包生成并写回 recipe["steps"]。
    返回步骤列表；失败返回 None。
    """
    current = recipe.get("steps")
    if isinstance(current, list):
        cleaned = [str(item).strip() for item in current if str(item).strip()]
        if cleaned:
            recipe["steps"] = cleaned
            return cleaned

    title = str(recipe.get("title") or "").strip()
    ingredients = recipe.get("ingredients") or []
    if not title or not ingredients:
        return None

    subtitle = str(recipe.get("subtitle") or "").strip()
    category = str(recipe.get("category") or "").strip()
    category_hint = ""
    if category:
        _map = {"cake": "蛋糕", "mousse": "慕斯", "cold": "冷饮"}
        category_hint = f"\n菜品类型：{_map.get(category.lower(), category)}（步骤必须做出这种类型的成品）"
    prompt = f"""
请为下面这道猫咪辅食生成 3 步制作步骤，并严格只返回 JSON 数组。步骤的成品必须就是「{title}」这道菜，不能是别的菜。

菜名：{title}
副标题：{subtitle or "无"}{category_hint}
食材：
{_ingredient_lines(ingredients)}

要求：
- 每步 18~38 字左右，语言自然温柔
- 不要出现任何调味料、糖、盐、生食建议
- 最后一步：羹/汤/糊/碗类用「盛出」或「装盘」即可；只有慕斯、蛋糕、冻类等需要定型的才写「冷藏定型」，且必须加上「食用前回温至室温再给猫咪」或类似表述（猫咪不宜吃冰的）
- 成品必须与菜名一致：做的是「{title}」，步骤里就要体现这道菜的特点（例如草莓蛋糕要有草莓、蛋糕形态；慕斯要有慕斯质地等）
""".strip()

    content = generate_text(
        prompt,
        system_instruction=_SYSTEM_PROMPT,
        generation_config={"temperature": 0.6, "max_tokens": 300},
    )
    steps = _parse_steps(content)
    if steps:
        recipe["steps"] = steps
    return steps
