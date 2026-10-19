"""认证契约测试：验证码 → 登录 → me 的闭环与失败分支。"""

from tests.conftest import admin_login, auth_header


def _login_body(client, fake_captcha, username="admin", password="admin123", captcha_override=None):
    cap = client.get("/api/v1/system/auth/captcha/get").json()["data"]
    answer = fake_captcha.data[cap["key"]][0]
    return {
        "username": username,
        "password": password,
        "captcha_key": cap["key"],
        "captcha": captcha_override if captcha_override is not None else answer,
    }


def test_login_with_captcha_disabled(monkeypatch, client):
    """内部部署关闭验证码：任意验证码可登录。"""
    from tfserver.core.config import get_settings

    monkeypatch.setattr(get_settings(), "captcha_enabled", False)
    resp = client.post("/api/v1/system/auth/login", json={
        "username": "admin", "password": "admin123",
        "captcha_key": "ignored", "captcha": "0",
    })
    assert resp.json()["code"] == 0


def test_login_success_and_me(client, fake_captcha):
    body = _login_body(client, fake_captcha)
    resp = client.post("/api/v1/system/auth/login", json=body)
    payload = resp.json()
    assert resp.status_code == 200
    assert payload["code"] == 0
    assert payload["data"]["token"]
    assert payload["data"]["user"]["username"] == "admin"

    me = client.get("/api/v1/system/auth/me", headers=auth_header(payload["data"]["token"])).json()
    assert me["code"] == 0
    assert me["data"]["is_super"] is True
    assert me["data"]["permissions"] == ["*"]


def test_login_wrong_password(client, fake_captcha):
    body = _login_body(client, fake_captcha, password="wrong-pass")
    payload = client.post("/api/v1/system/auth/login", json=body).json()
    assert payload["code"] == 1003
    assert payload["msg"] == "用户名或密码错误"


def test_login_captcha_expired(client):
    body = {
        "username": "admin", "password": "admin123",
        "captcha_key": "not-exist", "captcha": "1",
    }
    payload = client.post("/api/v1/system/auth/login", json=body).json()
    assert payload["code"] == 1001
    assert payload["msg"] == "验证码已过期"


def test_login_captcha_wrong(client, fake_captcha):
    body = _login_body(client, fake_captcha, captcha_override="0000")
    payload = client.post("/api/v1/system/auth/login", json=body).json()
    assert payload["code"] == 1002


def test_login_captcha_single_use(client, fake_captcha):
    """验证码一次性：用过一次后（即使密码错）不能再用。"""
    body = _login_body(client, fake_captcha, password="wrong-pass")
    client.post("/api/v1/system/auth/login", json=body)
    body["password"] = "admin123"
    payload = client.post("/api/v1/system/auth/login", json=body).json()
    assert payload["code"] == 1001  # key 已消费


def test_me_without_token(client):
    resp = client.get("/api/v1/system/auth/me")
    assert resp.status_code == 401
    assert resp.json()["code"] == 401


def test_me_with_garbage_token(client):
    resp = client.get("/api/v1/system/auth/me", headers=auth_header("garbage.token.value"))
    assert resp.status_code == 401


def test_captcha_get_shape(client):
    payload = client.get("/api/v1/system/auth/captcha/get").json()
    assert payload["code"] == 0
    assert set(payload["data"].keys()) == {"key", "img_base"}


def test_admin_seeded_once(client, fake_captcha):
    token = admin_login(client, fake_captcha)
    users = client.get(
        "/api/v1/system/user/list", headers=auth_header(token)
    ).json()["data"]
    assert users["total"] == 1
    assert users["items"][0]["username"] == "admin"
