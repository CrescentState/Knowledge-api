import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from docling.document_converter import DocumentConverter
from loguru import logger
import asyncio

from app.schemas.document import ExtractionResult


class DocumentProcessor:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=2)  # ← Created
        self.converter = DocumentConverter()
        

    async def process_pdf(self, file_path: Path) -> ExtractionResult:
        # "Bind" the filename to all logs in this scope
        log = logger.bind(filename=file_path.name)

        log.info(f"Starting extraction for: {file_path.name}")
        start_time = time.perf_counter()

        try:
            # The conversion process
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
            self._executor, self.converter.convert, file_path
        )

            end_time = time.perf_counter()
            total_duration = end_time - start_time

            # Metadata extraction
            page_count = (
                len(result.document.pages) if hasattr(result.document, "pages") else 1
            )
            avg_time_per_page = total_duration / page_count if page_count > 0 else 0

            # Professional Granular Logging
            log.success(f"Extraction complete for {file_path.name}")
            log.info(f"Total Pages: {page_count}")
            log.info(f"Total Time: {total_duration:.2f}s")
            log.info(f"Avg Time Per Page: {avg_time_per_page:.2f}s")

            return ExtractionResult(
                content=result.document.export_to_markdown(),
                page_count=page_count,
                metadata=result.document.metadata.model_dump()
                if hasattr(result.document, "metadata")
                else {},
                processing_time_seconds=round(total_duration, 2),
            )

        except Exception as e:
            log.error(f"Failed to process document: {str(e)}")
            raise e

    def shutdown(self) -> None:
        """Gracefully shut down the thread pool executor."""
        logger.info("Shutting down DocumentProcessor executor...")
        self._executor.shutdown(wait=True)
