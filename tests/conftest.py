from unittest.mock import MagicMock

import pytest

from app.main import app


@pytest.fixture(autouse=True)
def mock_processor() -> MagicMock:
    """Mocks the heavy Docling processor to keep tests fast."""
    mock = MagicMock()

    # Mock the return value of process_pdf (it must be a coroutine!)
    async def fake_process(*args: object, **kwargs: object) -> MagicMock:
        return MagicMock(content="Mocked Content", page_count=1)

    mock.process_pdf = fake_process

    # Inject the mock into app state (lifespan doesn't run with ASGITransport)
    app.state.processor = mock
    return mock
