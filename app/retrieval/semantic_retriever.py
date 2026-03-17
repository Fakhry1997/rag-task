from __future__ import annotations

from langchain_core.documents import Document

from app.models.response_models import Source
from app.stores.vector_store import VectorStore


class SemanticRetriever:
    """
    Embeds the query with Gemini text-embedding-004, searches FAISS,
    and returns top-k chunks strictly filtered to client_id.
    """

    def __init__(self, vector_store: VectorStore) -> None:
        self._vector = vector_store

    def retrieve(
        self, query: str, client_id: str
    ) -> tuple[list[Document], list[Source]]:
        docs = self._vector.search(query, client_id=client_id)
        sources = [
            Source(
                store="vector",
                reference=f"{doc.metadata.get('source_doc', 'unknown')} § {doc.metadata.get('section_heading', '')}",
                snippet=doc.page_content[:200],
            )
            for doc in docs
        ]
        return docs, sources
