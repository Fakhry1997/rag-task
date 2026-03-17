"""Stub — implementation in a later phase."""
from collections import defaultdict
from app.models.response_models import Message


class SessionStore:
    def __init__(self) -> None:
        # { session_id: {"client_id": str, "messages": [Message]} }
        self._store: dict[str, dict] = defaultdict(lambda: {"client_id": "", "messages": []})

    def get(self, session_id: str) -> dict:
        return self._store[session_id]

    def append(self, session_id: str, client_id: str, message: Message) -> None:
        entry = self._store[session_id]
        entry["client_id"] = client_id
        entry["messages"].append(message)

    def clear(self, session_id: str) -> None:
        self._store.pop(session_id, None)
