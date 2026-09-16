"""FastAPI 应用入口。"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, interview, knowledge, profile
from app.core.config import settings

app = FastAPI(title=settings.app_name, version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["knowledge"])
app.include_router(interview.router, prefix="/api/interview", tags=["interview"])
app.include_router(profile.router, prefix="/api/profile", tags=["profile"])


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "status": "ok", "environment": settings.environment}
