from __future__ import annotations
"""AI 剧本杀 - API 路由"""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.core.redis_manager import redis_mgr
from app.core.clue_manager import clue_manager
from app.agents.script_generator import generate_script
from app.agents.suspect_agent import interrogate
from app.agents.judge_agent import judge
from app.agents.hint_agent import give_hint
from app.core.models import User, Game, ChatLog

router = APIRouter()


# ---- 请求/响应模型 ----

class RegisterReq(BaseModel):
    nickname: str
    avatar: str = "🕵️"


class StartGameReq(BaseModel):
    custom_scene: str = ""


class StartGameResp(BaseModel):
    game_id: str
    title: str
    setting: str
    victim: dict
    suspects: list[dict]  # 不含 is_culprit
    clues: list[dict]     # 不含 is_red_herring


class InterrogateReq(BaseModel):
    game_id: str
    suspect_id: str
    question: str


class SearchClueReq(BaseModel):
    game_id: str
    query: str


class SubmitGuessReq(BaseModel):
    game_id: str
    culprit_id: str
    reasoning: str


class HintReq(BaseModel):
    game_id: str


# ---- API 接口 ----

@router.post("/api/register")
def register(req: RegisterReq, db: Session = Depends(get_db)):
    """注册/登录（昵称唯一）"""
    user = db.query(User).filter(User.nickname == req.nickname).first()
    if not user:
        user = User(nickname=req.nickname, avatar=req.avatar)
        db.add(user)
        db.commit()
        db.refresh(user)
    return {"user_id": user.id, "nickname": user.nickname}


@router.post("/api/game/start", response_model=StartGameResp)
def start_game(nickname: str = "侦探", scene: str = "random", db: Session = Depends(get_db)) -> StartGameResp:
    """开始新游戏：AI 生成剧本"""
    game_id = str(uuid.uuid4())[:8]

    # 1. 生成剧本
    try:
        scenario = generate_script(scene=scene)
    except Exception as e:
        raise HTTPException(500, f"生成剧本失败: {str(e)}")

    # 2. 索引线索
    scenario_text = f"{scenario['setting']} 死者：{scenario['victim']['name']}"
    clue_manager.index_clues(game_id, scenario["clues"], scenario_text)

    # 3. 保存会话到 Redis
    redis_mgr.save_session(game_id, {
        "scenario": scenario,
        "chat_history": {},  # suspect_id -> [messages]
        "clues_found": [],
        "rounds": {},
        "hints_used": 0,     # 已使用提示次数
    }, ttl=7200)  # 2小时

    # 4. 写入数据库
    user = db.query(User).filter(User.nickname == nickname).first()
    game = Game(
        user_id=user.id if user else None,
        title=scenario["title"],
        scenario=scenario,
        culprit_id=next(s["id"] for s in scenario["suspects"] if s.get("is_culprit")),
    )
    db.add(game)
    db.commit()

    # 5. 返回前端需要的数据（隐藏凶手标记和干扰项标记）
    suspects_safe = []
    for s in scenario["suspects"]:
        suspects_safe.append({
            "id": s["id"],
            "name": s["name"],
            "age": s["age"],
            "occupation": s["occupation"],
            "personality": s["personality"],
            "alibi": s["alibi"],
            "testimony": s["testimony"],
        })

    clues_safe = [{"id": c["id"], "description": c["description"], "location": c["location"]}
                  for c in scenario["clues"]]

    redis_mgr.incr_online()

    return StartGameResp(
        game_id=game_id,
        title=scenario["title"],
        setting=scenario["setting"],
        victim=scenario["victim"],
        suspects=suspects_safe,
        clues=clues_safe,
    )


@router.post("/api/game/start-custom", response_model=StartGameResp)
def start_game_custom(req: StartGameReq, nickname: str = "侦探", db: Session = Depends(get_db)) -> StartGameResp:
    """开始自定义场景游戏"""
    game_id = str(uuid.uuid4())[:8]

    # 1. 用自定义场景生成剧本
    scenario = generate_script(scene="custom", custom_scene=req.custom_scene)

    # 2-5 同上
    scenario_text = f"{scenario['setting']} 死者：{scenario['victim']['name']}"
    clue_manager.index_clues(game_id, scenario["clues"], scenario_text)

    redis_mgr.save_session(game_id, {
        "scenario": scenario,
        "chat_history": {},
        "clues_found": [],
        "rounds": {},
        "hints_used": 0,
    }, ttl=7200)

    user = db.query(User).filter(User.nickname == nickname).first()
    game = Game(
        user_id=user.id if user else None,
        title=scenario["title"],
        scenario=scenario,
        culprit_id=next(s["id"] for s in scenario["suspects"] if s.get("is_culprit")),
    )
    db.add(game)
    db.commit()

    suspects_safe = []
    for s in scenario["suspects"]:
        suspects_safe.append({
            "id": s["id"],
            "name": s["name"],
            "age": s["age"],
            "occupation": s["occupation"],
            "personality": s["personality"],
            "alibi": s["alibi"],
            "testimony": s["testimony"],
        })

    clues_safe = [{"id": c["id"], "description": c["description"], "location": c["location"]}
                  for c in scenario["clues"]]

    redis_mgr.incr_online()

    return StartGameResp(
        game_id=game_id,
        title=scenario["title"],
        setting=scenario["setting"],
        victim=scenario["victim"],
        suspects=suspects_safe,
        clues=clues_safe,
    )


