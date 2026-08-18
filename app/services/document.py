import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pymupdf4llm
import fitz
from loguru import logger

from app.schemas.document import ExtractionResult


class DocumentProcessor:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=2)

    def _extract_pdf_data(self, file_path: Path) -> tuple[str, int, dict]:
        # Extracts clean Markdown using PyMuPDF4LLM
        content = pymupdf4llm.to_markdown(str(file_path))
        
        with fitz.open(file_path) as doc:
            page_count = len(doc)
            metadata = dict(doc.metadata) if doc.metadata else {}
            
        return content, page_count, metadata

    async def process_pdf(self, file_path: Path) -> ExtractionResult:
        log = logger.bind(filename=file_path.name)

        log.info(f"Starting extraction for: {file_path.name}")
        start_time = time.perf_counter()

        try:
            loop = asyncio.get_running_loop()
            content, page_count, metadata = await loop.run_in_executor(
                self._executor, self._extract_pdf_data, file_path
            )

            end_time = time.perf_counter()
            total_duration = end_time - start_time
            avg_time_per_page = total_duration / page_count if page_count > 0 else 0

            log.success(f"Extraction complete for {file_path.name}")
            log.info(f"Total Pages: {page_count}")
            log.info(f"Total Time: {total_duration:.2f}s")
            log.info(f"Avg Time Per Page: {avg_time_per_page:.2f}s")

            return ExtractionResult(
                content=content,
                page_count=page_count,
                metadata=metadata,
                processing_time_seconds=round(total_duration, 2),
            )

        except Exception as e:
            log.error(f"Failed to process document: {str(e)}")
            raise

    def shutdown(self) -> None:
        """Gracefully shut down the thread pool executor."""
        logger.info("Shutting down DocumentProcessor executor...")
        self._executor.shutdown(wait=True)