"""SQLite 数据库连接（占位，暂未定义模型）。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 跨线程
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
