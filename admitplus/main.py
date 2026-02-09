import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from admitplus.database.redis import redismanager, BaseRedisCRUD
from admitplus.database.mongo import mongomanager
from admitplus.database.milvus import milvusmanager
from admitplus.config import settings
from admitplus.api import router, invite_router
from admitplus.agent import router as agent_router


log_dir = "logs"
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    force=True,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(os.path.join(log_dir, "app.log")),
    ],
)

load_dotenv()
under_dev = os.getenv("ENV", "").lower() == "dev"


class TokenRefreshMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if response.status_code < 200 or response.status_code >= 300:
            return response
        if request.url.path in {"/login", "/logout", "/docs", "/openapi.json"}:
            return response
        auth = request.headers.get("authorization")
        if not auth or not auth.startswith("Bearer "):
            return response

        token = auth.replace("Bearer ", "")
        await BaseRedisCRUD().expire(
            f"token:{token}",
            int(settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS or 1) * 24 * 60 * 60,
        )
        return response


def init_server():
    @asynccontextmanager
    async def lifespan(_: FastAPI):  # pylint: disable=function-redefined
        redismanager.init()
        mongomanager.init(settings.MONGO_URI)
        milvusmanager.init()
        yield
        await redismanager.close()
        mongomanager.close()
        milvusmanager.close()

    server = FastAPI(
        title="AdmitPlus Backend",
        description="Backend API for AdmitPlus Platform",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if under_dev else None,
        redoc_url=None,
        openapi_url="/openapi.json" if under_dev else None,
    )
    server.include_router(router)
    server.include_router(invite_router)
    server.include_router(agent_router)
    return server


server = init_server()


server.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=600,
)
server.add_middleware(TokenRefreshMiddleware)


@server.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@server.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.error(
        f"[Validation Error] {request.method} {request.url} - Errors: {exc.errors()}"
    )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@server.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error("Unhandled exception: %s", str(exc))

    if isinstance(exc, StarletteHTTPException):
        status_code = exc.status_code
        detail = exc.detail
    else:
        status_code = 500
        detail = "Internal server error"

    return JSONResponse(status_code=status_code, content={"detail": detail})


@server.get("/")
async def root():
    return {
        "message": "Welcome to AdmitPlus API. Please visit /docs for API documentation."
    }


if __name__ == "__main__":
    uvicorn.run("admitplus.main:server", host="127.0.0.1", port=8001)
