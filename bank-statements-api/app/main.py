import logging
import os
import subprocess
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware

from app.api.errors import AppException, ErrorResponse
from app.app import register_app_routes
from app.core.config import settings
from app.core.dependencies import provide_dependencies
from app.logging.config import init_logging

init_logging()
logger = logging.getLogger(__name__)


def _resolve_version() -> str:
    if env_version := os.environ.get("APP_VERSION"):
        return env_version.strip()
    api_dir = Path(__file__).resolve().parents[1]
    for candidate in (api_dir.parent / "VERSION", api_dir / "VERSION", Path("/VERSION")):
        if candidate.is_file():
            return candidate.read_text().strip()
    return "unknown"


def _resolve_commit() -> str:
    if env_commit := os.environ.get("APP_COMMIT"):
        return env_commit.strip()
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=Path(__file__).resolve().parents[2],
                stderr=subprocess.DEVNULL,
            )
            .decode()
            .strip()
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


APP_VERSION = _resolve_version()
APP_COMMIT = _resolve_commit()

app = FastAPI(version=APP_VERSION)


@app.get("/version", tags=["meta"])
def get_version() -> dict[str, str]:
    return {"version": APP_VERSION, "commit": APP_COMMIT}


@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(f"{request.method} {request.url.path} - {duration_ms:.0f}ms")
    return response


app.add_middleware(SessionMiddleware, secret_key=settings.JWT_SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            code=exc.code,
            message=exc.message,
            details=exc.details,
        ).model_dump(),
    )


@app.exception_handler(ValueError)
async def value_error_handler(_request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            code="VALIDATION_ERROR",
            message=str(exc),
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(_request: Request, _exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
        ).model_dump(),
    )


register_app_routes(app, provide_dependencies)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.API_PORT,
    )
