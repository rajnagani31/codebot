from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from backend.bot.workflow.pg_vector.pg_vector_service import PGVectorService
from bot.workflow.openai_flow.openai_tool.openai_tool_graph import OpenAIToolGraph
from bot.workflow.qudrant.vector_service import VectorService

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id : int
    code: str | None = None
    mode: str = "chat"  # chat | code | debug | review
	 

# def build_prompt(request: ChatRequest):
#     content = request.query

#     if request.code:
#         content += f"\n\nHere is the code:\n```python\n{request.code}\n```"

#     if request.mode == "debug":
#         content = f"Debug this:\n{content}"
#     elif request.mode == "review":
#         content = f"Review this code:\n{content}"
#     elif request.mode == "code":
#         content = f"Write code for:\n{content}"

#     return content


@router.post("/chat")
async def chat(request: ChatRequest, code = Query(str)):
    try:
        graph = OpenAIToolGraph()
        # vector_service = VectorService()
        pg_vector_service = PGVectorService()
        user_id = request.user_id
        user_query = request.query
        history = pg_vector_service.search(user_id=user_id, query = user_query)

        user_history = "\n".join(history)
        print("user_history",user_history)
        # full_message = GetSytemInstruction().build_messages(messages = user_query, previous_context = user_history)
        messages = [
            HumanMessage(content=user_query)
        ]
    except Exception as e:
        # Error before streaming starts
        raise HTTPException(status_code=500, detail=f"Setup error: {str(e)}")

    async def event_stream():
        full_response = ""
        try:
            async for event in graph.app.astream(
                {
                    "messages": messages,
                    "previous_context": user_history  # inject here
                }
            ):
                for node, output in event.items():
                    if node == "agent_response":
                        msg = output["messages"][-1]

                        if msg.content:
                            full_response += msg.content
                            yield msg.content

        except Exception as stream_error:
            # Error during streaming
            yield f"\n[stream-error]: {str(stream_error)}\n"

        try:
            chat_text = f"User: {user_query}\nAI: {full_response}"

            pg_vector_service.store(
                user_id=user_id,
                text=chat_text,
                type_="chat"
            )
        except Exception as store_error:
            print("Vector store error :",store_error)

    return StreamingResponse(event_stream(), media_type="text/plain")
