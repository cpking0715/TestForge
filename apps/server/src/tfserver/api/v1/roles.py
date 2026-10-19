"""角色管理接口。"""

from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tfserver.api.deps import DbDep, require_perm
from tfserver.core.response import ok
from tfserver.domain.rbac import service as rbac

router = APIRouter(prefix="/api/v1/system/role", tags=["system-role"])


class RoleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    code: str = Field(min_length=1, max_length=64)
    remark: str = ""
    menu_ids: list[int] = []


class RoleUpdate(BaseModel):
    name: str | None = None
    remark: str | None = None
    status: bool | None = None
    menu_ids: list[int] | None = None


@router.get("/list")
def list_roles(db: DbDep, _: Annotated[object, require_perm("system:role:list")]) -> dict:
    return ok(rbac.list_roles(db))


@router.post("/create")
def create_role(body: RoleCreate, db: DbDep,
                _: Annotated[object, require_perm("system:role:create")]) -> dict:
    return ok(rbac.create_role(
        db, name=body.name, code=body.code, remark=body.remark, menu_ids=body.menu_ids,
    ), msg="创建成功")


@router.post("/update/{role_id}")
def update_role(role_id: int, body: RoleUpdate, db: DbDep,
                _: Annotated[object, require_perm("system:role:update")]) -> dict:
    rbac.update_role(
        db, role_id, name=body.name, remark=body.remark,
        status=body.status, menu_ids=body.menu_ids,
    )
    return ok(msg="更新成功")


@router.post("/delete/{role_id}")
def delete_role(role_id: int, db: DbDep,
                _: Annotated[object, require_perm("system:role:delete")]) -> dict:
    rbac.delete_role(db, role_id)
    return ok(msg="删除成功")
