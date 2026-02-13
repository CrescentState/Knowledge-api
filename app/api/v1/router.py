import shutil
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile
from loguru import logger

router = APIRouter(prefix="/documents", tags=["documents"])


# This is the "Worker" function that runs after the response is sent
async def process_document_task(processor: object, file_path: Path, original_name: str) -> None:
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
    request: Request, background_tasks: BackgroundTasks, file: UploadFile = None
) -> dict:
    if file is None:
        file = File(...)

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # 1. Create a persistent temp path
    temp_path = Path(f"temp_{file.filename}")

    # 2. Save the uploaded file to disk
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 3. Hand the job over to the background worker
    background_tasks.add_task(
        process_document_task, request.app.state.processor, temp_path, file.filename
    )

    # 4. Return immediately to the user
    return {
        "message": "File uploaded successfully. Processing has started in the background.",
        "filename": file.filename,
    }
