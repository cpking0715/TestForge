"""认证接口：验证码 / 登录 / 当前用户信息 / 我的菜单。"""

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from tfserver.api.deps import CaptchaStoreDep, CurrentUser, DbDep
from tfserver.core.config import get_settings
from tfserver.core.response import ok
from tfserver.domain.auth import service as auth_service
from tfserver.domain.auth.captcha import generate_captcha
from tfserver.domain.rbac import service as rbac

router = APIRouter(prefix="/api/v1/system/auth", tags=["auth"])


class LoginBody(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)
    captcha_key: str
    captcha: str


@router.get("/captcha/get")
def get_captcha(store: CaptchaStoreDep) -> dict:
    payload = generate_captcha(store, get_settings().captcha_ttl_seconds)
    return ok(payload, msg="获取验证码成功")


@router.post("/login")
def login(body: LoginBody, db: DbDep, store: CaptchaStoreDep) -> dict:
    result = auth_service.login(
        db, store,
        username=body.username, password=body.password,
        captcha_key=body.captcha_key, captcha=body.captcha,
    )
    return ok(result, msg="登录成功")


@router.get("/me")
def me(request: Request, user: CurrentUser) -> dict:
    perms: list[str] = getattr(request.state, "permissions", [])
    return ok({
        "id": user.id,
        "username": user.username,
        "nickname": user.nickname,
        "is_super": user.is_super,
        "roles": user.role_codes,
        "permissions": perms,
    })


@router.get("/menus")
def my_menus(user: CurrentUser, db: DbDep) -> dict:
    tree = rbac.menu_tree(db)
    if user.is_super:
        return ok(tree)
    allowed = {m.id for role in user.roles if role.status for m in role.menus}
    return ok(_filter_tree(tree, allowed))


def _filter_tree(nodes: list[dict], allowed: set[int]) -> list[dict]:
    result = []
    for node in nodes:
        children = _filter_tree(node["children"], allowed)
        if node["id"] in allowed or children:
            result.append({**node, "children": children})
    return result
