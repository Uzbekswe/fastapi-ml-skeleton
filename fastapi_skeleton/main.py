from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from fastapi_skeleton.api.routes.router import api_router
from fastapi_skeleton.core.config import API_PREFIX, APP_NAME, APP_VERSION, settings
from fastapi_skeleton.services.models import HousePriceModel


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Running app start handler.")
    model_path = settings.DEFAULT_MODEL_PATH
    model_instance = HousePriceModel(model_path)
    app.state.model = model_instance
    yield
    logger.info("Running app shutdown handler.")
    app.state.model = None


def get_app() -> FastAPI:
    fast_app = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        debug=settings.IS_DEBUG,
        lifespan=lifespan,
    )

    fast_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    fast_app.include_router(api_router, prefix=API_PREFIX)

    @fast_app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return fast_app


app = get_app()
