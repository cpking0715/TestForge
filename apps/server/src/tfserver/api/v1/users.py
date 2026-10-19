"""用户管理接口。"""

from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tfserver.api.deps import DbDep, require_perm
from tfserver.core.response import ok
from tfserver.domain.rbac import service as rbac

router = APIRouter(prefix="/api/v1/system/user", tags=["system-user"])


class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=64)
    password: str = Field(min_length=6, max_length=128)
    nickname: str = ""
    email: str = ""
    role_ids: list[int] = []


class UserUpdate(BaseModel):
    nickname: str | None = None
    email: str | None = None
    status: bool | None = None
    role_ids: list[int] | None = None


class PasswordReset(BaseModel):
    password: str = Field(min_length=6, max_length=128)


@router.get("/list")
def list_users(
    db: DbDep,
    _: Annotated[object, require_perm("system:user:list")],
    keyword: str = "",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    return ok(rbac.list_users(db, keyword=keyword, page=page, page_size=page_size))


@router.post("/create")
def create_user(body: UserCreate, db: DbDep, _: Annotated[object, require_perm("system:user:create")]) -> dict:
    return ok(rbac.create_user(
        db, username=body.username, password=body.password,
        nickname=body.nickname, email=body.email, role_ids=body.role_ids,
    ), msg="创建成功")


@router.post("/update/{user_id}")
def update_user(user_id: int, body: UserUpdate, db: DbDep,
                _: Annotated[object, require_perm("system:user:update")]) -> dict:
    rbac.update_user(
        db, user_id,
        nickname=body.nickname, email=body.email,
        status=body.status, role_ids=body.role_ids,
    )
    return ok(msg="更新成功")


@router.post("/delete/{user_id}")
def delete_user(user_id: int, db: DbDep, _: Annotated[object, require_perm("system:user:delete")]) -> dict:
    rbac.delete_user(db, user_id)
    return ok(msg="删除成功")


@router.post("/reset-password/{user_id}")
def reset_password(user_id: int, body: PasswordReset, db: DbDep,
                   _: Annotated[object, require_perm("system:user:update")]) -> dict:
    rbac.reset_password(db, user_id, body.password)
    return ok(msg="密码已重置")
