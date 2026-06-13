"""AI 剧本杀 - 嫌疑人 Agent

每个嫌疑人是一个独立 Agent，有自己的性格、秘密和口供策略
- 凶手会说谎，但谎言有逻辑漏洞
- 无辜者会隐瞒秘密，但不会编造虚假不在场证明
- 审问轮数有限，玩家需要策略性选择问题
"""
from typing import Optional
from app.core.llm import chat


def build_suspect_prompt(suspect: dict, scenario: dict, chat_history: list[dict]) -> str:
    """构建嫌疑人 Agent 的 System Prompt"""

    role = "凶手" if suspect["is_culprit"] else "无辜者"

    strategy = ""
    if suspect["is_culprit"]:
        strategy = f"""你是凶手！你必须：
1. 坚决否认自己是凶手
2. 你的不在场证明「{suspect['alibi']}」是编造的，其中有时序矛盾
3. 当被问到具体时间线时，你会含糊其辞或自相矛盾
4. 你会试图把嫌疑引向其他嫌疑人
5. 如果对方出示了与你不利的线索，你会紧张，回答开始出现破绽"""
    else:
        strategy = f"""你是无辜的。你的策略：
1. 你说的是真话，但会隐瞒你的秘密「{suspect['secret']}」
2. 你的不在场证明「{suspect['alibi']}」是真实的
3. 如果被问到你的秘密相关话题，你会试图转移话题
4. 你可能会因为其他原因对某些问题反应激烈（如私情、恩怨）
5. 你不确定谁是凶手，但你有自己的怀疑对象"""

    # 构建其他嫌疑人信息（Agent 能"知道"的部分）
    others_info = ""
    for s in scenario["suspects"]:
        if s["id"] != suspect["id"]:
            others_info += f"- {s['name']}（{s['occupation']}）：你知道TA的表面情况\n"

    # 构建已知线索
    clues_info = ""
    for c in scenario["clues"]:
        if c["related_suspect"] == suspect["id"]:
            clues_info += f"- 你知道：{c['description']}\n"

    history_text = ""
    if chat_history:
        history_text = "\n## 之前的对话\n"
        for msg in chat_history[-6:]:  # 只保留最近6条
            history_text += f"{'玩家' if msg['role'] == 'player' else '你'}：{msg['content']}\n"

    return f"""你正在扮演一个剧本杀嫌疑人。

## 你的身份
- 姓名：{suspect['name']}
- 年龄：{suspect['age']}
- 职业：{suspect['occupation']}
- 性格：{suspect['personality']}
- 你是：{role}

## 案件背景
{scenario['setting']}
死者：{scenario['victim']['name']}，{scenario['victim']['cause_of_death']}
死亡时间：{scenario['victim']['time_of_death']}
死亡地点：{scenario['victim']['location']}

## 你的动机
{suspect['motive']}

## 你的秘密
{suspect['secret']}

## 你的不在场证明
{suspect['alibi']}

## 你知道的其他嫌疑人
{others_info}

## 你知道的线索
{clues_info}

## 行为策略
{strategy}
{history_text}

## 重要规则
1. 始终以第一人称回答，保持角色不穿帮
2. 回答不超过 150 字，像真人对话一样自然
3. 不要直接暴露你的秘密或凶手身份
4. 如果被反复追问同一个问题，你会越来越紧张
5. 语气要符合你的性格：{suspect['personality']}
"""


def interrogate(suspect: dict, scenario: dict, question: str, chat_history: list[dict], model: Optional[str] = None) -> str:
    """审问嫌疑人"""
    system_prompt = build_suspect_prompt(suspect, scenario, chat_history)
    return chat(system_prompt, question, temperature=0.8, model=model)
