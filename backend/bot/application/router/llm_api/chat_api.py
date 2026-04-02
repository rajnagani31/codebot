import asyncio
import json

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

from ...config import SessionLocal
from ...dependencies.auth import get_auth_service, require_current_user
from ...repository.chat_repository import ChatRepository
from ...schema.chat_schema import (
    ChatStreamRequest,
    MessageMetadata,
    MessageProcessMetadata,
)
from ...service.auth_service import AuthService, QuotaExceededError
from ...service.chat_service import ChatService
from ...service.choice_resolver import ChoiceResolver, ChoiceResolverInput
from ....workflow.openai_flow.openai_tool.openai_tool_graph import (
    GraphRunContext,
    OpenAIToolGraph,
)

router = APIRouter(tags=["chat_bot"])


def get_chat_service() -> ChatService:
    return ChatService(ChatRepository(SessionLocal))


def encode_sse_event(event_name: str, payload: dict) -> str:
    return f"event: {event_name}\ndata: {json.dumps(payload, default=str)}\n\n"


@router.post("/chat/stream")
async def chat(
    request: ChatStreamRequest,
    current_user=Depends(require_current_user),
    chat_service: ChatService = Depends(get_chat_service),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        current_user = auth_service.consume_chat_credit(current_user)
        resolved_choice = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query=request.query,
                mode=request.mode,
                choice_config=request.choice_config,
                use_web=request.use_web,
            )
        )
        base_metadata = MessageMetadata(
            process=MessageProcessMetadata(
                choice_config=resolved_choice.choice_config.model_dump(),
                resolved_choice_config=resolved_choice.model_dump(),
                execution_mode="pending",
                tools_used=[],
                web_search_used=False,
                model_name=resolved_choice.model_name,
                prompt_name=resolved_choice.prompt_name,
            ),
        ).model_dump()
        context = chat_service.prepare_stream(
            user_id=current_user.id,
            thread_id=request.thread_id,
            query=request.query,
            mode=request.mode,
            code=request.code,
            model_name=resolved_choice.model_name,
            user_metadata=base_metadata,
            assistant_metadata=base_metadata,
        )
        graph = OpenAIToolGraph(
            resolved_choice=resolved_choice,
            run_context=GraphRunContext(
                user_id=current_user.id,
                thread_id=context.thread_id,
                assistant_message_id=context.assistant_message.id,
            ),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except QuotaExceededError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Setup error: {exc}") from exc

    async def event_stream():
        full_response = ""
        final_metadata = base_metadata
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
                        "metadata_json": context.user_message.metadata_json,
                    },
                    "assistant_message": {
                        "id": context.assistant_message.id,
                        "role": context.assistant_message.role,
                        "content": "",
                        "status": context.assistant_message.status,
                        "created_at": context.assistant_message.created_at.isoformat(),
                        "metadata_json": context.assistant_message.metadata_json,
                    },
                },
            )

            async for (
                event
            ) in graph.run_stream(  # here send everything to llm and get a response in streaming
                messages=context.llm_messages,
                previous_context=context.previous_context,
            ):
                if event["type"] == "delta":
                    content = event["delta"]
                    full_response += content
                    yield encode_sse_event(
                        "message.delta",
                        {
                            "thread_id": context.thread_id,
                            "assistant_message_id": context.assistant_message.id,
                            "delta": content,
                        },
                    )
                    continue

                if event["type"] == "progress":
                    yield encode_sse_event(
                        "message.progress",
                        {
                            "thread_id": context.thread_id,
                            "assistant_message_id": context.assistant_message.id,
                            "stage": event["stage"],
                            "label": event["label"],
                        },
                    )
                    continue

                if event["type"] == "complete":
                    final_metadata = event["metadata"]
                    yield encode_sse_event(
                        "message.sources",
                        {
                            "thread_id": context.thread_id,
                            "assistant_message_id": context.assistant_message.id,
                            "metadata_json": final_metadata,
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
                metadata_json=final_metadata,
            )
            if final_message is not None:
                yield encode_sse_event(
                    "message.completed",
                    {
                        "thread_id": context.thread_id,
                        "assistant_message_id": final_message.id,
                        "status": final_message.status,
                        "content": final_message.content,
                        "completed_at": (
                            final_message.completed_at.isoformat()
                            if final_message.completed_at
                            else None
                        ),
                        "metadata_json": final_metadata,
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
                metadata_json=final_metadata,
            )
            raise
        except Exception as stream_error:
            failed_metadata = dict(final_metadata or {})
            failed_process = dict((failed_metadata.get("process") or {}))
            failed_process["execution_mode"] = (
                failed_process.get("execution_mode") or "failed"
            )
            failed_metadata["process"] = failed_process
            final_message = chat_service.finalize_stream(
                user_id=current_user.id,
                thread_id=context.thread_id,
                user_message_id=context.user_message.id,
                assistant_message_id=context.assistant_message.id,
                user_query=request.query,
                assistant_content=full_response,
                status="failed",
                error_text=str(stream_error),
                metadata_json=failed_metadata,
            )
            payload = {
                "thread_id": context.thread_id,
                "assistant_message_id": context.assistant_message.id,
                "status": "failed",
                "error": str(stream_error),
                "content": full_response,
                "metadata_json": failed_metadata,
            }
            if final_message is not None and final_message.completed_at is not None:
                payload["completed_at"] = final_message.completed_at.isoformat()
            yield encode_sse_event("message.failed", payload)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/chat/stream/test")
async def chat_test(
    user: str,
    current_user=Depends(require_current_user),
):
    return JSONResponse(
        {
            "user": user,
            "current_user": {
                "id": current_user.id,
                "email": current_user.email,
            },
        }
    )
