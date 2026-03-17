from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.controllers.ingestion_controller import IngestionController
from app.core.dependencies import get_ingestion_controller
from app.models.response_models import IngestResponse

router = APIRouter()

_ALLOWED_EXTENSIONS = {".xlsx", ".docx"}
_ALLOWED_CONTENT_TYPES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # some clients send this for both types
}


@router.post("", response_model=IngestResponse, status_code=202, summary="Ingest a document")
async def ingest_document(
    client_id: str = Form(..., description="Client this document belongs to"),
    file: UploadFile = File(..., description=".xlsx or .docx file to ingest"),
    controller: IngestionController = Depends(get_ingestion_controller),
) -> IngestResponse:
    """
    Upload an Excel or Word document and ingest it into the appropriate store.

    - **.xlsx** → structured rows extracted into SQLite, keyed by `client_id`.
    - **.docx** → narrative text chunked and embedded into the vector store,
      with `client_id` attached to every chunk's metadata.

    Both types may be ingested for the same client; the query router decides
    which store(s) to search at query time.
    """
    _validate_file(file)
    return await controller.handle_ingest(client_id=client_id, file=file)


def _validate_file(file: UploadFile) -> None:
    import os

    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Unsupported file type '{ext}'. Allowed: {', '.join(_ALLOWED_EXTENSIONS)}"
        )
