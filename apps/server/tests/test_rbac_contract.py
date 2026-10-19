"""RBAC 契约测试：用户/角色/菜单 CRUD、权限校验、菜单树防护。"""

from tests.conftest import admin_login, auth_header


def test_user_crud_lifecycle(client, fake_captcha):
    token = admin_login(client, fake_captcha)
    headers = auth_header(token)

    created = client.post("/api/v1/system/user/create", headers=headers, json={
        "username": "tester", "password": "test1234",
        "nickname": "测试员", "role_ids": [2],  # 2=普通用户（种子）
    }).json()
    assert created["code"] == 0

    listed = client.get("/api/v1/system/user/list", headers=headers).json()["data"]
    assert listed["total"] == 2
    tester = next(u for u in listed["items"] if u["username"] == "tester")
    assert tester["roles"][0]["name"] == "普通用户"

    updated = client.post(f"/api/v1/system/user/update/{tester['id']}",
                          headers=headers, json={"nickname": "测试员2", "status": False})
    assert updated.json()["code"] == 0

    deleted = client.post(f"/api/v1/system/user/delete/{tester['id']}", headers=headers)
    assert deleted.json()["code"] == 0
    assert client.get("/api/v1/system/user/list", headers=headers).json()["data"]["total"] == 1


def test_duplicate_username_rejected(client, fake_captcha):
    token = admin_login(client, fake_captcha)
    resp = client.post("/api/v1/system/user/create", headers=auth_header(token), json={
        "username": "admin", "password": "whatever123",
    })
    assert resp.json()["code"] == -1
    assert "已存在" in resp.json()["msg"]


def test_super_admin_delete_forbidden(client, fake_captcha):
    token = admin_login(client, fake_captcha)
    resp = client.post("/api/v1/system/user/delete/1", headers=auth_header(token))
    assert resp.json()["code"] == -1


def test_password_reset_allows_new_login(client, fake_captcha):
    token = admin_login(client, fake_captcha)
    headers = auth_header(token)
    client.post("/api/v1/system/user/create", headers=headers, json={
        "username": "tester2", "password": "oldpass123",
    })
    user_id = client.get("/api/v1/system/user/list?keyword=tester2", headers=headers).json()["data"]["items"][0]["id"]
    client.post(f"/api/v1/system/user/reset-password/{user_id}", headers=headers,
                json={"password": "newpass456"})

    cap = client.get("/api/v1/system/auth/captcha/get").json()["data"]
    body = {"username": "tester2", "password": "newpass456",
            "captcha_key": cap["key"], "captcha": fake_captcha.data[cap["key"]][0]}
    resp = client.post("/api/v1/system/auth/login", json=body).json()
    assert resp["code"] == 0


def test_common_user_denied_system_api(client, fake_captcha):
    """普通用户（无 system:user 权限）访问用户列表 → code 403。"""
    headers_admin = auth_header(admin_login(client, fake_captcha))
    client.post("/api/v1/system/user/create", headers=headers_admin, json={
        "username": "viewer", "password": "view12345", "role_ids": [2],
    })
    cap = client.get("/api/v1/system/auth/captcha/get").json()["data"]
    login = client.post("/api/v1/system/auth/login", json={
        "username": "viewer", "password": "view12345",
        "captcha_key": cap["key"], "captcha": fake_captcha.data[cap["key"]][0],
    }).json()["data"]

    resp = client.get("/api/v1/system/user/list", headers=auth_header(login["token"]))
    assert resp.json()["code"] == 403

    menus = client.get("/api/v1/system/auth/menus", headers=auth_header(login["token"])).json()["data"]
    assert [m["name"] for m in menus] == ["控制台"]  # 只有 dashboard


def test_menu_tree_cycle_guard(client, fake_captcha):
    headers = auth_header(admin_login(client, fake_captcha))
    dir_id = client.post("/api/v1/system/menu/create", headers=headers, json={
        "name": "测试目录", "type": "dir", "path": "/t",
    }).json()["data"]["id"]
    child_id = client.post("/api/v1/system/menu/create", headers=headers, json={
        "name": "子页", "type": "page", "parent_id": dir_id, "path": "/t/c",
    }).json()["data"]["id"]

    # 父指向自身
    resp = client.post(f"/api/v1/system/menu/update/{dir_id}", headers=headers,
                       json={"parent_id": dir_id})
    assert resp.json()["code"] == -1
    assert "自身" in resp.json()["msg"]

    # 父指向后代（环路）
    resp = client.post(f"/api/v1/system/menu/update/{dir_id}", headers=headers,
                       json={"parent_id": child_id})
    assert resp.json()["code"] == -1

    # 有子菜单不可删
    resp = client.post(f"/api/v1/system/menu/delete/{dir_id}", headers=headers)
    assert resp.json()["code"] == -1

    # 删子后可删父
    assert client.post(f"/api/v1/system/menu/delete/{child_id}", headers=headers).json()["code"] == 0
    assert client.post(f"/api/v1/system/menu/delete/{dir_id}", headers=headers).json()["code"] == 0


def test_menu_tree_shape(client, fake_captcha):
    headers = auth_header(admin_login(client, fake_captcha))
    tree = client.get("/api/v1/system/menu/tree", headers=headers).json()["data"]
    names = {n["name"] for n in tree}
    assert {"控制台", "系统管理"} <= names
    dash = next(n for n in tree if n["name"] == "控制台")
    assert dash["path"] == "/"
    sys_dir = next(n for n in tree if n["name"] == "系统管理")
    assert {c["name"] for c in sys_dir["children"]} == {"用户管理", "角色管理", "菜单管理"}


def test_role_crud_and_builtin_protection(client, fake_captcha):
    headers = auth_header(admin_login(client, fake_captcha))
    created = client.post("/api/v1/system/role/create", headers=headers, json={
        "name": "测试工程师", "code": "qa", "remark": "读写用例", "menu_ids": [1],
    }).json()
    assert created["code"] == 0

    roles = client.get("/api/v1/system/role/list", headers=headers).json()["data"]
    assert len(roles) == 3

    role_id = created["data"]["id"]
    assert client.post(f"/api/v1/system/role/update/{role_id}", headers=headers,
                       json={"menu_ids": [1, 2]}).json()["code"] == 0
    assert client.post(f"/api/v1/system/role/delete/{role_id}", headers=headers).json()["code"] == 0

    # 内置角色不可删
    super_role_id = next(r["id"] for r in
                         client.get("/api/v1/system/role/list", headers=headers).json()["data"]
                         if r["code"] == "super_admin")
    resp = client.post(f"/api/v1/system/role/delete/{super_role_id}", headers=headers)
    assert resp.json()["code"] == -1


def test_invalid_role_reference_rejected(client, fake_captcha):
    headers = auth_header(admin_login(client, fake_captcha))
    resp = client.post("/api/v1/system/user/create", headers=headers, json={
        "username": "badref", "password": "badref123", "role_ids": [999],
    })
    assert resp.json()["code"] == -1
    assert "角色" in resp.json()["msg"]
