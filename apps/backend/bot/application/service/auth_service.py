import base64
import calendar
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from urllib.parse import quote, urlencode

import requests
from fastapi import Request, Response

from ..config import (
    ACCESS_TOKEN_EXPIRES_SECONDS,
    AUTH_COOKIE_DOMAIN,
    AUTH_COOKIE_SAMESITE,
    AUTH_COOKIE_SECURE,
    FRONTEND_BASE_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REDIRECT_URI,
    GUEST_MESSAGE_LIMIT,
    GUEST_SESSION_EXPIRES_SECONDS,
    REFRESH_TOKEN_EXPIRES_SECONDS,
)
from ..model.chat_history import ChatUser, UserSession
from ..repository.auth_repository import AuthRepository

ACCESS_COOKIE_NAME = "codebot_access_token"
REFRESH_COOKIE_NAME = "codebot_refresh_token"
GOOGLE_STATE_TTL_SECONDS = 600


class AuthError(Exception):
    pass


class QuotaExceededError(AuthError):
    pass


@dataclass
class AuthenticatedPrincipal:
    id: int
    public_id: str
    session_label: str
    email: str | None
    display_name: str | None
    user_type: str
    auth_provider: str
    email_verified: bool
    session_id: int
    session_expires_at: datetime
    guest_message_limit: int | None
    guest_messages_used: int
    remaining_guest_messages: int | None


@dataclass
class SessionTokens:
    token: str
    access_token: str
    refresh_token: str
    expires_at: int
    refresh_expires_at: int
    user_id: int
    session_label: str
    session_id: int
    user: AuthenticatedPrincipal


