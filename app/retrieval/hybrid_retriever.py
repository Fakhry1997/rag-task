from __future__ import annotations

import asyncio

from langchain_core.documents import Document

from app.models.response_models import Source
from app.retrieval.semantic_retriever import SemanticRetriever
from app.retrieval.structured_retriever import StructuredRetriever


class HybridRetriever:
    """
    Calls both retrievers in parallel, merges results into a single context block.
    """

    def __init__(
        self,
        structured: StructuredRetriever,
        semantic: SemanticRetriever,
    ) -> None:
        self._structured = structured
        self._semantic = semantic

    async def retrieve(
        self, question: str, client_id: str
    ) -> tuple[str, list[Source]]:
        """Returns (merged_context_text, combined_sources). Both stores queried in parallel."""
        (sql_rows, sql_sources), (vec_docs, vec_sources) = await asyncio.gather(
            self._structured.retrieve(question, client_id),
            asyncio.to_thread(self._semantic.retrieve, question, client_id),
        )

        context_parts: list[str] = []

        if sql_rows:
            formatted = "\n".join(
                f"- {r.get('parameter')}: {r.get('numeric_value')} {r.get('unit', '')} "
                f"[{r.get('region')}] ({r.get('limit_type')})"
                for r in sql_rows
            )
            context_parts.append(f"Structured data:\n{formatted}")

        if vec_docs:
            formatted = "\n\n".join(d.page_content for d in vec_docs)
            context_parts.append(f"Narrative context:\n{formatted}")

        context = "\n\n---\n\n".join(context_parts)
        sources = sql_sources + vec_sources
        return context, sources
