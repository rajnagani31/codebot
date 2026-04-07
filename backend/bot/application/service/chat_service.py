from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage

from ...workflow.pg_vector.pg_vector_service import PGVectorService
from ..repository.chat_repository import ChatRepository
from ...workflow.qudrant.vector_service import QdrantVectorService


@dataclass
class ChatStreamContext:
    thread_id: str
    user_message: object
    assistant_message: object
    llm_messages: list
    previous_context: str


class ChatService:
    def __init__(self, repository: ChatRepository):
        self.repository = repository

    def create_thread(
        self,
        *,
        user_id: int,
        title: str,
        mode: str,
        client_session_id: str | None = None,
    ):
        return self.repository.create_thread(
            user_id=user_id,
            title=title,
            mode=mode,
            client_session_id=client_session_id,
        )

    def list_threads(self, *, user_id: int) -> list[dict]:
        return self.repository.list_threads(user_id=user_id)

    def list_messages(self, *, user_id: int, thread_id: str):
        return self.repository.list_messages(user_id=user_id, thread_id=thread_id)

    def prepare_stream(
        self,
        *,
        user_id: int,
        thread_id: str,
        query: str,
        mode: str,
        code: str | None = None,
        model_name: str = "gpt-4o-mini",
        user_metadata: dict | None = None,
        assistant_metadata: dict | None = None,
    ) -> ChatStreamContext:
        thread = self.repository.get_thread(user_id=user_id, thread_id=thread_id)
        if thread is None:
            raise KeyError("Thread not found")

        previous_messages = self.repository.recent_messages(
            user_id=user_id, thread_id=thread_id
        )
        user_message = self.repository.create_message(
            thread_id=thread_id,
            user_id=user_id,
            role="user",
            content=query,
            status="completed",
            code_context=code,
            metadata_json=user_metadata,
        )
        assistant_message = self.repository.create_message(
            thread_id=thread_id,
            user_id=user_id,
            role="assistant",
            content="",
            status="streaming",
            model_name=model_name,
            code_context=code,
            metadata_json=assistant_metadata,
        )

        pg_vector_service = PGVectorService()
        # Qdrant_vector_service = QdrantVectorService()
        # history = pg_vector_service.search(user_id=user_id, query=query)
        history = "nothing to compere" # TODO: re-enable retrieval after vector search is optimized
        llm_messages = self._build_llm_messages(previous_messages, query)

        return ChatStreamContext(
            thread_id=thread_id,
            user_message=user_message,
            assistant_message=assistant_message,
            llm_messages=llm_messages,
            previous_context="\n".join(history),
        )

    def finalize_stream(
        self,
        *,
        user_id: int,
        thread_id: str,
        user_message_id: str,
        assistant_message_id: str,
        user_query: str,
        assistant_content: str,
        status: str,
        error_text: str | None = None,
        metadata_json: dict | None = None,
    ):
        message = self.repository.finalize_message(
            message_id=assistant_message_id,
            content=assistant_content,
            status=status,
            error_text=error_text,
            metadata_json=metadata_json,
        )

        if message is None:
            return None

        if status == "completed" and assistant_content.strip():
            pg_vector_service = PGVectorService()
            pg_vector_service.store(
                user_id=user_id,
                text=user_query,
                type_="user_message",
                metadata={
                    "thread_id": thread_id,
                    "message_id": user_message_id,
                    "role": "user",
                },
            )
            pg_vector_service.store(
                user_id=user_id,
                text=assistant_content,
                type_="assistant_message",
                metadata={
                    "thread_id": thread_id,
                    "message_id": assistant_message_id,
                    "role": "assistant",
                },
            )

        return message

    def _build_llm_messages(self, previous_messages, query: str) -> list:
        llm_messages = []

        for message in previous_messages:
            if message.role == "user":
                llm_messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                llm_messages.append(AIMessage(content=message.content))

        llm_messages.append(HumanMessage(content=query))
        return llm_messages
