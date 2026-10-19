"""算术验证码：生成/校验/一次性消费（领域层，不依赖 FastAPI）。

存储端口 CaptchaStore 用 Protocol 定义；当前默认内存实现，
P6 换 Redis 时提供新实现即可，领域代码不动。
"""

import base64
import io
import random
import threading
import time
from typing import Protocol, TypedDict

from PIL import Image, ImageDraw, ImageFont

from tfserver.core.response import BusinessError


class CaptchaPayload(TypedDict):
    key: str
    img_base: str  # data:image/png;base64,...


class CaptchaStore(Protocol):
    def save(self, key: str, answer: str, ttl_seconds: int) -> None: ...
    def pop(self, key: str) -> str | None: ...  # 取出并消费；不存在/过期返回 None


class InMemoryCaptchaStore:
    """线程安全的内存存储：key -> (answer, expires_at)。"""

    def __init__(self) -> None:
        self._data: dict[str, tuple[str, float]] = {}
        self._lock = threading.Lock()

    def save(self, key: str, answer: str, ttl_seconds: int) -> None:
        with self._lock:
            self._purge()
            self._data[key] = (answer, time.monotonic() + ttl_seconds)

    def pop(self, key: str) -> str | None:
        with self._lock:
            item = self._data.pop(key, None)
            if item is None:
                return None
            answer, expires_at = item
            if time.monotonic() > expires_at:
                return None
            return answer

    def _purge(self) -> None:
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._data.items() if exp < now]
        for k in expired:
            del self._data[k]


# 全局单例；测试通过重新赋值或直接构造替换
captcha_store: CaptchaStore = InMemoryCaptchaStore()


def _draw_expression() -> tuple[str, str]:
    """随机算术题，返回 (表达式文本, 答案文本)。"""
    a, b = random.randint(1, 20), random.randint(1, 20)
    if random.choice("+-") == "+":
        return f"{a}+{b}=?", str(a + b)
    if a < b:
        a, b = b, a
    return f"{a}-{b}=?", str(a - b)


def _render_png(expression: str) -> str:
    width, height = 160, 48
    image = Image.new("RGB", (width, height), (245, 248, 250))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.load_default(size=30)
    except TypeError:  # 旧版 Pillow 无 size 参数
        font = ImageFont.load_default()
    # 干扰线与噪点
    for _ in range(6):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line((x1, y1, x2, y2), fill=(180, 190, 200), width=1)
    for _ in range(120):
        draw.point((random.randint(0, width - 1), random.randint(0, height - 1)), fill=(150, 160, 175))
    # 逐字符轻微错位
    x = 14
    for ch in expression:
        y = random.randint(-3, 3) + (height - 34) // 2
        draw.text((x, max(0, y)), ch, fill=(35, 60, 90), font=font)
        x += 22
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def generate_captcha(store: CaptchaStore, ttl_seconds: int) -> CaptchaPayload:
    expression, answer = _draw_expression()
    key = f"{time.time_ns():x}{random.randbytes(8).hex()}"
    store.save(key, answer, ttl_seconds)
    return CaptchaPayload(key=key, img_base=_render_png(expression))


def verify_captcha(store: CaptchaStore, key: str, answer: str) -> None:
    """校验并消费；失败抛 BusinessError（区分过期与错误）。"""
    expected = store.pop(key)
    if expected is None:
        raise BusinessError("验证码已过期", code=1001)
    if expected != (answer or "").strip():
        raise BusinessError("验证码错误", code=1002)
