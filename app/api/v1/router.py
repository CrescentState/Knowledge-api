import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.document import ExtractionResult
from app.services.document import DocumentProcessor

router = APIRouter(prefix="/documents", tags=["documents"])
processor = DocumentProcessor()
file_param = File(...)


@router.post("/upload", response_model=ExtractionResult)
async def upload_document(file: UploadFile = file_param) -> ExtractionResult:
    if not file.filename or not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Temporary storage for processing
    temp_path = Path(f"temp_{file.filename}")
    with temp_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        result = await processor.process_pdf(temp_path)
        return result
    finally:
        # Cleanup: Professional code never leaves trash behind
        if temp_path.exists():
            temp_path.unlink()
