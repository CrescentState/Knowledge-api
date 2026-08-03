import shutil
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile
from loguru import logger

from app.services.document import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["documents"])

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}


# This is the "Worker" function that runs after the response is sent
async def process_document_task(
    processor: DocumentProcessor, file_path: Path, original_name: str
) -> None:
    try:
        logger.info(f"Background processing started for {original_name}")
        result = await processor.process_pdf(file_path)  # Our heavy Docling logic

        # FOR NOW: We just log the result.
        # IN PHASE 2: We will save this result to a database/Vector Store.
        logger.success(
            f"Background processing complete: {len(result.content)} characters extracted."
        )

    except Exception as e:
        logger.error(f"Background processing failed for {original_name}: {e}")
    finally:
        # Cleanup the temp file after processing is done
        if file_path.exists():
            file_path.unlink()
            logger.debug(f"Temporary file {file_path} removed.")


@router.post("/upload", status_code=202)  # 202 = Accepted
async def upload_document(
    request: Request, background_tasks: BackgroundTasks, file: UploadFile
) -> dict:

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Validate file extension (basic check)
    safe_filename = Path(file.filename).name  # Prevent path traversal
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDF files are allowed.")

    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid content type: {file.content_type}. Only application/pdf is allowed.",
        )

    # 1. Create a unique, non-predictable temp path in the system temp directory
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / f"{uuid.uuid4()}_{safe_filename}"

    # 2. Save the uploaded file to disk with size limit
    try:
        file_size = 0
        with temp_path.open("wb") as buffer:
            while chunk := file.file.read(8192):
                file_size += len(chunk)
                if file_size > MAX_FILE_SIZE:
                    # Clean up partial file and reject
                    buffer.close()
                    temp_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE // (1024 * 1024)} MB.",
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save uploaded file {safe_filename}: {e}")
        if temp_path.exists():
            temp_path.unlink()
        raise HTTPException(status_code=500, detail="Failed to save uploaded file.") from e

    # 3. Hand the job over to the background worker
    background_tasks.add_task(
        process_document_task, request.app.state.processor, temp_path, safe_filename
    )

    # 4. Return immediately to the user
    return {
        "message": "File uploaded successfully. Processing has started in the background.",
        "filename": safe_filename,
    }
