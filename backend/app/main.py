"""FastAPI 应用入口。"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import interview_error_handler, learning_error_handler, rag_error_handler
from app.api.routes import health, interview, knowledge, knowledge_qa, learning, models, profile
from app.core.config import settings
from app.db.database import init_db
from app.interview.errors import InterviewError
from app.learning.errors import LearningError
from app.rag.errors import RAGError


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(RAGError, rag_error_handler)
app.add_exception_handler(InterviewError, interview_error_handler)
app.add_exception_handler(LearningError, learning_error_handler)

app.include_router(health.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(knowledge_qa.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(learning.router, prefix="/api/learning", tags=["learning"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])
app.include_router(models.router, prefix="/api/models", tags=["models"])


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "ok", "environment": settings.environment}
