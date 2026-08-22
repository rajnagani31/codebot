import base64
import hashlib
import hmac
import json
import os
import time
from typing import Optional

from .schemas import TokenPayload


class AuthException(Exception):
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))


def get_jwt_secret() -> bytes:
    secret = os.getenv("JWT_SECRET", "codebot-dev-jwt-secret")
    return secret.encode("utf-8")


def decode_access_token(
    token: str,
    secret: Optional[bytes] = None,
    expected_type: str = "access",
) -> TokenPayload:
    if not secret:
        secret = get_jwt_secret()

    try:
        parts = token.split(".")
        if len(parts) != 3:
            raise AuthException("Token format invalid")
        encoded_header, encoded_payload, encoded_signature = parts
    except ValueError as exc:
        raise AuthException("Token format invalid") from exc

    # Verify signature
    signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
    expected_signature = hmac.new(secret, signing_input, hashlib.sha256).digest()
    actual_signature = _b64decode(encoded_signature)

    if not hmac.compare_digest(expected_signature, actual_signature):
        raise AuthException("Token signature invalid")

    # Parse payload
    try:
        raw_payload = json.loads(_b64decode(encoded_payload).decode("utf-8"))
    except Exception as exc:
        raise AuthException("Token payload corrupt") from exc

    # Validate expiration
    exp = int(raw_payload.get("exp", 0))
    if exp and exp < int(time.time()):
        raise AuthException("Token expired")

    # Validate token type (if typ claim exists)
    typ = raw_payload.get("typ")
    if typ and expected_type and typ != expected_type:
        raise AuthException(f"Invalid token type: expected {expected_type}, got {typ}")

    sub = raw_payload.get("sub")
    if not sub:
        raise AuthException("Token missing subject (user_id)")

    try:
        user_id = int(sub)
    except (ValueError, TypeError):
        user_id = sub

    return TokenPayload(
        sub=str(user_id),
        email=raw_payload.get("email"),
        user_type=raw_payload.get("user_type", "registered"),
        sid=raw_payload.get("sid"),
        provider=raw_payload.get("provider"),
        session_label=raw_payload.get("session_label"),
        iat=raw_payload.get("iat"),
        exp=exp,
    )
