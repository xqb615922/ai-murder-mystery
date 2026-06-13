"""AI 剧本杀 - 数据库模型"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    """用户表"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String(50), unique=True, nullable=False)
    avatar = Column(String(200), default="🕵️")
    created_at = Column(DateTime, default=datetime.utcnow)
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)

    games = relationship("Game", back_populates="user")


class Game(Base):
    """游戏记录表"""
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(200))                # 剧本标题
    scenario = Column(JSON)                    # 完整剧本（死者/嫌疑人/线索/凶手）
    culprit_id = Column(String(50))            # 凶手 ID
    player_guess = Column(String(50))          # 玩家猜测
    is_correct = Column(Boolean)               # 是否猜对
    score = Column(Float, default=0)           # 得分
    rounds_played = Column(Integer, default=0) # 审问总轮数
    clues_found = Column(Integer, default=0)   # 发现线索数
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="games")


class ChatLog(Base):
    """对话记录表"""
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    game_id = Column(Integer, ForeignKey("games.id"))
    suspect_id = Column(String(50))            # 嫌疑人 ID
    role = Column(String(20))                  # player / suspect
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class Leaderboard(Base):
    """排行榜（物化视图）"""
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nickname = Column(String(50))
    total_games = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    win_rate = Column(Float, default=0)
    avg_score = Column(Float, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
