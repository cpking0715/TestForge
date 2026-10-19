"""API 依赖：会话、当前用户、权限校验。"""

from typing import Annotated

import jwt
from fastapi import Depends, Request
from sqlalchemy.orm import Session

from tfserver.core.response import BusinessError, fail
from tfserver.core.security import decode_access_token
from tfserver.domain.auth.captcha import CaptchaStore
from tfserver.domain.rbac import service as rbac
from tfserver.infra.db import get_db
from tfserver.infra.models import SystemUser

DbDep = Annotated[Session, Depends(get_db)]


def get_captcha_store(request: Request) -> CaptchaStore:
    return request.app.state.captcha_store


CaptchaStoreDep = Annotated[CaptchaStore, Depends(get_captcha_store)]


def get_current_user(request: Request, db: DbDep) -> SystemUser:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise _unauthorized()
    token = header.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise _unauthorized()
    user = db.get(SystemUser, user_id)
    if user is None or not user.status:
        raise _unauthorized()
    request.state.permissions = rbac.effective_permissions(db, user)
    return user


CurrentUser = Annotated[SystemUser, Depends(get_current_user)]


def require_perm(*perms: str):
    """声明式权限校验：超管（*）放行，否则需命中任一权限。"""
    def checker(request: Request, user: CurrentUser) -> SystemUser:
        granted: list[str] = getattr(request.state, "permissions", [])
        if "*" not in granted and not any(p in granted for p in perms):
            raise BusinessError("没有操作权限", code=403)
        return user
    return Depends(checker)


def _unauthorized():
    from fastapi import HTTPException

    return HTTPException(status_code=401, detail="未登录或登录已过期")
