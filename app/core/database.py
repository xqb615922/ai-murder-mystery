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
    # PostgreSQL：强制使用 psycopg (v3) 驱动，禁用预编译兼容 PgBouncer
    if "postgresql" in DB_URL and "+psycopg" not in DB_URL:
        DB_URL = DB_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        DB_URL = DB_URL.replace("postgres://", "postgresql+psycopg://", 1)
    connect_args = {"prepare_threshold": None}
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