class AuthService:
    def __init__(self, repository: AuthRepository, *, secret: str):
        self.repository = repository
        self.secret = secret.encode("utf-8")

    def create_guest_session(
        self, request: Request, client_session_id: str | None = None
    ) -> SessionTokens:
        existing = self._resolve_existing_principal(request)
        if existing is not None:
            return self._rotate_existing_session(existing, request)

        user = self.repository.create_guest_user()
        return self._create_session_bundle(
            user=user,
            auth_method="guest",
            request=request,
            client_session_id=client_session_id,
            is_guest=True,
            existing_session=None,
        )

    def signup(
        self,
        *,
        request: Request,
        email: str,
        password: str,
        display_name: str | None,
        client_session_id: str | None = None,
    ) -> SessionTokens:
        normalized_email = self._normalize_email(email)
        self._validate_email(normalized_email)
        self._validate_password(password)

        existing_user = self.repository.get_user_by_email(normalized_email) # might be 1 user or None
        current = self._resolve_existing_principal(request) # logged in user or None
        password_hash = self._hash_password(password)
        print('existing_user:', existing_user.id if existing_user else None)
        print('current:', current.id if current else None)
        if existing_user is not None and (
            current is None or existing_user.id != current.id
        ):
            raise AuthError("Email is already registered")

        if current is not None and current.user_type == "guest":
            upgraded_user = self.repository.upgrade_guest_user_to_password(
                user_id=current.id,
                email=normalized_email,
                display_name=display_name,
                password_hash=password_hash,
            )
            if upgraded_user is None:
                raise AuthError("Guest session could not be upgraded")
            return self._rotate_existing_session(
                current,
                request,
                user_override=upgraded_user,
                auth_method="password",
            )

        if current is not None and current.user_type != "guest":
            raise AuthError("You are already signed in")

        user = self.repository.create_password_user(
            email=normalized_email,
            display_name=display_name,
            password_hash=password_hash,
        )
        return self._create_session_bundle(
            user=user,
            auth_method="password",
            request=request,
            client_session_id=client_session_id,
            is_guest=False,
            existing_session=None,
        )

    def login(
        self,
        *,
        request: Request,
        email: str,
        password: str,
        client_session_id: str | None = None,
    ) -> SessionTokens:
        normalized_email = self._normalize_email(email)
        identity = self.repository.get_password_identity(normalized_email)
        if identity is None or not identity.password_hash:
            raise AuthError("Invalid email or password")

        if not self._verify_password(password, identity.password_hash):
            raise AuthError("Invalid email or password")

        user = self.repository.get_user(identity.user_id)
        if user is None or not user.is_active:
            raise AuthError("User account is unavailable")

        return self._create_session_bundle(
            user=user,
            auth_method="password",
            request=request,
            client_session_id=client_session_id,
            is_guest=False,
            existing_session=None,
        )

    def refresh_session(self, request: Request) -> SessionTokens:
        refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
        if not refresh_token:
            raise AuthError("Refresh token missing")

        payload = self._decode_token(refresh_token, expected_type="refresh")
        session_id = self._parse_session_id(payload.get("sid"))
        if session_id is None:
            raise AuthError("Refresh token session missing")

        record = self.repository.get_session_user(session_id)
        if record is None:
            raise AuthError("Session not found")
        self._validate_session(
            record.session, expected_token=refresh_token, token_kind="refresh"
        )
        if record.session.refresh_expires_at < datetime.utcnow():
            raise AuthError("Refresh session expired")
        if not record.user.is_active:
            raise AuthError("User account is inactive")

        return self._create_session_bundle(
            user=record.user,
            auth_method=record.session.auth_method,
            request=request,
            client_session_id=record.session.client_session_id,
            is_guest=record.user.user_type == "guest",
            existing_session=record.session,
        )

    def logout(self, request: Request) -> None:
        session_id = self._extract_session_id_from_request(request)
        if not session_id:
            return
        self.repository.revoke_session(session_id)

    def get_user_from_request(self, request: Request) -> AuthenticatedPrincipal:
        access_token = self._extract_access_token(request)
        if not access_token:
            raise AuthError("Authorization required")

        payload = self._decode_token(access_token, expected_type="access")
        session_id = self._parse_session_id(payload.get("sid"))
        if session_id is None:
            raise AuthError("Token session missing")

        record = self.repository.get_session_user(session_id)
        if record is None:
            raise AuthError("Session not found")

        self._validate_session(
            record.session, expected_token=access_token, token_kind="access"
        )
        if record.session.expires_at < datetime.utcnow():
            raise AuthError("Token expired")
        if not record.user.is_active:
            raise AuthError("User account is inactive")

        self.repository.touch_user(record.user.id)
        touched_session = self.repository.touch_session(record.session.id)
        session_for_principal = touched_session or record.session
        user_for_principal = self.repository.get_user(record.user.id) or record.user
        return self._build_principal(user_for_principal, session_for_principal)

    def consume_chat_credit(
        self, principal: AuthenticatedPrincipal
    ) -> AuthenticatedPrincipal:
        if principal.user_type != "guest":
            return principal

        if (
            principal.guest_message_limit is not None
            and principal.remaining_guest_messages is not None
        ):
            if principal.remaining_guest_messages <= 0:
                raise QuotaExceededError(
                    "Guest message limit reached. Sign in to continue."
                )

        session = self.repository.consume_message_credit(principal.session_id)
        if session is None:
            raise AuthError("Session not found")
        user = self.repository.get_user(principal.id)
        if user is None:
            raise AuthError("User not found")
        return self._build_principal(user, session)

    def google_login_url(self) -> tuple[bool, str | None, str | None]:
        if not self._google_oauth_enabled():
            return False, None, "Google OAuth is not configured"
        state = self._encode_token(
            {
                "typ": "google_state",
                "nonce": secrets.token_hex(16),
                "iat": int(time.time()),
                "exp": int(time.time()) + GOOGLE_STATE_TTL_SECONDS,
            }
        )
        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return (
            True,
            f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}",
            None,
        )

    def login_with_google_callback(
        self, *, request: Request, code: str, state: str
    ) -> SessionTokens:
        if not self._google_oauth_enabled():
            raise AuthError("Google OAuth is not configured")

        self._decode_token(state, expected_type="google_state")
        token_response = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        if token_response.status_code >= 400:
            raise AuthError("Google token exchange failed")

        token_payload = token_response.json()
        access_token = token_payload.get("access_token")
        if not access_token:
            raise AuthError("Google access token missing")

        profile_response = requests.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        if profile_response.status_code >= 400:
            raise AuthError("Google profile fetch failed")

        profile = profile_response.json()
        google_sub = profile.get("sub")
        if not google_sub:
            raise AuthError("Google user id missing")

        user = self.repository.create_or_link_google_user(
            google_sub=google_sub,
            email=profile.get("email"),
            display_name=profile.get("name"),
            email_verified=bool(profile.get("email_verified")),
        )
        return self._create_session_bundle(
            user=user,
            auth_method="google",
            request=request,
            client_session_id=None,
            is_guest=False,
            existing_session=None,
        )

    def apply_session_cookies(
        self, response: Response, session_tokens: SessionTokens
    ) -> None:
        self._set_cookie(
            response,
            key=ACCESS_COOKIE_NAME,
            value=session_tokens.access_token,
            expires_at=session_tokens.expires_at,
        )
        self._set_cookie(
            response,
            key=REFRESH_COOKIE_NAME,
            value=session_tokens.refresh_token,
            expires_at=session_tokens.refresh_expires_at,
        )
        response.delete_cookie("guest_token")

    def clear_session_cookies(self, response: Response) -> None:
        for key in (ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, "guest_token"):
            response.delete_cookie(
                key=key,
                domain=AUTH_COOKIE_DOMAIN,
                path="/",
                secure=AUTH_COOKIE_SECURE,
                httponly=True,
                samesite=AUTH_COOKIE_SAMESITE,
            )

    def build_frontend_redirect_url(self, *, error: str | None = None) -> str:
        if error:
            separator = "&" if "?" in FRONTEND_BASE_URL else "?"
            return f"{FRONTEND_BASE_URL}{separator}auth_error={quote(error)}"
        return FRONTEND_BASE_URL

    def _rotate_existing_session(
        self,
        principal: AuthenticatedPrincipal,
        request: Request,
        *,
        user_override: ChatUser | None = None,
        auth_method: str | None = None,
    ) -> SessionTokens:
        session = self.repository.get_session(principal.session_id)
        if session is None:
            raise AuthError("Session not found")
        user = user_override or self.repository.get_user(principal.id)
        if user is None:
            raise AuthError("User not found")
        return self._create_session_bundle(
            user=user,
            auth_method=auth_method or session.auth_method,
            request=request,
            client_session_id=session.client_session_id,
            is_guest=user.user_type == "guest",
            existing_session=session,
        )

    def _create_session_bundle(
        self,
        *,
        user: ChatUser,
        auth_method: str,
        request: Request,
        client_session_id: str | None,
        is_guest: bool,
        existing_session: UserSession | None,
    ) -> SessionTokens:
        access_expires_at_dt, refresh_expires_at_dt = self._build_expiry_window(
            is_guest=is_guest
        )
        session_id = existing_session.id if existing_session is not None else None
        if session_id is None:
            provisional_session = self.repository.create_session(
                user_id=user.id,
                auth_method=auth_method,
                session_token_hash=secrets.token_hex(64),
                refresh_token_hash=secrets.token_hex(64),
                expires_at=access_expires_at_dt,
                refresh_expires_at=refresh_expires_at_dt,
                client_session_id=client_session_id,
                user_agent=request.headers.get("User-Agent"),
                ip_address=request.client.host if request.client else None,
                message_limit=GUEST_MESSAGE_LIMIT if is_guest else None,
            )
            session_id = provisional_session.id
        access_token = self._encode_token(
            {
                "typ": "access",
                "sub": str(user.id),
                "sid": session_id,
                "session_label": user.session_label,
                "provider": auth_method,
                "user_type": user.user_type,
                "iat": int(time.time()),
                "exp": calendar.timegm(access_expires_at_dt.timetuple()),
            }
        )
        refresh_token = self._encode_token(
            {
                "typ": "refresh",
                "sub": str(user.id),
                "sid": session_id,
                "iat": int(time.time()),
                "exp": calendar.timegm(refresh_expires_at_dt.timetuple()),
            }
        )
        access_token_hash = self._hash_token(access_token)
        refresh_token_hash = self._hash_token(refresh_token)

        user_session = self.repository.rotate_session_tokens(
            session_id=session_id,
            session_token_hash=access_token_hash,
            refresh_token_hash=refresh_token_hash,
            expires_at=access_expires_at_dt,
            refresh_expires_at=refresh_expires_at_dt,
        )
        if user_session is None:
            raise AuthError("Session not found")

        principal = self._build_principal(user, user_session)
        expires_at = calendar.timegm(access_expires_at_dt.timetuple())
        refresh_expires_at = calendar.timegm(refresh_expires_at_dt.timetuple())
        return SessionTokens(
            token=access_token,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            refresh_expires_at=refresh_expires_at,
            user_id=user.id,
            session_label=user.session_label,
            session_id=user_session.id,
            user=principal,
        )

    def _build_principal(
        self, user: ChatUser, session: UserSession
    ) -> AuthenticatedPrincipal:
        remaining_guest_messages = None
        if session.message_limit is not None:
            remaining_guest_messages = max(
                session.message_limit - session.message_count, 0
            )

        return AuthenticatedPrincipal(
            id=user.id,
            public_id=user.public_id,
            session_label=user.session_label,
            email=user.email,
            display_name=user.display_name,
            user_type=user.user_type,
            auth_provider=session.auth_method,
            email_verified=user.email_verified,
            session_id=session.id,
            session_expires_at=session.expires_at,
            guest_message_limit=session.message_limit,
            guest_messages_used=session.message_count,
            remaining_guest_messages=remaining_guest_messages,
        )

    def _resolve_existing_principal(
        self, request: Request
    ) -> AuthenticatedPrincipal | None:
        try:
            return self.get_user_from_request(request)
        except AuthError:
            return None

    def _extract_access_token(self, request: Request) -> str | None:
        cookie_token = request.cookies.get(ACCESS_COOKIE_NAME) or request.cookies.get(
            "guest_token"
        )
        if cookie_token:
            return cookie_token

        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:].strip()
        return None

    def _extract_session_id_from_request(self, request: Request) -> int | None:
        for token in (
            self._extract_access_token(request),
            request.cookies.get(REFRESH_COOKIE_NAME),
        ):
            if not token:
                continue
            try:
                payload = self._decode_token(token)
            except AuthError:
                continue
            session_id = self._parse_session_id(payload.get("sid"))
            if session_id is not None:
                return session_id
        return None

    def _parse_session_id(self, value: object) -> int | None:
        if value is None:
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    def _validate_session(
        self, session: UserSession, *, expected_token: str, token_kind: str
    ) -> None:
        if not session.is_active or session.revoked_at is not None:
            raise AuthError("Session revoked")

        hashed = self._hash_token(expected_token)
        stored_hash = (
            session.session_token_hash
            if token_kind == "access"
            else session.refresh_token_hash
        )
        if not hmac.compare_digest(stored_hash, hashed):
            raise AuthError("Session token invalid")

    def _set_cookie(
        self, response: Response, *, key: str, value: str, expires_at: int
    ) -> None:
        max_age = max(expires_at - int(time.time()), 0)
        response.set_cookie(
            key=key,
            value=value,
            httponly=True,
            secure=AUTH_COOKIE_SECURE,
            samesite=AUTH_COOKIE_SAMESITE,
            domain=AUTH_COOKIE_DOMAIN,
            path="/",
            max_age=max_age,
        )

    def _build_expiry_window(self, *, is_guest: bool) -> tuple[datetime, datetime]:
        now = datetime.utcnow()
        if is_guest:
            refresh_ttl = min(
                GUEST_SESSION_EXPIRES_SECONDS, REFRESH_TOKEN_EXPIRES_SECONDS
            )
            refresh_expires_at = now + timedelta(seconds=refresh_ttl)
            access_ttl = min(ACCESS_TOKEN_EXPIRES_SECONDS, refresh_ttl)
            access_expires_at = now + timedelta(seconds=access_ttl)
            return access_expires_at, refresh_expires_at

        return (
            now + timedelta(seconds=ACCESS_TOKEN_EXPIRES_SECONDS),
            now + timedelta(seconds=REFRESH_TOKEN_EXPIRES_SECONDS),
        )

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def _validate_email(self, email: str) -> None:
        if "@" not in email or "." not in email.split("@")[-1]:
            raise AuthError("Email format is invalid")

    def _validate_password(self, password: str) -> None:
        if len(password) < 8:
            raise AuthError("Password must be at least 8 characters long")

    def _hash_password(self, password: str) -> str:
        iterations = 260000
        salt = os.urandom(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return "pbkdf2_sha256${}${}${}".format(
            iterations,
            base64.urlsafe_b64encode(salt).decode("utf-8"),
            base64.urlsafe_b64encode(digest).decode("utf-8"),
        )

    def _verify_password(self, password: str, stored_password: str) -> bool:
        try:
            scheme, iterations_str, salt_b64, digest_b64 = stored_password.split("$", 3)
        except ValueError:
            return False
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iterations_str)
        salt = base64.urlsafe_b64decode(salt_b64.encode("utf-8"))
        expected_digest = base64.urlsafe_b64decode(digest_b64.encode("utf-8"))
        candidate = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, iterations
        )
        return hmac.compare_digest(candidate, expected_digest)

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _encode_token(self, payload: dict) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        encoded_header = self._b64encode(
            json.dumps(header, separators=(",", ":")).encode("utf-8")
        )
        encoded_payload = self._b64encode(
            json.dumps(payload, separators=(",", ":")).encode("utf-8")
        )
        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        signature = hmac.new(self.secret, signing_input, hashlib.sha256).digest()
        encoded_signature = self._b64encode(signature)
        return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

    def _decode_token(self, token: str, *, expected_type: str | None = None) -> dict:
        try:
            encoded_header, encoded_payload, encoded_signature = token.split(".")
        except ValueError as exc:
            raise AuthError("Token format invalid") from exc

        signing_input = f"{encoded_header}.{encoded_payload}".encode("utf-8")
        expected_signature = hmac.new(
            self.secret, signing_input, hashlib.sha256
        ).digest()
        actual_signature = self._b64decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, actual_signature):
            raise AuthError("Token signature invalid")

        payload = json.loads(self._b64decode(encoded_payload).decode("utf-8"))
        if int(payload.get("exp", 0)) < int(time.time()):
            raise AuthError("Token expired")
        if expected_type is not None and payload.get("typ") != expected_type:
            raise AuthError("Token type invalid")
        return payload

    def _b64encode(self, value: bytes) -> str:
        return base64.urlsafe_b64encode(value).rstrip(b"=").decode("utf-8")

    def _b64decode(self, value: str) -> bytes:
        padding = "=" * (-len(value) % 4)
        return base64.urlsafe_b64decode(f"{value}{padding}".encode("utf-8"))

    def _google_oauth_enabled(self) -> bool:
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)
