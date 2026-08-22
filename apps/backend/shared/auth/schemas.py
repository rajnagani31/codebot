from pydantic import BaseModel
from typing import Optional


class TokenPayload(BaseModel):
    sub: str  # User ID (stringified int or uuid)
    email: Optional[str] = None
    user_type: str = "registered"  # "registered" | "guest"
    sid: Optional[int] = None  # Session ID
    provider: Optional[str] = None
    session_label: Optional[str] = None
    iat: Optional[int] = None
    exp: Optional[int] = None


class UserPrincipal(BaseModel):
    id: int
    public_id: Optional[str] = None
    email: Optional[str] = None
    display_name: Optional[str] = None
    user_type: str = "registered"
    session_id: Optional[int] = None
    guest_message_limit: Optional[int] = None
    guest_messages_used: int = 0
    remaining_guest_messages: Optional[int] = None

