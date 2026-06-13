"""AI 剧本杀 - 提示 Agent

根据玩家已发现的线索和审问记录，给出渐进式提示
提示分三级：弱提示 → 中提示 → 强提示
"""
from app.core.llm import chat


HINT_PROMPT = """你是一个剧本杀提示助手。根据玩家的调查进度，给出一个有帮助但不直接揭晓答案的提示。

## 案件信息
背景：{setting}
死者：{victim_name}，{cause_of_death}

## 嫌疑人概览
{suspects_summary}

## 所有线索
{all_clues}

## 凶手信息（仅供你参考，绝不能直接透露）
凶手：{culprit_name}
动机：{culprit_motive}
关键破绽：{culprit_secret}

## 玩家已发现的线索
{clues_found_text}

## 玩家的审问记录摘要
{chat_summary}

## 提示等级
当前是第 {hint_level} 次提示（共3次）：
- 第1次：给出方向性提示，指出哪个嫌疑人的口供可能有问题，或哪条线索值得深挖
- 第2次：更具体的提示，指出凶手的某个破绽方向，或某两个证据之间的矛盾
- 第3次：近乎明示的提示，直接指出凶手口供的关键漏洞，但不说出凶手名字

## 规则
1. 绝不能直接说出凶手是谁
2. 提示要基于已有证据，不要编造新线索
3. 用侦探助手的口吻，简短有力（50字以内）
4. 每次提示要比上次更具体
"""

EMPTY_CLUES_TEXT = "（玩家还没有搜索到任何线索）"


def give_hint(
    scenario: dict,
    clues_found: list[str],
    chat_history: dict,
    hints_used: int,
) -> str:
    """生成渐进式提示"""
    # 嫌疑人概览
    suspects_summary = "\n".join(
        f"- {s['name']}（{s['occupation']}）：{s['testimony']}"
        for s in scenario["suspects"]
    )

    # 所有线索
    all_clues = "\n".join(
        f"- [{c['id']}] {c['description']}（{'干扰项' if c.get('is_red_herring') else '关键线索'}）"
        for c in scenario["clues"]
    )

    # 已发现线索
    clues_found_text = "\n".join(f"- {c}" for c in clues_found) if clues_found else EMPTY_CLUES_TEXT

    # 审问记录摘要
    chat_summary_parts = []
    for suspect_id, messages in chat_history.items():
        suspect = next((s for s in scenario["suspects"] if s["id"] == suspect_id), None)
        if suspect and messages:
            chat_summary_parts.append(f"审问{suspect['name']}：{len(messages)}条对话")
    chat_summary = "\n".join(chat_summary_parts) if chat_summary_parts else "（尚未审问任何嫌疑人）"

    # 凶手信息
    culprit = next(s for s in scenario["suspects"] if s.get("is_culprit"))

    prompt = HINT_PROMPT.format(
        setting=scenario["setting"],
        victim_name=scenario["victim"]["name"],
        cause_of_death=scenario["victim"]["cause_of_death"],
        suspects_summary=suspects_summary,
        all_clues=all_clues,
        culprit_name=culprit["name"],
        culprit_motive=culprit["motive"],
        culprit_secret=culprit["secret"],
        clues_found_text=clues_found_text,
        chat_summary=chat_summary,
        hint_level=hints_used + 1,
    )

    return chat(
        system_prompt="你是剧本杀提示助手。给出简短有力的提示，50字以内，绝不说出凶手名字。",
        user_message=prompt,
        temperature=0.7,
    )
