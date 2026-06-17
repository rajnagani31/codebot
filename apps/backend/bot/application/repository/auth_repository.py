import secrets
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select

from ..model.chat_history import AuthIdentity, ChatUser, UserSession


@dataclass
class SessionUserRecord:
    user: ChatUser
    session: UserSession


class AuthRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create_guest_user(self) -> ChatUser:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user = ChatUser(
                public_id=f"usr_{secrets.token_hex(16)}",
                session_label=secrets.token_hex(6),
                user_type="guest",
                primary_auth_provider="guest",
                email_verified=False,
                is_active=True,
                created_at=now,
                updated_at=now,
                last_seen_at=now,
                last_login_at=now,
            )
            session.add(user)
            session.flush()

            session.add(
                AuthIdentity(
                    user_id=user.id,
                    provider="guest",
                    provider_user_id=user.public_id,
                    provider_email=None,
                    password_hash=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def create_password_user(
        self, *, email: str, display_name: str | None, password_hash: str
    ) -> ChatUser:
        session = self.session_factory()
        now = datetime.utcnow()
        normalized_email = email.lower()
        try:
            user = ChatUser(
                public_id=f"usr_{secrets.token_hex(16)}",
                session_label=secrets.token_hex(6),
                email=normalized_email,
                display_name=display_name,
                user_type="registered",
                primary_auth_provider="password",
                email_verified=False,
                is_active=True,
                created_at=now,
                updated_at=now,
                last_seen_at=now,
                last_login_at=now,
            )
            session.add(user)
            session.flush()

            session.add(
                AuthIdentity(
                    user_id=user.id,
                    provider="password",
                    provider_user_id=normalized_email,
                    provider_email=normalized_email,
                    password_hash=password_hash,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def upgrade_guest_user_to_password(
        self,
        *,
        user_id: int,
        email: str,
        display_name: str | None,
        password_hash: str,
    ) -> ChatUser | None:
        session = self.session_factory()
        now = datetime.utcnow()
        normalized_email = email.lower()
        try:
            user = session.get(ChatUser, user_id)
            if user is None:
                return None

            user.email = normalized_email
            user.display_name = display_name or user.display_name
            user.user_type = "registered"
            user.primary_auth_provider = "password"
            user.updated_at = now
            user.last_login_at = now
            user.last_seen_at = now

            identity = session.execute(
                select(AuthIdentity).where(
                    AuthIdentity.user_id == user_id,
                    AuthIdentity.provider == "password",
                )
            ).scalar_one_or_none()
            if identity is None:
                identity = AuthIdentity(
                    user_id=user.id,
                    provider="password",
                    provider_user_id=normalized_email,
                    provider_email=normalized_email,
                    password_hash=password_hash,
                    created_at=now,
                    updated_at=now,
                )
                session.add(identity)
            else:
                identity.provider_user_id = normalized_email
                identity.provider_email = normalized_email
                identity.password_hash = password_hash
                identity.updated_at = now

            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def create_or_link_google_user(
        self,
        *,
        google_sub: str,
        email: str | None,
        display_name: str | None,
        email_verified: bool,
    ) -> ChatUser:
        session = self.session_factory()
        now = datetime.utcnow()
        normalized_email = email.lower() if email else None
        try:
            existing_identity = session.execute(
                select(AuthIdentity).where(
                    AuthIdentity.provider == "google",
                    AuthIdentity.provider_user_id == google_sub,
                )
            ).scalar_one_or_none()
            if existing_identity is not None:
                user = session.get(ChatUser, existing_identity.user_id)
                if user is None:
                    raise ValueError("Google identity user missing")
                if normalized_email and not user.email:
                    user.email = normalized_email
                if display_name and not user.display_name:
                    user.display_name = display_name
                user.primary_auth_provider = "google"
                user.user_type = "registered"
                user.email_verified = email_verified or user.email_verified
                user.updated_at = now
                user.last_login_at = now
                user.last_seen_at = now
                existing_identity.provider_email = normalized_email
                existing_identity.updated_at = now
                session.commit()
                session.refresh(user)
                return user

            user = None
            if normalized_email:
                user = session.execute(
                    select(ChatUser).where(ChatUser.email == normalized_email)
                ).scalar_one_or_none()

            if user is None:
                user = ChatUser(
                    public_id=f"usr_{secrets.token_hex(16)}",
                    session_label=secrets.token_hex(6),
                    email=normalized_email,
                    display_name=display_name,
                    user_type="registered",
                    primary_auth_provider="google",
                    email_verified=email_verified,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                    last_seen_at=now,
                    last_login_at=now,
                )
                session.add(user)
                session.flush()
            else:
                if display_name and not user.display_name:
                    user.display_name = display_name
                user.primary_auth_provider = "google"
                user.user_type = "registered"
                user.email_verified = email_verified or user.email_verified
                user.updated_at = now
                user.last_login_at = now
                user.last_seen_at = now

            session.add(
                AuthIdentity(
                    user_id=user.id,
                    provider="google",
                    provider_user_id=google_sub,
                    provider_email=normalized_email,
                    password_hash=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def get_user(self, user_id: int) -> ChatUser | None:
        session = self.session_factory()
        try:
            return session.get(ChatUser, user_id)
        finally:
            session.close()

    def get_user_by_email(self, email: str) -> ChatUser | None:
        session = self.session_factory()
        try:
            return session.execute(
                select(ChatUser).where(ChatUser.email == email.lower())
            ).scalar_one_or_none()
        finally:
            session.close()

    def get_identity(
        self, *, provider: str, provider_user_id: str
    ) -> AuthIdentity | None:
        session = self.session_factory()
        try:
            return session.execute(
                select(AuthIdentity).where(
                    AuthIdentity.provider == provider,
                    AuthIdentity.provider_user_id == provider_user_id,
                )
            ).scalar_one_or_none()
        finally:
            session.close()

    def get_password_identity(self, email: str) -> AuthIdentity | None:
        return self.get_identity(provider="password", provider_user_id=email.lower())

    def create_session(
        self,
        *,
        user_id: int,
        auth_method: str,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
        refresh_expires_at: datetime,
        client_session_id: str | None,
        user_agent: str | None,
        ip_address: str | None,
        message_limit: int | None,
    ) -> UserSession:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user_session = UserSession(
                user_id=user_id,
                auth_method=auth_method,
                session_token_hash=session_token_hash,
                refresh_token_hash=refresh_token_hash,
                client_session_id=client_session_id,
                user_agent=user_agent,
                ip_address=ip_address,
                is_active=True,
                message_limit=message_limit,
                message_count=0,
                created_at=now,
                expires_at=expires_at,
                refresh_expires_at=refresh_expires_at,
                last_seen_at=now,
                revoked_at=None,
            )
            session.add(user_session)
            session.commit()
            session.refresh(user_session)
            return user_session
        finally:
            session.close()

    def get_session(self, session_id: int) -> UserSession | None:
        session = self.session_factory()
        try:
            return session.get(UserSession, session_id)
        finally:
            session.close()

    def get_session_user(self, session_id: int) -> SessionUserRecord | None:
        session = self.session_factory()
        try:
            user_session = session.get(UserSession, session_id)
            if user_session is None:
                return None
            user = session.get(ChatUser, user_session.user_id)
            if user is None:
                return None
            session.expunge(user_session)
            session.expunge(user)
            return SessionUserRecord(user=user, session=user_session)
        finally:
            session.close()

    def touch_session(self, session_id: int) -> UserSession | None:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user_session = session.get(UserSession, session_id)
            if user_session is None:
                return None
            user_session.last_seen_at = now
            session.commit()
            session.refresh(user_session)
            return user_session
        finally:
            session.close()

    def touch_user(self, user_id: int) -> ChatUser | None:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user = session.get(ChatUser, user_id)
            if user is None:
                return None
            user.last_seen_at = now
            user.updated_at = now
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def rotate_session_tokens(
        self,
        *,
        session_id: int,
        session_token_hash: str,
        refresh_token_hash: str,
        expires_at: datetime,
        refresh_expires_at: datetime,
    ) -> UserSession | None:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user_session = session.get(UserSession, session_id)
            if user_session is None:
                return None
            user_session.session_token_hash = session_token_hash
            user_session.refresh_token_hash = refresh_token_hash
            user_session.expires_at = expires_at
            user_session.refresh_expires_at = refresh_expires_at
            user_session.last_seen_at = now
            session.commit()
            session.refresh(user_session)
            return user_session
        finally:
            session.close()

    def revoke_session(self, session_id: int) -> UserSession | None:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user_session = session.get(UserSession, session_id)
            if user_session is None:
                return None
            user_session.is_active = False
            user_session.revoked_at = now
            user_session.last_seen_at = now
            session.commit()
            session.refresh(user_session)
            return user_session
        finally:
            session.close()

    def consume_message_credit(self, session_id: int) -> UserSession | None:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            user_session = session.get(UserSession, session_id)
            if user_session is None:
                return None
            user_session.message_count += 1
            user_session.last_seen_at = now
            session.commit()
            session.refresh(user_session)
            return user_session
        finally:
            session.close()
