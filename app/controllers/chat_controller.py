from app.core.security import validate_client_access
from app.models.request_models import ChatRequest
from app.models.response_models import ChatResponse, Message, SessionHistoryResponse
from app.services.chat_service import ChatService
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
        self._service = ChatService(
            sql_store=sql_store,
            vector_store=vector_store,
            session_store=session_store,
        )
        self._sessions = session_store

    async def handle_query(self, body: ChatRequest) -> ChatResponse:
        # Enforce isolation: if resuming a session, its owner must match
        if body.session_id:
            existing = self._sessions.get(body.session_id)
            owner = existing.get("client_id")
            if owner:
                validate_client_access(
                    resource_client_id=owner,
                    requesting_client_id=body.client_id,
                )

        return await self._service.answer(
            question=body.message,
            client_id=body.client_id,
            session_id=body.session_id,
        )

    async def get_history(self, session_id: str, client_id: str) -> SessionHistoryResponse:
        entry = self._sessions.get(session_id)
        owner = entry.get("client_id")
        if owner:
            validate_client_access(
                resource_client_id=owner,
                requesting_client_id=client_id,
            )
        return SessionHistoryResponse(
            session_id=session_id,
            client_id=client_id,
            messages=entry.get("messages", []),
        )

    async def clear_session(self, session_id: str, client_id: str) -> None:
        entry = self._sessions.get(session_id)
        owner = entry.get("client_id")
        if owner:
            validate_client_access(
                resource_client_id=owner,
                requesting_client_id=client_id,
            )
        self._sessions.clear(session_id)
