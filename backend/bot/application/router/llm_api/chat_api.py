import asyncio
import json
from pydantic import BaseModel
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
import uuid
from datetime import datetime

from sqlalchemy import func, select

from ...model.chat_history import ChatMessage, ChatThread, ChatUser

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
            )
        )
        print(f"Resolved choice: {resolved_choice}")
        base_metadata = MessageMetadata(
            process=MessageProcessMetadata(
                choice_config=resolved_choice.choice_config.model_dump(),
                resolved_choice_config=resolved_choice.model_dump(),
                execution_mode="pending",
                tools_used=[],
                web_search_used=False,
                current_info_requested=resolved_choice.current_info_requested,
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



class SQLAlchemyTestRequest(BaseModel):
    id :int
    user_id: str
    title: str
    mode: str
    client :str
    is_archived: bool
    updated_at: datetime
    created_at: datetime

@router.post("/chat/stream/test")
async def chat_test(
    user: str,
    # current_user=Depends(require_current_user),
):
    # Fiter in SqlAlchemy model to get user details based on email or username
    session = SessionLocal()
    users = []
    # get_all_user_thread = session.query(ChatThread).all()
    get_all_user_thread = select(ChatThread)
    result = session.execute(get_all_user_thread)
    users_list = result.scalars().all()
    for user in users_list:
        users.append(
            {
                "id": user.id,
                "email": user.user_id,
                "title": user.title,
                "mode": user.mode,
                "client": user.client_session_id,
                "is_active": user.is_archived,
                # "updated_at": str(user.updated_at),
                # "created_at": str(user.created_at),
                "updated_at": user.updated_at.isoformat() if user.updated_at else None, # .isoformat is convers datetime into JSON
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
        )

    "--------------------------------------------------------------------------------------"
    # get threads based on user_id and count
    # get_user_thread = select(func.count()).select_from(ChatThread).where(ChatThread.user_id == 138) _> count
    # get_user_thread = select(ChatThread.id, ChatThread.user_id).where(ChatThread.user_id == 138) # get all threads for user_id 138
    get_user_thread = select(ChatThread).where(ChatThread.user_id == 138) # get all threads for user_id 138
    result = session.execute(get_user_thread)
    # rows = result.fetchall()
    user_threads = result.scalars().all()
    user_thread_list = []

    for thread in user_threads: 

        user_thread_list.append(
            {
                "id": thread.id,
                "email": thread.user_id,
                "title": thread.title,
                "mode": thread.mode,
                "client": thread.client_session_id,
                "is_active": thread.is_archived,
                "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
                "created_at": thread.created_at.isoformat() if thread.created_at else None,
            }
    )
        

    "--------------------------------------------------------------------------------------"
    # insert data in database using SQLAlchemy
    new_thread = [
        ChatThread(id=7,user_id=138,title="Test Thread",mode="test",client_session_id="test_client",created_at=datetime.utcnow(),updated_at=datetime.utcnow()),
        ChatThread(id=8,user_id=138,title="Test Thread",mode="test",client_session_id="test_client",created_at=datetime.utcnow(),updated_at=datetime.utcnow()),
        ChatThread(id=9,user_id=138,title="Test Thread",mode="test",client_session_id="test_client",created_at=datetime.utcnow(),updated_at=datetime.utcnow()),
        ]
    # if new_thread:
    #     return JSONResponse(
    #         {
    #             "message": "Thread already exists",
    #         }
    #     )

    # session.add_all(new_thread)
    # # session.bulk_save_objects(new_thread)
    # session.commit()
    # session.refresh(new_thread) 

    return JSONResponse(
        {
            "thead_count": users,
            # "user_threads": user_thread_list,
            # "message": "Test successful",
        }
    )


@router.post("sqlalchemy/test/lookups")
async def sqlalchemy_lookups():
    session = SessionLocal()
    # Example of using SQLAlchemy to perform lookups
    # Get all threads for a specific user_id
    user_id = 138
    threads = session.query(ChatThread).filter(ChatThread.user_id == user_id).all()
    thread_data = []
    for thread in threads:
        thread_data.append(
            {
                "id": thread.id,
                "user_id": thread.user_id,
                "title": thread.title,
                "mode": thread.mode,
                "client_session_id": thread.client_session_id,
                "created_at": thread.created_at.isoformat() if thread.created_at else None,
                "updated_at": thread.updated_at.isoformat() if thread.updated_at else None,
            }
        )
    return JSONResponse({"threads": thread_data})

def test_nero_16():
    pass