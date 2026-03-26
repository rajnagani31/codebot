import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ...config import SessionLocal
from ...dependencies.auth import require_current_user
from ...repository.chat_repository import ChatRepository
from ...schema.chat_schema import ChatStreamRequest
from ...service.chat_service import ChatService
from ....workflow.openai_flow.openai_tool.openai_tool_graph import OpenAIToolGraph


router = APIRouter()


def get_chat_service() -> ChatService:
    return ChatService(ChatRepository(SessionLocal))


def encode_sse_event(event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"


@router.post("/chat/stream")
async def chat(
    request: ChatStreamRequest,
    current_user=Depends(require_current_user),
    chat_service: ChatService = Depends(get_chat_service),
):
    try:
        graph = OpenAIToolGraph()
        context = chat_service.prepare_stream(
            user_id=current_user.id,
            thread_id=request.thread_id,
            query=request.query,
            mode=request.mode,
            code=request.code,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Setup error: {exc}") from exc

    async def event_stream():
        full_response = ""
        try:
            yield encode_sse_event(
                "message.created",
                {
                    "thread_id": context.thread_id,
                    "user_message": {
                        "id": context.user_message.id,
                        "role": context.user_message.role,
                        "content": context.user_message.content,
                        "status": context.user_message.status,
                        "created_at": context.user_message.created_at.isoformat(),
                    },
                    "assistant_message": {
                        "id": context.assistant_message.id,
                        "role": context.assistant_message.role,
                        "content": "",
                        "status": context.assistant_message.status,
                        "created_at": context.assistant_message.created_at.isoformat(),
                    },
                },
            )

            async for chunk, _metadata in graph.app.astream(
                {
                    "messages": context.llm_messages,
                    "previous_context": context.previous_context,
                },
                stream_mode="messages",
            ):
                content = getattr(chunk, "content", "")
                if not content or not isinstance(content, str):
                    continue

                full_response += content
                yield encode_sse_event(
                    "message.delta",
                    {
                        "thread_id": context.thread_id,
                        "assistant_message_id": context.assistant_message.id,
                        "delta": content,
                    },
                )

            final_message = chat_service.finalize_stream(
                user_id=current_user.id,
                thread_id=context.thread_id,
                user_message_id=context.user_message.id,
                assistant_message_id=context.assistant_message.id,
                user_query=request.query,
                assistant_content=full_response,
                status="completed",
            )
            if final_message is not None:
                yield encode_sse_event(
                    "message.completed",
                    {
                        "thread_id": context.thread_id,
                        "assistant_message_id": final_message.id,
                        "status": final_message.status,
                        "content": final_message.content,
                        "completed_at": final_message.completed_at.isoformat() if final_message.completed_at else None,
                    },
                )
        except asyncio.CancelledError:
            chat_service.finalize_stream(
                user_id=current_user.id,
                thread_id=context.thread_id,
                user_message_id=context.user_message.id,
                assistant_message_id=context.assistant_message.id,
                user_query=request.query,
                assistant_content=full_response,
                status="stopped",
            )
            raise
        except Exception as stream_error:
            final_message = chat_service.finalize_stream(
                user_id=current_user.id,
                thread_id=context.thread_id,
                user_message_id=context.user_message.id,
                assistant_message_id=context.assistant_message.id,
                user_query=request.query,
                assistant_content=full_response,
                status="failed",
                error_text=str(stream_error),
            )
            payload = {
                "thread_id": context.thread_id,
                "assistant_message_id": context.assistant_message.id,
                "status": "failed",
                "error": str(stream_error),
                "content": full_response,
            }
            if final_message is not None and final_message.completed_at is not None:
                payload["completed_at"] = final_message.completed_at.isoformat()
            yield encode_sse_event("message.failed", payload)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
