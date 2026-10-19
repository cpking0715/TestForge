"""统一响应信封：{code, msg, data}。

约定：业务失败 HTTP 200 + code≠0；鉴权失败 401；未捕获异常 500。
HTTP 状态与业务 code 解耦，前端只看 code。
"""

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

CODE_OK = 0
CODE_FAIL = -1
CODE_UNAUTHORIZED = 401


class BusinessError(Exception):
    """业务失败：HTTP 200 + code≠0，msg 面向用户。"""

    def __init__(self, msg: str, *, code: int = CODE_FAIL):
        self.msg = msg
        self.code = code
        super().__init__(msg)


def ok(data: Any = None, msg: str = "操作成功") -> dict[str, Any]:
    return {"code": CODE_OK, "msg": msg, "data": data}


def fail(msg: str, *, code: int = CODE_FAIL) -> dict[str, Any]:
    return {"code": code, "msg": msg, "data": None}


def register_exception_handlers(app) -> None:
    @app.exception_handler(BusinessError)
    async def on_business_error(_: Request, exc: BusinessError) -> JSONResponse:
        return JSONResponse(status_code=200, content=fail(exc.msg, code=exc.code))

    @app.exception_handler(StarletteHTTPException)
    async def on_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "请求错误"
        return JSONResponse(
            status_code=exc.status_code,
            content=fail(detail, code=exc.status_code),
        )

    @app.exception_handler(RequestValidationError)
    async def on_validate_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        return JSONResponse(status_code=200, content=fail(f"参数错误：{loc} {first.get('msg', '')}"))

    @app.exception_handler(Exception)
    async def on_unknown(_: Request, exc: Exception) -> JSONResponse:  # pragma: no cover
        return JSONResponse(status_code=500, content=fail(f"服务器内部错误：{exc}"))
