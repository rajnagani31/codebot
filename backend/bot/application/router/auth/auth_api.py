from fastapi import APIRouter, Depends

from ...dependencies.auth import get_auth_service, require_current_user
from ...schema.chat_schema import AuthenticatedUserResponse, UserSessionResponse
from ...service.auth_service import AuthService


router = APIRouter()


@router.post("/guest", response_model=UserSessionResponse)
def create_guest_session(auth_service: AuthService = Depends(get_auth_service)):
    return auth_service.create_guest_session()


@router.get("/me", response_model=AuthenticatedUserResponse)
def get_authenticated_user(current_user=Depends(require_current_user)):
    return current_user
