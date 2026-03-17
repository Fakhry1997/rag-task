"""Stub — implementation in a later phase."""
from app.models.request_models import ChatRequest
from app.models.response_models import ChatResponse, SessionHistoryResponse
from app.stores.session_store import SessionStore
from app.stores.sql_store import SQLStore
from app.stores.vector_store import VectorStore


class ChatController:
    def __init__(
        self,
        sql_store: SQLStore,
        vector_store: VectorStore,
        session_store: SessionStore,
    ) -> None:
        self._sql = sql_store
        self._vector = vector_store
        self._sessions = session_store

    async def handle_query(self, body: ChatRequest) -> ChatResponse:
        raise NotImplementedError

    async def get_history(self, session_id: str, client_id: str) -> SessionHistoryResponse:
        raise NotImplementedError

    async def clear_session(self, session_id: str, client_id: str) -> None:
        raise NotImplementedError
