import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check() -> None:
    """Verify the API is healthy."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "active"


@pytest.mark.asyncio
async def test_upload_non_pdf_fails() -> None:
    """Verify the API rejects non-PDF files."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}
        response = await ac.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_upload_pdf_success_flow() -> None:
    """Verify the 202 Accepted flow for a PDF."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Create a fake PDF-like byte string
        files = {"file": ("test.pdf", b"%PDF-1.4...", "application/pdf")}
        response = await ac.post("/api/v1/documents/upload", files=files)

    assert response.status_code == 202
    assert "Processing has started" in response.json()["message"]
