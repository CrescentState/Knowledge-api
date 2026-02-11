from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1.router import router as api_v1_router
from app.core.config import settings
from app.services.document import DocumentProcessor

state = {}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # --- Startup Logic ---
    logger.info("🚀 Initializing Heavy AI Models (Docling)...")
    app.state.processor = DocumentProcessor()
    yield
    # --- Shutdown Logic ---
    logger.info("🛑 Cleaning up resources...")
    state.clear()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str]:
    return {"status": "active", "version": settings.VERSION}
