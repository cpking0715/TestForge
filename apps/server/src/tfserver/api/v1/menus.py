"""菜单管理接口。"""

from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from tfserver.api.deps import DbDep, require_perm
from tfserver.core.response import ok
from tfserver.domain.rbac import service as rbac

router = APIRouter(prefix="/api/v1/system/menu", tags=["system-menu"])


class MenuCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    parent_id: int | None = None
    type: str = Field(default="page", pattern="^(dir|page|button)$")
    path: str = ""
    permission: str = ""
    icon: str = ""
    sort: int = 0


class MenuUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None
    path: str | None = None
    permission: str | None = None
    sort: int | None = None
    visible: bool | None = None


@router.get("/tree")
def menu_tree(db: DbDep, _: Annotated[object, require_perm("system:menu:list")]) -> dict:
    return ok(rbac.menu_tree(db))


@router.post("/create")
def create_menu(body: MenuCreate, db: DbDep,
                _: Annotated[object, require_perm("system:menu:create")]) -> dict:
    return ok(rbac.create_menu(
        db, name=body.name, parent_id=body.parent_id, type_=body.type,
        path=body.path, permission=body.permission, icon=body.icon, sort=body.sort,
    ), msg="创建成功")


@router.post("/update/{menu_id}")
def update_menu(menu_id: int, body: MenuUpdate, db: DbDep,
                _: Annotated[object, require_perm("system:menu:update")]) -> dict:
    rbac.update_menu(
        db, menu_id, name=body.name, parent_id=body.parent_id,
        path=body.path, permission=body.permission, sort=body.sort, visible=body.visible,
    )
    return ok(msg="更新成功")


@router.post("/delete/{menu_id}")
def delete_menu(menu_id: int, db: DbDep,
                _: Annotated[object, require_perm("system:menu:delete")]) -> dict:
    rbac.delete_menu(db, menu_id)
    return ok(msg="删除成功")
