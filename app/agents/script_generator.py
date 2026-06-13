"""AI 剧本杀 - 剧本生成器

核心 Agent：生成完整的谋杀案剧本
包括：死者、嫌疑人、线索、凶手、各人口供
"""
import json
from app.core.llm import chat_json
from app.core.config import settings


SCRIPT_PROMPT = """你是一个悬疑剧本杀编剧大师。请生成一个谋杀案剧本，要求：

1. 故事背景设定在以下随机场景之一（必须从中选择，不要重复上次）：{scene}
2. 有 {suspect_count} 个嫌疑人，每人有独特性格和动机
3. 有 {clue_count} 条关键线索，部分指向凶手，部分是干扰项
4. 只有一个凶手，凶手的口供中必须包含可被识破的谎言
5. 每个嫌疑人知道部分真相，但会隐瞒或歪曲对自己不利的部分

请严格按以下 JSON 格式输出：

{{
    "title": "剧本标题",
    "setting": "故事背景描述（100字内）",
    "victim": {{
        "name": "死者姓名",
        "cause_of_death": "死因",
        "time_of_death": "死亡时间",
        "location": "死亡地点"
    }},
    "suspects": [
        {{
            "id": "suspect_1",
            "name": "姓名",
            "age": 年龄,
            "occupation": "职业",
            "personality": "性格特点（3个关键词）",
            "motive": "杀机（只有凶手这个字段是真实的，其他人写表面动机）",
            "alibi": "不在场证明",
            "secret": "隐藏的秘密（审问时可能暴露）",
            "is_culprit": false,
            "testimony": "初始口供（100字内，凶手口供含可识破的谎言）"
        }}
    ],
    "clues": [
        {{
            "id": "clue_1",
            "description": "线索描述",
            "location": "发现地点",
            "related_suspect": "suspect_1",
            "is_red_herring": false
        }}
    ]
}}

注意：
- 嫌疑人中必须有且只有一个人的 is_culprit 为 true
- 凶手的口供必须有逻辑漏洞，可被其他线索或证词推翻
- 每个嫌疑人的 secret 至少有一条与案件相关
- 线索中至少有 2 条是干扰项（red herring）
- 角色名字要有特色，不要用"张三李四"
"""


def generate_script(scene: str = "random", custom_scene: str = "") -> dict:
    """生成一个完整的剧本"""
    scene_map = {
        "luxury_cruise": "豪华远洋游轮",
        "snow_cabin": "雪山孤零零的小屋",
        "castle": "中世纪古堡",
        "tech_party": "科技公司年会",
        "movie_premiere": "电影首映礼后台",
        "archaeology": "考古发掘现场",
        "space_station": "太空站",
        "casino": "地下赌场",
        "concert_hall": "音乐学院演奏厅",
        "old_mansion": "百年老宅遗产继承",
        "island_resort": "热带孤岛度假村",
        "night_store": "深夜便利店",
        "art_gallery": "美术馆暗室",
        "train": "跨国列车包厢",
        "asylum": "废弃精神病院",
        "oil_rig": "海上石油钻井平台",
        "wine_cellar": "地下酒窖",
        "magic_show": "魔术秀后台",
        "esports": "电竞决赛现场",
        "private_jet": "私人飞机",
    }
    scenes = list(scene_map.values())

    if scene == "custom" and custom_scene:
        chosen_scene = custom_scene
    elif scene == "random" or scene not in scene_map:
        import random
        chosen_scene = random.choice(scenes)
    else:
        chosen_scene = scene_map[scene]

    prompt = SCRIPT_PROMPT.format(
        suspect_count=settings.SUSPECT_COUNT,
        clue_count=settings.CLUE_COUNT,
        scene=chosen_scene,
    )

    raw = chat_json(
        system_prompt="你是专业剧本杀编剧。只输出 JSON，不要输出任何其他内容。",
        user_message=prompt,
        temperature=0.8,  # 高温度保证每次不同
    )

    # 清理 LLM 输出中可能的 markdown 标记
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    if raw.startswith("```json"):
        raw = raw[7:]

    try:
        script = json.loads(raw.strip())
    except json.JSONDecodeError:
        # 如果解析失败，尝试提取 JSON 部分
        start = raw.find("{")
        end = raw.rfind("}") + 1
        script = json.loads(raw[start:end])

    # 验证基本结构
    assert "suspects" in script, "剧本缺少 suspects 字段"
    assert "clues" in script, "剧本缺少 clues 字段"
    assert any(s.get("is_culprit") for s in script["suspects"]), "没有指定凶手"

    return script
