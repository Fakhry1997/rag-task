from fastapi import APIRouter, Depends

from app.controllers.chat_controller import ChatController
from app.core.dependencies import get_chat_controller
from app.models.request_models import ChatRequest
from app.models.response_models import ChatResponse, SessionHistoryResponse

router = APIRouter()


@router.post("/query", response_model=ChatResponse, summary="Ask a question")
async def query(
    body: ChatRequest,
    controller: ChatController = Depends(get_chat_controller),
) -> ChatResponse:
    """
    Route a natural language question to the correct retrieval path
    (structured / semantic / hybrid) and return a grounded answer.

    - **client_id**: enforces data isolation — only documents belonging to this client are searched.
    - **session_id**: pass the value returned from a previous response to maintain conversation context.
      Omit (or pass `null`) to start a fresh session.
    - **message**: the user's natural language question.
    """
    return await controller.handle_query(body)


@router.get(
    "/sessions/{session_id}/history",
    response_model=SessionHistoryResponse,
    summary="Get conversation history",
)
async def get_history(
    session_id: str,
    client_id: str,
    controller: ChatController = Depends(get_chat_controller),
) -> SessionHistoryResponse:
    """
    Return the full message history for a session.
    `client_id` must match the session owner — prevents cross-client history reads.
    """
    return await controller.get_history(session_id=session_id, client_id=client_id)


@router.delete(
    "/sessions/{session_id}",
    summary="Clear a session",
    status_code=204,
)
async def clear_session(
    session_id: str,
    client_id: str,
    controller: ChatController = Depends(get_chat_controller),
) -> None:
    """Delete all history for a session. Requires matching `client_id`."""
    await controller.clear_session(session_id=session_id, client_id=client_id)
