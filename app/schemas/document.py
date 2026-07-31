from typing import Any

from pydantic import Field

from app.schemas.base import CoreModel


class ExtractionResult(CoreModel):
    """The structured output of our Brain."""
    content: str = Field(..., description="The extracted markdown text")
    page_count: int = Field(..., ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    processing_time_seconds: float
