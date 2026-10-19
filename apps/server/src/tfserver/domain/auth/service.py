"""登录领域服务：验证码校验 + 账号密码 + 签发 JWT。"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from tfserver.core.config import get_settings
from tfserver.core.response import BusinessError
from tfserver.core.security import create_access_token, verify_password
from tfserver.domain.auth.captcha import CaptchaStore, verify_captcha
from tfserver.infra.models import SystemUser


def get_user_by_username(db: Session, username: str) -> SystemUser | None:
    return db.scalar(select(SystemUser).where(SystemUser.username == username))


def login(
    db: Session,
    store: CaptchaStore,
    *,
    username: str,
    password: str,
    captcha_key: str,
    captcha: str,
) -> dict:
    """成功返回 {token, user}；失败抛 BusinessError。"""
    if get_settings().captcha_enabled:
        verify_captcha(store, captcha_key, captcha)  # 先消费验证码，防重放

    user = get_user_by_username(db, username)
    if user is None or not verify_password(password, user.password_hash):
        raise BusinessError("用户名或密码错误", code=1003)
    if not user.status:
        raise BusinessError("账号已停用", code=1004)

    token = create_access_token(user.id, is_super=user.is_super)
    return {
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "nickname": user.nickname,
            "is_super": user.is_super,
            "roles": user.role_codes,
        },
    }
