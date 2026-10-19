"""端到端冒烟：拉验证码 → 模板匹配识别（确定性，不依赖视觉模型）→ 登录 → /me。

用法：uv run python scripts/smoke_login.py [base_url]
默认 http://localhost:8900，账号 admin/admin123（种子数据）。
"""

import base64
import io
import sys

import httpx
from PIL import Image, ImageDraw, ImageFont

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8900"
CHARS = "0123456789+-=?"
BAND_W, START_X = 22, 14


def dark_pixels(img: Image.Image, x0: int, x1: int) -> set[tuple[int, int]]:
    """区域内的深色像素（文字色 35,60,90；噪声线/点均 >120 不会命中）。"""
    px = img.load()
    return {
        (x - x0, y)
        for x in range(x0, min(x1, img.width))
        for y in range(img.height)
        if all(c < 120 for c in px[x, y][:3])
    }


def render_char(ch: str) -> set[tuple[int, int]]:
    canvas = Image.new("RGB", (BAND_W + 8, 48), (255, 255, 255))
    ImageDraw.Draw(canvas).text((2, 7), ch, fill=(0, 0, 0), font=ImageFont.load_default(size=30))
    return {(x, y) for x in range(canvas.width) for y in range(canvas.height)
            if all(c < 120 for c in canvas.load()[x, y][:3])}


GLYPHS = {c: render_char(c) for c in CHARS}


def match_band(band: set[tuple[int, int]]) -> tuple[str, float]:
    best, best_score = "?", -1.0
    for ch, glyph in GLYPHS.items():
        for dx in range(-4, 5):
            for dy in range(-4, 5):
                shifted = {(x + dx, y + dy) for x, y in glyph}
                # Jaccard：惩罚 band 中未被字形覆盖的墨迹，避免 '-' 匹配 '=' 拿满分
                score = len(shifted & band) / len(shifted | band)
                if score > best_score:
                    best_score, best = score, ch
    return best, best_score


def recognize(img: Image.Image) -> str:
    # 找出有文字墨迹的列区间 → 按带宽切 band（渲染时字符固定步进 22，起点 14）
    cols = sorted({x for x in range(img.width) for y in range(img.height)
                   if all(c < 120 for c in img.load()[x, y][:3])})
    if not cols:
        return ""
    left, right = cols[0], cols[-1]
    n_bands = round((right - START_X) / BAND_W) + 1
    chars = []
    for i in range(n_bands):
        band = dark_pixels(img, START_X + i * BAND_W, START_X + (i + 1) * BAND_W)
        ch, score = match_band(band)
        if score < 0.3:
            break
        chars.append(ch)
        if ch == "?":
            break
    return "".join(chars)


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=10) as client:
        cap = client.get("/api/v1/system/auth/captcha/get").json()["data"]
        raw = base64.b64decode(cap["img_base"].split(",", 1)[1])
        expression = recognize(Image.open(io.BytesIO(raw)))
        assert expression.endswith("=?"), f"识别失败：{expression!r}"
        answer = str(eval(expression[:-2]))  # noqa: S307 仅冒烟脚本，输入受控

        login = client.post("/api/v1/system/auth/login", json={
            "username": "admin", "password": "admin123",
            "captcha_key": cap["key"], "captcha": answer,
        }).json()
        assert login["code"] == 0, f"登录失败：{login}"
        token = login["data"]["token"]

        me = client.get("/api/v1/system/auth/me",
                        headers={"Authorization": f"Bearer {token}"}).json()
        assert me["code"] == 0 and me["data"]["username"] == "admin", me

        menus = client.get("/api/v1/system/auth/menus",
                           headers={"Authorization": f"Bearer {token}"}).json()
        assert menus["code"] == 0 and len(menus["data"]) >= 2, menus

        print(f"冒烟通过：验证码[{expression}]→{answer}，登录成功，用户 {me['data']['username']}，"
              f"菜单 {len(menus['data'])} 组")


if __name__ == "__main__":
    main()
