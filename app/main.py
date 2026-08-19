from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.database import init_db

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("🚀 Application startup complete (lazy model loading enabled)")
    init_db()
    yield
    logger.info("🛑 Cleaning up resources...")
    if hasattr(app.state, "processor"):
        app.state.processor.shutdown()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "active", "version": settings.VERSION}
