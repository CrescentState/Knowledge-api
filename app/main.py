from fastapi import FastAPI

from app.api.v1.router import router as api_v1_router
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.get("/health", tags=["system"])
async def health_check() -> dict[str, str | bool]:
    """
    Standard health check for monitoring systems.
    """
    return {
        "status": "active",
        "version": settings.VERSION,
        "debug_mode": settings.DEBUG,
    }


app.include_router(api_v1_router, prefix=settings.API_V1_STR)
