from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ..config import JWT_EXPIRES_SECONDS, JWT_SECRET, SessionLocal
from ..repository.chat_repository import ChatRepository
from ..service.auth_service import AuthError, AuthService


bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service() -> AuthService:
    return AuthService(
        ChatRepository(SessionLocal),
        secret=JWT_SECRET,
        expires_in_seconds=JWT_EXPIRES_SECONDS,
    )


def require_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    auth_service: AuthService = Depends(get_auth_service),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required")

    try:
        return auth_service.get_user_from_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc
