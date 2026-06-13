"""AI 剧本杀 - 评判 Agent

分析玩家的推理，判断是否正确，给出详细点评
"""
from typing import Optional
from app.core.llm import chat_json
import json


JUDGE_PROMPT = """你是一个剧本杀评委，需要评判玩家的推理是否正确。

## 案件真相
凶手：{culprit_name}（{culprit_id}）
动机：{culprit_motive}
作案手法：根据线索推断

## 所有线索
{clues_text}

## 玩家的推理
玩家认为凶手是：{player_guess}
推理过程：{player_reasoning}

## 请评判
请按以下 JSON 格式输出：

{{
    "is_correct": true/false,
    "score": 0-100,
    "analysis": "详细分析玩家的推理过程（200字内）",
    "truth_reveal": "揭晓真相的叙述（150字内，像侦探小说结尾一样精彩）",
    "tips": "给玩家的建议（50字内）"
}}

评分标准：
- 猜对凶手：基础 60 分
- 推理过程逻辑清晰：+20 分
- 提到了关键线索：+10 分
- 排除了干扰项：+10 分
"""


def judge(
    scenario: dict,
    player_guess: str,
    player_reasoning: str,
    model: Optional[str] = None,
) -> dict:
    """评判玩家的推理"""
    # 找到凶手
    culprit = next(s for s in scenario["suspects"] if s.get("is_culprit"))

    # 整理线索文本
    clues_text = "\n".join(
        f"- [{c['id']}] {c['description']}（{'干扰项' if c.get('is_red_herring') else '关键线索'}）"
        for c in scenario["clues"]
    )

    prompt = JUDGE_PROMPT.format(
        culprit_name=culprit["name"],
        culprit_id=culprit["id"],
        culprit_motive=culprit["motive"],
        clues_text=clues_text,
        player_guess=player_guess,
        player_reasoning=player_reasoning,
    )

    raw = chat_json(
        system_prompt="你是专业剧本杀评委。只输出 JSON。",
        user_message=prompt,
        temperature=0.3,  # 低温度保证评判公正
        model=model,
    )

    # 清理输出
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    if raw.startswith("```json"):
        raw = raw[7:]

    try:
        result = json.loads(raw.strip())
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        result = json.loads(raw[start:end])

    return result
