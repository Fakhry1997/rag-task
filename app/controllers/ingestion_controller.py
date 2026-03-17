"""Stub — implementation in a later phase."""
from fastapi import UploadFile

from app.models.response_models import IngestResponse
from app.stores.sql_store import SQLStore
from app.stores.vector_store import VectorStore


class IngestionController:
    def __init__(self, sql_store: SQLStore, vector_store: VectorStore) -> None:
        self._sql = sql_store
        self._vector = vector_store

    async def handle_ingest(self, client_id: str, file: UploadFile) -> IngestResponse:
        raise NotImplementedError
