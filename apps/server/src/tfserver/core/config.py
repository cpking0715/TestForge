"""应用配置：环境变量 + .env，凭据不落源码。"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # 数据库：默认零配置 SQLite；开发/生产通过 .env 指向 PostgreSQL
    database_url: str = "sqlite:///./testforge.db"

    # 安全
    secret_key: str = "dev-secret-change-me"  # 生产必须通过环境变量覆盖
    token_expire_minutes: int = 720
    token_issuer: str = "testforge"

    # 验证码
    captcha_ttl_seconds: int = 180
    # 内部部署可关闭验证码（登录时跳过校验，验证码接口仍可用）
    captcha_enabled: bool = True

    # CORS（前端开发端口）
    cors_origins: list[str] = ["http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
