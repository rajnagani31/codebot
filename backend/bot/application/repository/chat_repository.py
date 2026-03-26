import uuid
from datetime import datetime

from sqlalchemy import func, select

from ..model.chat_history import ChatMessage, ChatThread, ChatUser


class ChatRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def create_user(self) -> ChatUser:
        session = self.session_factory()
        try:
            user = ChatUser(session_label=uuid.uuid4().hex[:12])
            session.add(user)
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

    def touch_user(self, user_id: int) -> ChatUser | None:
        session = self.session_factory()
        try:
            user = session.get(ChatUser, user_id)
            if user is None:
                return None
            user.last_seen_at = datetime.utcnow()
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def create_thread(
        self,
        *,
        user_id: int,
        title: str,
        mode: str,
        client_session_id: str | None = None,
    ) -> ChatThread:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            thread = ChatThread(
                id=uuid.uuid4().hex,
                user_id=user_id,
                title=title.strip() or "New chat",
                mode=mode,
                client_session_id=client_session_id,
                created_at=now,
                updated_at=now,
            )
            session.add(thread)
            session.commit()
            session.refresh(thread)
            return thread
        finally:
            session.close()

    def get_thread(self, *, user_id: int, thread_id: str) -> ChatThread | None:
        session = self.session_factory()
        try:
            stmt = select(ChatThread).where(
                ChatThread.id == thread_id,
                ChatThread.user_id == user_id,
                ChatThread.is_archived.is_(False),
            )
            return session.execute(stmt).scalar_one_or_none()
        finally:
            session.close()

    def list_threads(self, *, user_id: int) -> list[dict]:
        session = self.session_factory()
        try:
            stmt = (
                select(ChatThread)
                .where(ChatThread.user_id == user_id, ChatThread.is_archived.is_(False))
                .order_by(ChatThread.updated_at.desc())
            )
            threads = session.execute(stmt).scalars().all()
            result: list[dict] = []

            for thread in threads:
                message_count = session.scalar(
                    select(func.count(ChatMessage.id)).where(ChatMessage.thread_id == thread.id)
                ) or 0
                last_message = session.execute(
                    select(ChatMessage)
                    .where(ChatMessage.thread_id == thread.id)
                    .order_by(ChatMessage.sequence_no.desc())
                    .limit(1)
                ).scalar_one_or_none()

                result.append(
                    {
                        "id": thread.id,
                        "title": thread.title,
                        "mode": thread.mode,
                        "updated_at": thread.updated_at,
                        "last_message_at": thread.last_message_at,
                        "preview": (last_message.content[:160] if last_message else ""),
                        "message_count": message_count,
                    }
                )

            return result
        finally:
            session.close()

    def list_messages(self, *, user_id: int, thread_id: str) -> list[ChatMessage]:
        session = self.session_factory()
        try:
            stmt = (
                select(ChatMessage)
                .where(ChatMessage.user_id == user_id, ChatMessage.thread_id == thread_id)
                .order_by(ChatMessage.sequence_no.asc())
            )
            return list(session.execute(stmt).scalars().all())
        finally:
            session.close()

    def recent_messages(self, *, user_id: int, thread_id: str, limit: int = 12) -> list[ChatMessage]:
        session = self.session_factory()
        try:
            stmt = (
                select(ChatMessage)
                .where(
                    ChatMessage.user_id == user_id,
                    ChatMessage.thread_id == thread_id,
                    ChatMessage.role.in_(("user", "assistant")),
                    ChatMessage.status.in_(("completed", "stopped")),
                )
                .order_by(ChatMessage.sequence_no.desc())
                .limit(limit)
            )
            rows = list(session.execute(stmt).scalars().all())
            rows.reverse()
            return rows
        finally:
            session.close()

    def create_message(
        self,
        *,
        thread_id: str,
        user_id: int,
        role: str,
        content: str,
        status: str,
        model_name: str | None = None,
        code_context: str | None = None,
        error_text: str | None = None,
        metadata_json: dict | None = None,
        completed_at: datetime | None = None,
    ) -> ChatMessage:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            sequence_no = self._next_sequence_no(session, thread_id)
            message = ChatMessage(
                id=uuid.uuid4().hex,
                thread_id=thread_id,
                user_id=user_id,
                role=role,
                content=content,
                status=status,
                sequence_no=sequence_no,
                model_name=model_name,
                code_context=code_context,
                error_text=error_text,
                metadata_json=metadata_json,
                created_at=now,
                completed_at=completed_at,
            )
            session.add(message)

            thread = session.get(ChatThread, thread_id)
            if thread is not None:
                thread.updated_at = now
                thread.last_message_at = now

            session.commit()
            session.refresh(message)
            return message
        finally:
            session.close()

    def finalize_message(
        self,
        *,
        message_id: str,
        content: str,
        status: str,
        error_text: str | None = None,
        metadata_json: dict | None = None,
    ) -> ChatMessage | None:
        session = self.session_factory()
        now = datetime.utcnow()
        try:
            # This ORM Update query on one exect messge_id
            message = session.get(ChatMessage, message_id)
            if message is None:
                return None

            message.content = content
            message.status = status
            message.error_text = error_text
            message.metadata_json = metadata_json
            message.completed_at = now

            thread = session.get(ChatThread, message.thread_id)
            # Update date time
            if thread is not None:
                thread.updated_at = now
                thread.last_message_at = now
                
            # Save date with new assitent response
            session.commit()
            session.refresh(message)
            return message
        finally:
            session.close()

    def _next_sequence_no(self, session, thread_id: str) -> int:
        current_max = session.scalar(
            select(func.max(ChatMessage.sequence_no)).where(ChatMessage.thread_id == thread_id)
        )
        return int(current_max or 0) + 1
