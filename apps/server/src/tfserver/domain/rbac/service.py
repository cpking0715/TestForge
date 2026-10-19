"""RBAC 领域服务：用户/角色/菜单 + 权限集合 + 种子数据。"""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tfserver.core.response import BusinessError
from tfserver.core.security import hash_password
from tfserver.infra.models import Menu, Role, SystemUser


# ---------- 用户 ----------

def list_users(db: Session, *, keyword: str = "", page: int = 1, page_size: int = 20) -> dict:
    stmt = select(SystemUser).order_by(SystemUser.id)
    if keyword:
        stmt = stmt.where(SystemUser.username.contains(keyword) | SystemUser.nickname.contains(keyword))
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(stmt.offset((page - 1) * page_size).limit(page_size)).scalars().all()
    return {
        "total": total,
        "items": [
            {
                "id": u.id,
                "username": u.username,
                "nickname": u.nickname,
                "email": u.email,
                "status": u.status,
                "is_super": u.is_super,
                "roles": [{"id": r.id, "name": r.name} for r in u.roles],
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in rows
        ],
    }


def create_user(
    db: Session, *, username: str, password: str, nickname: str = "", email: str = "",
    role_ids: list[int] | None = None,
) -> dict:
    if get_user_by_username(db, username):
        raise BusinessError(f"用户名 {username} 已存在")
    user = SystemUser(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname or username,
        email=email,
        roles=_load_roles(db, role_ids or []),
    )
    db.add(user)
    db.flush()
    return {"id": user.id, "username": user.username}


def get_user_by_username(db: Session, username: str) -> SystemUser | None:
    return db.scalar(select(SystemUser).where(SystemUser.username == username))


def update_user(
    db: Session, user_id: int, *, nickname: str | None = None, email: str | None = None,
    status: bool | None = None, role_ids: list[int] | None = None,
) -> None:
    user = db.get(SystemUser, user_id)
    if user is None:
        raise BusinessError("用户不存在")
    if nickname is not None:
        user.nickname = nickname
    if email is not None:
        user.email = email
    if status is not None:
        user.status = status
    if role_ids is not None:
        user.roles = _load_roles(db, role_ids)


def delete_user(db: Session, user_id: int) -> None:
    user = db.get(SystemUser, user_id)
    if user is None:
        raise BusinessError("用户不存在")
    if user.is_super:
        raise BusinessError("超级管理员不可删除")
    db.delete(user)


def reset_password(db: Session, user_id: int, new_password: str) -> None:
    user = db.get(SystemUser, user_id)
    if user is None:
        raise BusinessError("用户不存在")
    user.password_hash = hash_password(new_password)


# ---------- 角色 ----------

def list_roles(db: Session) -> list[dict]:
    roles = db.execute(select(Role).order_by(Role.id)).scalars().all()
    return [
        {"id": r.id, "name": r.name, "code": r.code, "remark": r.remark,
         "status": r.status, "menu_ids": [m.id for m in r.menus]}
        for r in roles
    ]


def create_role(db: Session, *, name: str, code: str, remark: str = "",
                menu_ids: list[int] | None = None) -> dict:
    if db.scalar(select(Role).where((Role.name == name) | (Role.code == code))):
        raise BusinessError("角色名或编码已存在")
    role = Role(name=name, code=code, remark=remark, menus=_load_menus(db, menu_ids or []))
    db.add(role)
    db.flush()
    return {"id": role.id, "name": role.name}


def update_role(db: Session, role_id: int, *, name: str | None = None, remark: str | None = None,
                status: bool | None = None, menu_ids: list[int] | None = None) -> None:
    role = db.get(Role, role_id)
    if role is None:
        raise BusinessError("角色不存在")
    if name is not None:
        role.name = name
    if remark is not None:
        role.remark = remark
    if status is not None:
        role.status = status
    if menu_ids is not None:
        role.menus = _load_menus(db, menu_ids)


def delete_role(db: Session, role_id: int) -> None:
    role = db.get(Role, role_id)
    if role is None:
        raise BusinessError("角色不存在")
    if role.code == "super_admin":
        raise BusinessError("内置超级管理员角色不可删除")
    db.delete(role)


def _load_roles(db: Session, role_ids: list[int]) -> list[Role]:
    roles = [db.get(Role, rid) for rid in role_ids]
    if any(r is None for r in roles):
        raise BusinessError("存在无效的角色 ID")
    return [r for r in roles if r]


def _load_menus(db: Session, menu_ids: list[int]) -> list[Menu]:
    menus = [db.get(Menu, mid) for mid in menu_ids]
    if any(m is None for m in menus):
        raise BusinessError("存在无效的菜单 ID")
    return [m for m in menus if m]


# ---------- 菜单 ----------

def menu_tree(db: Session) -> list[dict]:
    menus = db.execute(select(Menu).order_by(Menu.sort, Menu.id)).scalars().all()
    by_id = {m.id: _menu_dto(m) for m in menus}
    roots: list[dict] = []
    for m in menus:
        dto = by_id[m.id]
        if m.parent_id and m.parent_id in by_id:
            by_id[m.parent_id]["children"].append(dto)
        else:
            roots.append(dto)
    return roots


def create_menu(db: Session, *, name: str, parent_id: int | None = None, type_: str = "page",
                path: str = "", permission: str = "", icon: str = "", sort: int = 0) -> dict:
    _ensure_parent_valid(db, parent_id, exclude_id=None)
    menu = Menu(name=name, parent_id=parent_id, type=type_, path=path,
                permission=permission, icon=icon, sort=sort)
    db.add(menu)
    db.flush()
    return {"id": menu.id, "name": menu.name}


def update_menu(db: Session, menu_id: int, *, name: str | None = None,
                parent_id: int | None = None, path: str | None = None,
                permission: str | None = None, sort: int | None = None,
                visible: bool | None = None) -> None:
    menu = db.get(Menu, menu_id)
    if menu is None:
        raise BusinessError("菜单不存在")
    if name is not None:
        menu.name = name
    if path is not None:
        menu.path = path
    if permission is not None:
        menu.permission = permission
    if sort is not None:
        menu.sort = sort
    if visible is not None:
        menu.visible = visible
    if parent_id is not None:
        if parent_id == menu_id:
            raise BusinessError("父菜单不能是自身")
        _ensure_parent_valid(db, parent_id, exclude_id=menu_id)


def delete_menu(db: Session, menu_id: int) -> None:
    menu = db.get(Menu, menu_id)
    if menu is None:
        raise BusinessError("菜单不存在")
    children = db.execute(select(Menu).where(Menu.parent_id == menu_id)).scalars().all()
    if children:
        raise BusinessError("存在子菜单，先删除子菜单")
    db.delete(menu)


def _ensure_parent_valid(db: Session, parent_id: int | None, *, exclude_id: int | None) -> None:
    """环路防护：parent 链不得经过自身。"""
    if parent_id is None:
        return
    seen: set[int] = set()
    cursor: int | None = parent_id
    while cursor is not None:
        if cursor in seen or cursor == exclude_id:
            raise BusinessError("父菜单设置非法（环路）")
        seen.add(cursor)
        parent = db.get(Menu, cursor)
        if parent is None:
            raise BusinessError("父菜单不存在")
        cursor = parent.parent_id


def _menu_dto(m: Menu) -> dict:
    return {
        "id": m.id, "parent_id": m.parent_id, "name": m.name, "type": m.type,
        "path": m.path, "permission": m.permission, "icon": m.icon,
        "sort": m.sort, "visible": m.visible, "children": [],
    }


# ---------- 权限 ----------

def effective_permissions(db: Session, user: SystemUser) -> list[str]:
    """超管返回 *；否则角色关联菜单的 permission 并集。"""
    if user.is_super:
        return ["*"]
    perms: set[str] = set()
    for role in user.roles:
        if role.status:
            perms.update(m.permission for m in role.menus if m.permission)
    return sorted(perms)


# ---------- 种子 ----------

def seed_if_empty(db: Session) -> None:
    """首次启动初始化：超管 + 默认角色 + 基础菜单。幂等。"""
    if db.scalar(select(func.count()).select_from(SystemUser)):
        return
    super_role = Role(name="超级管理员", code="super_admin", remark="内置角色，拥有全部权限")
    user_role = Role(name="普通用户", code="common", remark="默认只读角色")
    db.add_all([super_role, user_role])

    dash = Menu(name="控制台", type="page", path="/", permission="dashboard:view", sort=1)
    sys_dir = Menu(name="系统管理", type="dir", path="/system", sort=2)
    db.add_all([dash, sys_dir])
    db.flush()
    pages = [
        Menu(name="用户管理", type="page", parent_id=sys_dir.id, path="/system/user",
             permission="system:user:list", sort=1),
        Menu(name="角色管理", type="page", parent_id=sys_dir.id, path="/system/role",
             permission="system:role:list", sort=2),
        Menu(name="菜单管理", type="page", parent_id=sys_dir.id, path="/system/menu",
             permission="system:menu:list", sort=3),
    ]
    db.add_all(pages)
    db.flush()
    user_role.menus = [dash]
    db.add(SystemUser(
        username="admin",
        password_hash=hash_password("admin123"),
        nickname="管理员",
        is_super=True,
        roles=[super_role],
    ))
    db.flush()
