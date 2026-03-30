from datetime import datetime
from typing import Literal

from pydantic import BaseModel


ChatMode = Literal["chat", "code", "debug", "review"]
UserType = Literal["guest", "registered"]


class AuthenticatedUserResponse(BaseModel):
    id: int
    public_id: str
    session_label: str
    email: str | None = None
    display_name: str | None = None
    user_type: UserType
    auth_provider: str
    email_verified: bool
    session_id: str
    session_expires_at: datetime
    guest_message_limit: int | None = None
    guest_messages_used: int = 0
    remaining_guest_messages: int | None = None


class UserSessionResponse(BaseModel):
    token: str
    access_token: str
    session_label: str
    user_id: int
    session_id: str
    expires_at: int
    refresh_expires_at: int
    user: AuthenticatedUserResponse


class GuestSessionRequest(BaseModel):
    client_session_id: str | None = None


class SignupRequest(BaseModel):
    email: str
    password: str
    display_name: str | None = None
    client_session_id: str | None = None


class LoginRequest(BaseModel):
    email: str
    password: str
    client_session_id: str | None = None


class LogoutResponse(BaseModel):
    success: bool = True


class GoogleLoginUrlResponse(BaseModel):
    enabled: bool
    login_url: str | None = None
    detail: str | None = None


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
