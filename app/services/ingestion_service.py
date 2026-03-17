from __future__ import annotations

import os
import tempfile

from fastapi import UploadFile

from app.ingestion.excel_parser import ExcelParser
from app.ingestion.text_chunker import TextChunker
from app.ingestion.word_parser import WordParser
from app.stores.sql_store import SQLStore
from app.stores.vector_store import VectorStore


class IngestionService:
    """
    Orchestrates the full ingestion pipeline:
      .xlsx  →  ExcelParser  →  SQLStore
      .docx  →  WordParser  →  TextChunker  →  VectorStore
    """

    def __init__(self, sql_store: SQLStore, vector_store: VectorStore) -> None:
        self._sql = sql_store
        self._vector = vector_store
        self._excel_parser = ExcelParser()
        self._word_parser = WordParser()
        self._chunker = TextChunker()

    async def ingest(
        self, client_id: str, file: UploadFile
    ) -> tuple[int, int]:
        """
        Returns (rows_stored, chunks_stored).
        Writes the upload to a temp file so parsers can use file-path APIs.
        """
        ext = os.path.splitext(file.filename or "")[-1].lower()
        contents = await file.read()

        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        try:
            if ext == ".xlsx":
                return await self._ingest_excel(client_id, tmp_path, file.filename)
            elif ext == ".docx":
                return await self._ingest_word(client_id, tmp_path, file.filename)
            else:
                raise ValueError(f"Unsupported extension: {ext}")
        finally:
            os.unlink(tmp_path)

    # ── private ───────────────────────────────────────────────────────────────

    async def _ingest_excel(
        self, client_id: str, path: str, filename: str
    ) -> tuple[int, int]:
        rows = self._excel_parser.parse(path)
        count = self._sql.insert_rows(rows, client_id=client_id, source_file=filename)
        return count, 0

    async def _ingest_word(
        self, client_id: str, path: str, filename: str
    ) -> tuple[int, int]:
        paragraphs = self._word_parser.parse(path)
        docs = self._chunker.chunk(paragraphs, client_id=client_id, source_doc=filename)
        count = self._vector.upsert(docs)
        return 0, count
