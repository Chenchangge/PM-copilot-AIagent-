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


def _ensure_interview_evaluation_columns() -> None:
    """给旧 SQLite 库补 P0-3 新增列（create_all 不会 ALTER 已存在的表）。

    幂等：先读 PRAGMA table_info，缺列才 ADD COLUMN；重复执行无副作用。
    """
    if engine.dialect.name != "sqlite":
        return
    with engine.begin() as conn:
        rows = conn.exec_driver_sql("PRAGMA table_info(interview_evaluations)").fetchall()
        columns = {row[1] for row in rows}
        if "turn_reviews" not in columns:
            conn.exec_driver_sql(
                "ALTER TABLE interview_evaluations ADD COLUMN turn_reviews JSON"
            )


def init_db() -> None:
    """创建所有表（幂等）。需在模型已导入后调用。"""
    from app import models  # noqa: F401  # 确保模型注册到 Base.metadata

    Base.metadata.create_all(bind=engine)
    _ensure_interview_evaluation_columns()

    # 幂等写入分类体系初始配置（Step 12-3 Part A）+ 面试题↔知识点关系
    from app.learning.seed import seed_question_knowledge, seed_taxonomy

    db = SessionLocal()
    try:
        seed_taxonomy(db)
        seed_question_knowledge(db)
    finally:
        db.close()
