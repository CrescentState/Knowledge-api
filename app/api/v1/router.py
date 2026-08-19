import tempfile
import uuid
import tempfile
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, UploadFile, Query, status, File
from loguru import logger
from pydantic import BaseModel

from app.schemas.document import ExtractionResult
from app.services.document import DocumentProcessor
from app.services.vector_service import VectorService

router = APIRouter()
document_processor = DocumentProcessor()
vector_service = VectorService()

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"application/pdf"}

class SearchResult(BaseModel):
    id: int
    document_name: str
    chunk_index: int
    content: str
    similarity_score: float

class SearchResponse(BaseModel):
    query: str
    results_count: int
    results: list[SearchResult]

# This is the "Worker" function that runs after the response is sent
async def process_document_task(
    processor: object, file_path: Path, original_name: str
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


@router.post("/documents/upload", status_code=202)  # 202 = Accepted
async def upload_document(
    request: Request, background_tasks: BackgroundTasks, file: UploadFile
) -> dict:

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    # Validate file extension (basic check)
    safe_filename = Path(file.filename).name  # Prevent path traversal
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF files are allowed.",
        )

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
                        detail=(
                            f"File size exceeds maximum allowed size of "
                            f"{MAX_FILE_SIZE // (1024 * 1024)} MB."
                        ),
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
    # Lazy initialization: create processor on first request
    if not hasattr(request.app.state, "processor"):
        from app.services.document import DocumentProcessor
        request.app.state.processor = DocumentProcessor()
        logger.info("Initialized DocumentProcessor on first request")

    background_tasks.add_task(
        process_document_task, request.app.state.processor, temp_path, safe_filename
    )

    # 4. Return immediately to the user
    return {
        "message": "File uploaded successfully. Processing has started in the background.",
        "filename": safe_filename,
    }

@router.post(
    "/process-pdf",
    response_model=ExtractionResult,
    status_code=status.HTTP_200_OK,
)
async def process_pdf_endpoint(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported.",
        )

    # 1. Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)

    try:
        # 2. Extract text/markdown using DocumentProcessor (PyMuPDF)
        result = await document_processor.process_pdf(tmp_path)

        # 3. Chunk, embed, and save chunks to PGVector
        chunks_stored = vector_service.process_and_store(
            document_name=file.filename,
            content=result.content,
        )
        logger.info(f"Indexed {chunks_stored} chunks into PGVector for '{file.filename}'")

        return result

    except Exception as e:
        logger.error(f"Processing failed for {file.filename}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document: {str(e)}",
        )
    finally:
        # Clean up temp file
        if tmp_path.exists():
            tmp_path.unlink()

@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., description="Semantic search query"),
    top_k: int = Query(5, ge=1, le=20, description="Number of results to return")
):
    try:
        matches = vector_service.search_similar_chunks(query=q, top_k=top_k)
        return SearchResponse(
            query=q,
            results_count=len(matches),
            results=matches
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {str(e)}")