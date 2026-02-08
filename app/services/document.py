import time
from pathlib import Path
from typing import Any

from docling.document_converter import DocumentConverter

from app.schemas.document import ExtractionResult


class DocumentProcessor:
    def __init__(self) -> None:
        # Initialize the converter (This can be expensive, so we do it once)
        self.converter = DocumentConverter()

    async def process_pdf(self, file_path: Path) -> ExtractionResult:
        """
        Processes a PDF and returns structured Markdown content.
        """
        start_time = time.perf_counter()

        # Perform the conversion
        result = self.converter.convert(file_path)

        # Export to Markdown (Industry standard for LLM ingestion)
        markdown_content = result.document.export_to_markdown()

        execution_time = time.perf_counter() - start_time

        # Extract metadata safely
        metadata: dict[str, Any] = {}

        return ExtractionResult(
            content=markdown_content,
            page_count=len(result.document.pages)
            if hasattr(result.document, "pages")
            else 1,
            metadata=metadata,
            processing_time_seconds=round(execution_time, 2),
        )
