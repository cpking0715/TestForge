"""测试基建：内存 SQLite + 隔离 app + 可控验证码存储。

约定：conftest 在 import tfserver 之前设置环境变量，
确保引擎/配置按测试环境构建（内存库 + 固定密钥）。
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-0123456789abcdef0123456789")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from tfserver.domain.auth.captcha import CaptchaStore  # noqa: E402
from tfserver.infra import models  # noqa: F401,E402  注册表模型
from tfserver.infra.db import Base, engine  # noqa: E402
from tfserver.main import create_app  # noqa: E402


class FakeCaptchaStore(CaptchaStore):
    """可控验证码存储：测试可直接读出答案、手工制造过期。"""

    def __init__(self) -> None:
        self.data: dict[str, tuple[str, int]] = {}

    def save(self, key: str, answer: str, ttl_seconds: int) -> None:
        self.data[key] = (answer, ttl_seconds)

    def pop(self, key: str) -> str | None:
        item = self.data.pop(key, None)
        return item[0] if item else None


@pytest.fixture()
def fake_captcha() -> FakeCaptchaStore:
    return FakeCaptchaStore()


@pytest.fixture()
def client(fake_captcha: FakeCaptchaStore):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app = create_app()
    app.state.captcha_store = fake_captcha
    with TestClient(app) as c:
        yield c


def admin_login(client: TestClient, fake_captcha: FakeCaptchaStore,
                username: str = "admin", password: str = "admin123") -> str:
    """契约测试辅助：走真实验证码流程拿 token。"""
    cap = client.get("/api/v1/system/auth/captcha/get").json()["data"]
    answer = fake_captcha.data[cap["key"]][0]
    body = {
        "username": username,
        "password": password,
        "captcha_key": cap["key"],
        "captcha": answer,
    }
    resp = client.post("/api/v1/system/auth/login", json=body)
    assert resp.json()["code"] == 0, resp.text
    return resp.json()["data"]["token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