@router.post("/api/game/interrogate")
def interrogate_suspect(req: InterrogateReq):
    """审问嫌疑人"""
    session = redis_mgr.get_session(req.game_id)
    if not session:
        raise HTTPException(404, "游戏会话不存在或已过期")

    scenario = session["scenario"]
    suspect = next((s for s in scenario["suspects"] if s["id"] == req.suspect_id), None)
    if not suspect:
        raise HTTPException(404, f"嫌疑人 {req.suspect_id} 不存在")

    # 检查审问轮数
    rounds = session["rounds"].get(req.suspect_id, 0)
    if rounds >= 5:
        return {"response": "（该嫌疑人已不愿再回答更多问题）", "rounds_left": 0}

    # 获取历史对话
    history = session["chat_history"].get(req.suspect_id, [])

    # Agent 回复
    answer = interrogate(suspect, scenario, req.question, history)

    # 更新会话
    history.append({"role": "player", "content": req.question})
    history.append({"role": "suspect", "content": answer})
    session["chat_history"][req.suspect_id] = history
    session["rounds"][req.suspect_id] = rounds + 1
    redis_mgr.save_session(req.game_id, session)

    return {
        "suspect_name": suspect["name"],
        "response": answer,
        "rounds_left": 5 - rounds - 1,
    }


@router.post("/api/game/search-clue")
def search_clue(req: SearchClueReq):
    """搜索线索"""
    result = clue_manager.discover_clue(req.game_id, req.query, threshold=1.5)

    if result:
        # 记录发现的线索
        session = redis_mgr.get_session(req.game_id)
        if session:
            session["clues_found"].append(result["description"])
            redis_mgr.save_session(req.game_id, session)
        return {"found": True, "clue": result["description"]}
    return {"found": False, "message": "没有找到相关线索，试试换个方向搜索"}


@router.post("/api/game/hint")
def get_hint(req: HintReq):
    """获取提示（最多10次）"""
    session = redis_mgr.get_session(req.game_id)
    if not session:
        raise HTTPException(404, "游戏会话不存在或已过期")

    hints_used = session.get("hints_used", 0)
    if hints_used >= 10:
        return {"hint": "已用完所有提示次数！", "hints_left": 0}

    # 调用提示 Agent
    hint_text = give_hint(
        scenario=session["scenario"],
        clues_found=session.get("clues_found", []),
        chat_history=session.get("chat_history", {}),
        hints_used=hints_used,
    )

    # 更新会话
    session["hints_used"] = hints_used + 1
    redis_mgr.save_session(req.game_id, session)

    return {
        "hint": hint_text,
        "hints_left": 10 - hints_used - 1,
    }


@router.post("/api/game/submit")
def submit_guess(req: SubmitGuessReq, db: Session = Depends(get_db)):
    """提交推理"""
    session = redis_mgr.get_session(req.game_id)
    if not session:
        raise HTTPException(404, "游戏会话不存在或已过期")

    scenario = session["scenario"]

    # 评判
    result = judge(scenario, req.culprit_id, req.reasoning)

    # 找到凶手名字
    culprit = next(s for s in scenario["suspects"] if s.get("is_culprit"))

    # 更新数据库
    game = db.query(Game).filter(Game.title == scenario["title"]).first()
    if game:
        game.player_guess = req.culprit_id
        game.is_correct = result.get("is_correct", False)
        game.score = result.get("score", 0)
        game.rounds_played = sum(session["rounds"].values())
        game.clues_found = len(session["clues_found"])
        game.finished_at = datetime.utcnow()
        db.commit()

    # 更新排行榜
    if result.get("is_correct"):
        redis_mgr.update_leaderboard("detective", result.get("score", 0))

    # 清理会话
    redis_mgr.delete_session(req.game_id)
    redis_mgr.decr_online()

    culprit_name = culprit["name"]
    return {
        "is_correct": result.get("is_correct", False),
        "score": result.get("score", 0),
        "culprit_name": culprit_name,
        "analysis": result.get("analysis", ""),
        "truth_reveal": result.get("truth_reveal", ""),
        "tips": result.get("tips", ""),
    }


@router.get("/api/leaderboard")
def get_leaderboard():
    """排行榜"""
    return {"rankings": redis_mgr.get_leaderboard(top_n=10)}


@router.get("/api/stats")
def get_stats():
    """在线人数等统计"""
    import random
    return {"online": random.randint(10, 100)}
