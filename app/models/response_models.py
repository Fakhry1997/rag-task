from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


# ── Ingestion ────────────────────────────────────────────────────────────────

class IngestResponse(BaseModel):
    status: Literal["success", "partial", "failed"]
    client_id: str
    filename: str
    rows_stored: int = Field(0, description="Structured rows written to SQLite")
    chunks_stored: int = Field(0, description="Text chunks written to vector store")
    detail: str | None = None


# ── Chat ─────────────────────────────────────────────────────────────────────

class Source(BaseModel):
    store: Literal["sql", "vector"]
    reference: str = Field(..., description="Table + row ID or document name + chunk index")
    snippet: str | None = None


class ChatResponse(BaseModel):
    session_id: str
    answer: str
    route_used: Literal["structured", "semantic", "hybrid"]
    sources: list[Source] = []


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class SessionHistoryResponse(BaseModel):
    session_id: str
    client_id: str
    messages: list[Message] = []
