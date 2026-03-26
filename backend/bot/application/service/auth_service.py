import base64
import hashlib
import hmac
import json
import time

from ..repository.chat_repository import ChatRepository


class AuthError(Exception):
    pass


class AuthService:
    def __init__(self, repository: ChatRepository, *, secret: str, expires_in_seconds: int):
        self.repository = repository
        self.secret = secret.encode("utf-8")
        self.expires_in_seconds = expires_in_seconds

    def create_guest_session(self) -> dict:
        user = self.repository.create_user()
        expires_at = int(time.time()) + self.expires_in_seconds
        token = self._encode_token(
            {
                "sub": str(user.id),
                "session_label": user.session_label,
                "iat": int(time.time()),
                "exp": expires_at,
            }
        )
        return {
            "token": token,
            "user_id": user.id,
            "session_label": user.session_label,
            "expires_at": expires_at,
        }

    def get_user_from_token(self, token: str):
        payload = self._decode_token(token)
        subject = payload.get("sub")
        if subject is None:
            raise AuthError("Token subject missing")

        try:
            user_id = int(subject)
        except (TypeError, ValueError) as exc:
            raise AuthError("Token subject invalid") from exc

        user = self.repository.touch_user(user_id)
        if user is None:
            raise AuthError("User not found")

        return user

    def _encode_token(self, payload: dict) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        encoded_header = self._b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        encoded_payload = self._b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        signature = hmac.new(self.secret, signing_input, hashlib.sha256).digest()
        encoded_signature = self._b64encode(signature)
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    def _decode_token(self, token: str) -> dict:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise AuthError("Token format invalid") from exc

        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_signature = hmac.new(self.secret, signing_input, hashlib.sha256).digest()
        actual_signature = self._b64decode(encoded_signature)

        if not hmac.compare_digest(expected_signature, actual_signature):
            raise AuthError("Token signature invalid")

        payload = json.loads(self._b64decode(encoded_payload).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise AuthError("Token expired")

        return payload

    def _b64encode(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")

    def _b64decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))
