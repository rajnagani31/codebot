from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


ChatMode = Literal["chat", "code", "debug", "review"]


class UserSessionResponse(BaseModel):
    token: str
    user_id: int
    session_label: str
    expires_at: int


class AuthenticatedUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_label: str


class CreateThreadRequest(BaseModel):
    title: str
    mode: ChatMode = "chat"
    client_session_id: str | None = None


class ThreadSummaryResponse(BaseModel):
    id: str
    title: str
    mode: ChatMode
    updated_at: datetime
    last_message_at: datetime | None = None
    preview: str = ""
    message_count: int = 0


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    status: str
    created_at: datetime
    completed_at: datetime | None = None


class ChatStreamRequest(BaseModel):
    thread_id: str
    query: str
    code: str | None = None
    mode: ChatMode = "chat"
