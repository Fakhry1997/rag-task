from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    client_id: str = Field(..., description="Owning client — enforces data isolation")
    session_id: str | None = Field(
        default=None,
        description="Existing session ID. Omit to start a new session.",
    )
    message: str = Field(..., min_length=1, description="User's natural language question")

    @field_validator("session_id", mode="before")
    @classmethod
    def empty_str_to_none(cls, v: object) -> object:
        """Treat empty string the same as null — both start a fresh session."""
        if isinstance(v, str) and v.strip() == "":
            return None
        return v
