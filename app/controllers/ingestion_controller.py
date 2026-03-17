from fastapi import UploadFile

from app.models.response_models import IngestResponse
from app.services.ingestion_service import IngestionService
from app.stores.sql_store import SQLStore
from app.stores.vector_store import VectorStore


class IngestionController:
    def __init__(self, sql_store: SQLStore, vector_store: VectorStore) -> None:
        self._service = IngestionService(sql_store=sql_store, vector_store=vector_store)

    async def handle_ingest(self, client_id: str, file: UploadFile) -> IngestResponse:
        try:
            rows_stored, chunks_stored = await self._service.ingest(
                client_id=client_id, file=file
            )
            return IngestResponse(
                status="success",
                client_id=client_id,
                filename=file.filename or "",
                rows_stored=rows_stored,
                chunks_stored=chunks_stored,
            )
        except ValueError as exc:
            raise exc  # re-raised → caught by global handler → 400
        except Exception as exc:
            return IngestResponse(
                status="failed",
                client_id=client_id,
                filename=file.filename or "",
                detail=str(exc),
            )
