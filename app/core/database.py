"""AI 剧本杀 - 数据库连接管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.models import Base

DB_URL = settings.effective_database_url

# 连接参数：SQLite / PostgreSQL 分别配置
if "sqlite" in DB_URL:
    connect_args = {"check_same_thread": False}
    pool_kwargs = {}
else:
    # Supabase Transaction mode (pooler 6543) 需要
    connect_args = {"prepared_statement": False, "statement_cache_size": 0}
    pool_kwargs = {
        "pool_size": 5,
        "max_overflow": 5,
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

engine = create_engine(
    DB_URL,
    echo=settings.DEBUG,
    connect_args=connect_args,
    **pool_kwargs,
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
