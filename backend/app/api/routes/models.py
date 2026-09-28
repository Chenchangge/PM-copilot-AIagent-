"""AI 模型配置 CRUD + 连通性测试 + 能力解析 路由。

匿名用户身份：MVP 无登录，前端在 localStorage 生成匿名 user_id 后经
`X-User-Id` 请求头传入；缺省回退为 "anonymous"。
"""
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.model import (
    ModelConfigCreate,
    ModelConfigOut,
    ModelConfigUpdate,
    ResolveRequest,
    ResolveResult,
    TestConnectionResult,
)
from app.services.model_service import ModelNotFoundError, ModelService

router = APIRouter()


def get_user_id(x_user_id: str | None = Header(default=None, alias="X-User-Id")) -> str:
    return x_user_id or "anonymous"


@router.get("", response_model=list[ModelConfigOut])
def list_models(user_id: str = Depends(get_user_id), db: Session = Depends(get_db)) -> list[ModelConfigOut]:
    return ModelService(db).list_models(user_id)


@router.post("", response_model=ModelConfigOut, status_code=201)
def create_model(
    payload: ModelConfigCreate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> ModelConfigOut:
    return ModelService(db).create_model(user_id, payload)


@router.get("/{model_id}", response_model=ModelConfigOut)
def get_model(
    model_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> ModelConfigOut:
    try:
        return ModelService(db).get_model(user_id, model_id)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="模型不存在")


@router.put("/{model_id}", response_model=ModelConfigOut)
def update_model(
    model_id: int,
    payload: ModelConfigUpdate,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> ModelConfigOut:
    try:
        return ModelService(db).update_model(user_id, model_id, payload)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="模型不存在")


@router.delete("/{model_id}", status_code=204)
def delete_model(
    model_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> None:
    try:
        ModelService(db).delete_model(user_id, model_id)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="模型不存在")


@router.post("/{model_id}/test", response_model=TestConnectionResult)
def test_connection(
    model_id: int,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> TestConnectionResult:
    try:
        return ModelService(db).test_connection(user_id, model_id)
    except ModelNotFoundError:
        raise HTTPException(status_code=404, detail="模型不存在")


@router.post("/resolve", response_model=ResolveResult)
def resolve_model(
    payload: ResolveRequest,
    user_id: str = Depends(get_user_id),
    db: Session = Depends(get_db),
) -> ResolveResult:
    return ModelService(db).resolve(user_id, payload.required_capabilities)
