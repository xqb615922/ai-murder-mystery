"""AI 剧本杀 - 数据库连接管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.models import Base

DB_URL = settings.effective_database_url

engine = create_engine(
    DB_URL,
    echo=settings.DEBUG,
    connect_args={"check_same_thread": False} if "sqlite" in DB_URL else {},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """建表"""
    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 依赖注入：获取数据库 session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
