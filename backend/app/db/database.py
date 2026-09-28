"""SQLite 数据库连接、会话与初始化。"""
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 跨线程
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """所有 ORM 模型的基类。"""


def get_db():
    """FastAPI 依赖：请求级数据库会话。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """创建所有表（幂等）。需在模型已导入后调用。"""
    from app import models  # noqa: F401  # 确保模型注册到 Base.metadata

    Base.metadata.create_all(bind=engine)

    # 幂等写入分类体系初始配置（Step 12-3 Part A）+ 面试题↔知识点关系
    from app.learning.seed import seed_question_knowledge, seed_taxonomy

    db = SessionLocal()
    try:
        seed_taxonomy(db)
        seed_question_knowledge(db)
    finally:
        db.close()
