"""AI 剧本杀 - 配置管理"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 应用
    APP_NAME: str = "AI 剧本杀"
    DEBUG: bool = True

    # LLM（阿里百炼）
    DASHSCOPE_API_KEY: str = ""
    LLM_BASE_URL: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen3.6-plus"

    # 数据库（Supabase / 本地）
    DATABASE_URL: str = "sqlite:///./murder_mystery.db"

    # Redis（Upstash / 本地）
    REDIS_URL: str = ""

    # ChromaDB
    CHROMA_PERSIST_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "chroma_data")

    # 游戏配置
    MAX_ROUNDS: int = 5          # 每个嫌疑人最多审问轮数
    SUSPECT_COUNT: int = 4       # 嫌疑人数量
    CLUE_COUNT: int = 6          # 线索数量

    class Config:
        env_file = ".env"


settings = Settings()
