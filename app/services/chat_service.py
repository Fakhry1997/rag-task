from __future__ import annotations

import uuid

from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import settings
from app.models.response_models import ChatResponse, Message, Source
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.semantic_retriever import SemanticRetriever
from app.retrieval.structured_retriever import StructuredRetriever
from app.services.query_router import QueryRouter, RouteType
from app.stores.session_store import SessionStore
from app.stores.sql_store import SQLStore
from app.stores.vector_store import VectorStore

_ANSWER_SYSTEM = """You are a helpful product safety assistant.
Answer the user's question using ONLY the context provided below.
If the context does not contain enough information, say so honestly.
Cite the source (structured data or document name) when possible.
Be concise and precise.
Write in plain prose paragraphs — no bullet points, no markdown, no headers.
"""


class ChatService:
    """
    End-to-end query handler:
      1. Load session history
      2. Route the question (structured / semantic / hybrid)
      3. Retrieve relevant context
      4. Synthesize a grounded answer via Gemini
      5. Persist the exchange in session store
    """

    def __init__(
        self,
        sql_store: SQLStore,
        vector_store: VectorStore,
        session_store: SessionStore,
    ) -> None:
        self._sessions = session_store
        self._router = QueryRouter()
        self._structured = StructuredRetriever(sql_store)
        self._semantic = SemanticRetriever(vector_store)
        self._hybrid = HybridRetriever(self._structured, self._semantic)
        self._llm = ChatGoogleGenerativeAI(
            model=settings.GEMINI_LLM_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
            temperature=0.2,
        )

    async def answer(
        self,
        question: str,
        client_id: str,
        session_id: str | None,
    ) -> ChatResponse:
        session_id = session_id or str(uuid.uuid4())
        history = self._sessions.get(session_id).get("messages", [])

        # 1. Route
        route: RouteType = await self._router.route(question)

        # 2. Retrieve context
        context, sources = await self._fetch_context(question, client_id, route)

        # 3. Build prompt
        messages = self._build_messages(history, context, question)

        # 4. Synthesize answer
        response = await self._llm.ainvoke(messages)
        answer_text = response.content.strip()

        # 5. Persist exchange
        self._sessions.append(session_id, client_id, Message(role="user", content=question))
        self._sessions.append(session_id, client_id, Message(role="assistant", content=answer_text))

        return ChatResponse(
            session_id=session_id,
            answer=answer_text,
            route_used=route,
            sources=sources,
        )

    # ── internal ─────────────────────────────────────────────────────────────

    async def _fetch_context(
        self, question: str, client_id: str, route: RouteType
    ) -> tuple[str, list[Source]]:
        if route == "structured":
            rows, sources = await self._structured.retrieve(question, client_id)
            context = "\n".join(
                f"- {r.get('parameter')}: {r.get('numeric_value')} {r.get('unit', '')} [{r.get('region')}]"
                for r in rows
            )
            return context, sources

        if route == "semantic":
            docs, sources = self._semantic.retrieve(question, client_id)
            context = "\n\n".join(d.page_content for d in docs)
            return context, sources

        # hybrid
        return await self._hybrid.retrieve(question, client_id)

    def _build_messages(
        self,
        history: list[Message],
        context: str,
        question: str,
    ) -> list[tuple[str, str]]:
        messages: list[tuple[str, str]] = [("system", _ANSWER_SYSTEM)]

        # Include last 6 turns of history for context window efficiency
        for msg in history[-6:]:
            messages.append((msg.role, msg.content))

        messages.append(
            ("human", f"Context:\n{context}\n\nQuestion: {question}")
        )
        return messages
