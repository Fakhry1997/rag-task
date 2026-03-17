from __future__ import annotations

import os

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.core.config import settings


class VectorStore:
    """
    Wraps a FAISS index using Gemini embeddings.
    Persists the index to disk so it survives restarts.
    Client isolation is enforced by filtering on chunk metadata['client_id'].
    """

    def __init__(self) -> None:
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model=settings.GEMINI_EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        self._index_path = settings.VECTOR_STORE_PATH
        self._index: FAISS | None = self._load_existing()

    # ── write ─────────────────────────────────────────────────────────────────

    def upsert(self, docs: list[Document]) -> int:
        """Embed and add documents; returns count stored."""
        if not docs:
            return 0
        if self._index is None:
            self._index = FAISS.from_documents(docs, self._embeddings)
        else:
            self._index.add_documents(docs)
        self._persist()
        return len(docs)

    # ── read ──────────────────────────────────────────────────────────────────

    def search(self, query: str, client_id: str, k: int | None = None) -> list[Document]:
        """
        Semantic search filtered strictly to client_id.
        Returns at most k documents (defaults to settings.VECTOR_TOP_K).
        """
        if self._index is None:
            return []
        top_k = k or settings.VECTOR_TOP_K
        # Fetch more candidates then filter — FAISS doesn't support metadata pre-filter
        candidates = self._index.similarity_search(query, k=top_k * 4)
        filtered = [d for d in candidates if d.metadata.get("client_id") == client_id]
        return filtered[:top_k]

    # ── internal ──────────────────────────────────────────────────────────────

    def _persist(self) -> None:
        os.makedirs(self._index_path, exist_ok=True)
        self._index.save_local(self._index_path)

    def _load_existing(self) -> FAISS | None:
        index_file = os.path.join(self._index_path, "index.faiss")
        if os.path.exists(index_file):
            return FAISS.load_local(
                self._index_path,
                self._embeddings,
                allow_dangerous_deserialization=True,
            )
        return None
