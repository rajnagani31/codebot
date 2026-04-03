import json
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, ToolMessage

from bot.application.schema.chat_schema import (
    MessageMetadata,
    MessageProcessMetadata,
    ResolvedChoiceConfig,
)
from bot.application.service.web_search_service import WebSearchService
from bot.workflow.openai_flow.openai_adapter.openai_llm_service import OpenAILLMService
from bot.workflow.openai_flow.openai_tool.openai_tools import (
    ToolCapabilities,
    ToolExecutionContext,
    build_tools,
)
from bot.workflow.openai_flow.system.system_helper import GetSytemInstruction


@dataclass(slots=True)
class GraphRunContext:
    user_id: int
    thread_id: str
    assistant_message_id: str


class OpenAIToolGraph:
    def __init__(
        self,
        *,
        resolved_choice: ResolvedChoiceConfig,
        run_context: GraphRunContext,
    ):
        self.resolved_choice = resolved_choice
        self.run_context = run_context
        self.web_search_service = (
            WebSearchService() if resolved_choice.web_enabled else None
        )
        self.tools = build_tools(
            capabilities=ToolCapabilities(
                web_search_enabled=resolved_choice.web_enabled
            ),
            execution_context=ToolExecutionContext(
                web_search_service=self.web_search_service
            ),
        )
        self.tool_map = {tool.name: tool for tool in self.tools}
        self.llm = OpenAILLMService(model_name=resolved_choice.model_name).bind_tools(
            self.tools
        )

    async def run_stream(
        self,
        *,
        messages: list[BaseMessage],
        previous_context: str = "",
    ):
        conversation = list(messages)
        tools_used: list[str] = []
        sources: list[dict[str, Any]] = []
        citations: list[dict[str, Any]] = []
        web_search_run_id: str | None = None

        while True:
            streamed_response: AIMessage | None = None
            async for event in self._stream_llm_events(
                messages=conversation, previous_context=previous_context
            ):
                if event["type"] == "delta":
                    yield event
                    continue
                streamed_response = event["response"]

            if streamed_response is None:
                raise RuntimeError("LLM did not produce a response")

            conversation.append(streamed_response)
            tool_calls = list(getattr(streamed_response, "tool_calls", []) or [])
            print(f"Tool calls:--------------------------------- {tool_calls}")
            if not tool_calls:
                metadata = self._build_metadata(
                    tools_used=tools_used,
                    sources=sources,
                    citations=citations,
                    web_search_run_id=web_search_run_id,
                )
                yield {
                    "type": "complete",
                    "metadata": metadata,
                }
                return

            for tool_call in tool_calls:
                async for event in self._execute_tool_call_events(tool_call):
                    if event["type"] == "progress":
                        yield event
                        continue

                    tool_message = event["tool_message"]
                    conversation.append(tool_message)
                    tool_name = event["tool_name"]
                    tools_used.append(tool_name)

                    if event.get("sources"):
                        sources = event["sources"]
                        citations = [
                            {
                                "title": source["title"],
                                "url": source["url"],
                                "rank": source["rank"],
                            }
                            for source in sources
                        ]
                    if event.get("web_search_run_id"):
                        web_search_run_id = event["web_search_run_id"]

    async def _stream_llm_events(
        self, *, messages: list[BaseMessage], previous_context: str
    ):
        accumulated = None
        full_messages = GetSytemInstruction().build_messages(
            messages=messages,
            previous_context=previous_context,
            prompt_name=self.resolved_choice.prompt_name,
            web_enabled=self.resolved_choice.web_enabled,
            web_preferred=self.resolved_choice.web_preferred,
        )

        async for chunk in self.llm._chat_model.astream(full_messages):
            content = getattr(chunk, "content", "")
            if isinstance(content, str) and content:
                yield {"type": "delta", "delta": content}

            accumulated = chunk if accumulated is None else accumulated + chunk

        if accumulated is None:
            accumulated = AIMessage(content="")

        yield {"type": "response", "response": accumulated}

    async def _execute_tool_call_events(self, tool_call: dict[str, Any]):
        tool_name = str(tool_call["name"])
        tool_args = tool_call.get("args", {})
        try:
            if tool_name == "web_search":
                if self.web_search_service is None:
                    raise RuntimeError("Web search is not enabled")

                query = str(tool_args.get("query") or "")
                yield {
                    "type": "progress",
                    "stage": "searching_web",
                    "label": "Searching web...",
                }
                result = await self.web_search_service.search(
                    query=query,
                    user_id=self.run_context.user_id,
                    thread_id=self.run_context.thread_id,
                    message_id=self.run_context.assistant_message_id,
                    max_results=3,
                )
                yield {
                    "type": "progress",
                    "stage": "reading_sources",
                    "label": "Reading sources...",
                }
                tool_message = ToolMessage(
                    content=json.dumps(
                        {
                            "query": result["query"],
                            "context": result["context_text"],
                            "sources": result["sources"],
                        },
                        ensure_ascii=True,
                    ),
                    tool_call_id=tool_call.get("id"),
                    name=tool_name,
                )
                yield {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "tool_message": tool_message,
                    "sources": result["sources"],
                    "web_search_run_id": result["run_id"],
                }
                return

            if tool_name == "read_web_page":
                if self.web_search_service is None:
                    raise RuntimeError("Web reading is not enabled")
                url = str(tool_args.get("url") or "")
                yield {
                    "type": "progress",
                    "stage": "reading_sources",
                    "label": "Reading sources...",
                }
                result = await self.web_search_service.read_web_page(url)
                tool_message = ToolMessage(
                    content=json.dumps(result, ensure_ascii=True),
                    tool_call_id=tool_call.get("id"),
                    name=tool_name,
                )
                yield {
                    "type": "tool_result",
                    "tool_name": tool_name,
                    "tool_message": tool_message,
                }
                return

            tool = self.tool_map.get(tool_name)
            if tool is None:
                raise KeyError(f"Unknown tool: {tool_name}")

            result = await tool.ainvoke(tool_args)
            content = (
                result
                if isinstance(result, str)
                else json.dumps(result, ensure_ascii=True)
            )
            yield {
                "type": "tool_result",
                "tool_name": tool_name,
                "tool_message": ToolMessage(
                    content=content,
                    tool_call_id=tool_call.get("id"),
                    name=tool_name,
                ),
            }
        except Exception as exc:
            yield {
                "type": "tool_result",
                "tool_name": tool_name,
                "tool_message": ToolMessage(
                    content=json.dumps({"error": str(exc)}, ensure_ascii=True),
                    tool_call_id=tool_call.get("id"),
                    name=tool_name,
                ),
            }

    def _build_metadata(
        self,
        *,
        tools_used: list[str],
        sources: list[dict[str, Any]],
        citations: list[dict[str, Any]],
        web_search_run_id: str | None,
    ) -> dict[str, Any]:
        web_tools = {"web_search", "read_web_page"}
        non_web_tools_used = [name for name in tools_used if name not in web_tools]
        web_tools_used = [name for name in tools_used if name in web_tools]

        if web_tools_used and non_web_tools_used:
            execution_mode = "agent_with_web_search_flow"
        elif web_tools_used:
            execution_mode = "web_search_flow"
        elif non_web_tools_used:
            execution_mode = "langgraph_agent_flow"
        else:
            execution_mode = "llm_only_flow"

        metadata = MessageMetadata(
            process=MessageProcessMetadata(
                choice_config=self.resolved_choice.choice_config.model_dump(),
                resolved_choice_config=self.resolved_choice.model_dump(),
                execution_mode=execution_mode,
                tools_used=tools_used,
                web_search_used=bool(web_tools_used),
                model_name=self.resolved_choice.model_name,
                prompt_name=self.resolved_choice.prompt_name,
            ),
            sources=sources,
            citations=citations,
            web_search_run_id=web_search_run_id,
        )
        return metadata.model_dump()
