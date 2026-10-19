"""应用入口：app 工厂 + 启动初始化。"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from tfserver.api.v1 import auth, menus, roles, users
from tfserver.core.config import get_settings
from tfserver.core.response import register_exception_handlers
from tfserver.domain.auth.captcha import InMemoryCaptchaStore
from tfserver.infra.db import Base, engine, session_scope
from tfserver.infra import models  # noqa: F401  确保表模型注册
from tfserver.domain.rbac import service as rbac

logger = logging.getLogger("tfserver")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    with session_scope() as db:
        rbac.seed_if_empty(db)
    logger.info("TestForge 启动完成（db=%s）", get_settings().database_url.split("://")[0])
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="TestForge API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.captcha_store = InMemoryCaptchaStore()

    app.include_router(auth.router)
    app.include_router(users.router)
    app.include_router(roles.router)
    app.include_router(menus.router)

    register_exception_handlers(app)
    return app


app = create_app()
