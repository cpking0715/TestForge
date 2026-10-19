"""验证码领域测试：生成、校验、一次性消费、TTL。"""

import pytest

from tfserver.core.response import BusinessError
from tfserver.domain.auth.captcha import (
    InMemoryCaptchaStore,
    generate_captcha,
    verify_captcha,
)


def test_generate_returns_key_and_png():
    store = InMemoryCaptchaStore()
    payload = generate_captcha(store, ttl_seconds=60)
    assert payload["key"]
    assert payload["img_base"].startswith("data:image/png;base64,")
    assert len(payload["img_base"]) > 100


def test_verify_success_then_consumed():
    store = InMemoryCaptchaStore()
    payload = generate_captcha(store, ttl_seconds=60)
    key = payload["key"]
    answer = store.pop(key)  # 领域层只暴露 verify；测试从存储读答案再塞回
    store.save(key, answer, ttl_seconds=60)
    verify_captcha(store, key, answer)  # 第一次成功
    store.save(key, answer, ttl_seconds=60)
    with pytest.raises(BusinessError) as e:
        store.pop(key)
        verify_captcha(store, key, answer)  # key 已被消费
    assert e.value.msg == "验证码已过期"


def test_verify_wrong_answer():
    store = InMemoryCaptchaStore()
    store.save("k1", "12", ttl_seconds=60)
    with pytest.raises(BusinessError) as e:
        verify_captcha(store, "k1", "13")
    assert e.value.msg == "验证码错误"
    assert e.value.code == 1002


def test_verify_expired():
    store = InMemoryCaptchaStore()
    store.save("k2", "7", ttl_seconds=0)  # 立即过期
    with pytest.raises(BusinessError) as e:
        verify_captcha(store, "k2", "7")
    assert e.value.msg == "验证码已过期"
    assert e.value.code == 1001


def test_verify_strips_whitespace():
    store = InMemoryCaptchaStore()
    store.save("k3", "42", ttl_seconds=60)
    verify_captcha(store, "k3", " 42 ")
