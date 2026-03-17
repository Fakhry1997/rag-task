from functools import lru_cache

from fastapi import Depends

from app.controllers.chat_controller import ChatController
from app.controllers.ingestion_controller import IngestionController
from app.stores.session_store import SessionStore
from app.stores.sql_store import SQLStore
from app.stores.vector_store import VectorStore


@lru_cache(maxsize=1)
def _sql_store() -> SQLStore:
    return SQLStore()


@lru_cache(maxsize=1)
def _vector_store() -> VectorStore:
    return VectorStore()


@lru_cache(maxsize=1)
def _session_store() -> SessionStore:
    return SessionStore()


def get_ingestion_controller(
    sql: SQLStore = Depends(_sql_store),
    vector: VectorStore = Depends(_vector_store),
) -> IngestionController:
    return IngestionController(sql_store=sql, vector_store=vector)


def get_chat_controller(
    sql: SQLStore = Depends(_sql_store),
    vector: VectorStore = Depends(_vector_store),
    sessions: SessionStore = Depends(_session_store),
) -> ChatController:
    return ChatController(sql_store=sql, vector_store=vector, session_store=sessions)
