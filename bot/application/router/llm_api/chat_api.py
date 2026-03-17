from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import importlib
import os
import sys
from pathlib import Path
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from bot.workflow.openai_flow.openai_tool.openai_tool_graph import OpenAIToolGraph

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    code: str | None = None
    mode: str = "chat"  # chat | code | debug | review
	 

def build_prompt(request: ChatRequest):
    content = request.query

    if request.code:
        content += f"\n\nHere is the code:\n```python\n{request.code}\n```"

    if request.mode == "debug":
        content = f"Debug this:\n{content}"
    elif request.mode == "review":
        content = f"Review this code:\n{content}"
    elif request.mode == "code":
        content = f"Write code for:\n{content}"

    return content


@router.post("/chat")
async def chat(request: ChatRequest, code = Query(str)):
    try:
        graph = OpenAIToolGraph()
        # code = f"```{code}```"
        content = request.query # + code

    except Exception as e:
        # Error before streaming starts
        raise HTTPException(status_code=500, detail=f"Setup error: {str(e)}")

    async def event_stream():
        try:
            inputs = {"messages": [HumanMessage(content=content)]}

            async for event in graph.app.astream(inputs):
                print(event)
                try:
                    for node, output in event.items():

                        if node == "agent_response":
                            msg = output["messages"][-1]
                            if isinstance(msg, AIMessage) and msg.content:
                                yield msg.content

                        elif node == "tools":
                            yield "\n[tool-executed]\n"

                except Exception as inner_error:
                    # Error while processing one event
                    yield f"\n[error-processing-event]: {str(inner_error)}\n"

        except Exception as stream_error:
            # Error during streaming
            yield f"\n[stream-error]: {str(stream_error)}\n"

    return StreamingResponse(event_stream(), media_type="text/plain")