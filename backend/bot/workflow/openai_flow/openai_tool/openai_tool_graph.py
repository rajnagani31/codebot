# openai_tool/openai_tool_graph.py

from typing import Annotated, TypedDict, Literal
import asyncio
import sys
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from bot.workflow.openai_flow.system.system_helper import GetSytemInstruction

# Use relative imports for modules in the same openai_tool package
from .openai_tools import *  # Your @tool functions
from bot.workflow.openai_flow.openai_adapter.openai_llm_service import OpenAILLMService


class State(TypedDict):
    messages: Annotated[list, add_messages]
    previous_context: str

class OpenAIToolGraph:
    """Encapsulates the tool-enabled LLM graph and provides streaming runs."""

    def __init__(self):
        # Bind tools to LLM first
        self.tools = [
            get_current_weather,
            two_sum,
            apply_command,
            list_directory,
            create_directory,
            read_file,
        ]

        self.llm = OpenAILLMService().bind_tools(self.tools)

        # Build graph
        self.graph = StateGraph(State)
        self.graph.add_node("agent_response", self.agent_response)
        self.graph.add_node("tools", self.execute_tools)

        # Edge
        self.graph.set_entry_point("agent_response")
        self.graph.add_conditional_edges(
            "agent_response", self.should_continue,
            {"tools": "tools", END: END},
        )
        self.graph.add_edge("tools", "agent_response")

        # start compiantion
        self.app = self.graph.compile()

    async def agent_response(self, state: State, config: RunnableConfig | None = None):
        """Agent: LLM decides which tools to call"""
        print("🧠 Agent streaming response...")

        messages = state["messages"]
        previous_context = state.get("previous_context", "")
        latest_message = str(messages[-1].content).strip()

        # greeting shortcut
        # if self._is_casual_message(latest_message):
        #     return {"messages": [AIMessage(content=self._build_casual_reply(latest_message))]}

        # STREAM the LLM response
        response = await self.stream_llm(messages, previous_context, config=config)

        # print("\nLLM final message:", response)

        return {"messages": state["messages"] + [response]}

    def execute_tools(self, state: State):
        """Execute the tool calls from agent"""
        print("🔧 3. Executing tools called by agent...")

        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
            return state

        tool_messages = self._execute_tool_calls(last_message)

        return {"messages": state["messages"] + tool_messages}

    def should_continue(self, state: State) -> Literal["tools", END]:  # type: ignore
        last_message = state["messages"][-1]
        print("🔍 2. Checking if agent called tools...")
        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    async def stream_llm(
        self,
        messages: list,
        previous_context: str = "",
        config: RunnableConfig | None = None,
    ) -> AIMessage:
        """Stream tokens while preserving tool calls"""

        accumulated = None
        print('previous_context',previous_context)
        
        # ✅ Inject context into system prompt
        full_message = GetSytemInstruction().build_messages(
            messages=messages,
            previous_context=previous_context
        )

        async for chunk in self.llm._chat_model.astream(full_message, config=config):

            if chunk.content:
                sys.stdout.flush()

            if accumulated is None:
                accumulated = chunk
            else:
                accumulated = accumulated + chunk

        return accumulated

    def _is_casual_message(self, content: str) -> bool:
        normalized = " ".join(content.lower().split())
        casual_messages = {
            "hi",
            "hello",
            "hey",
            "hi there",
            "hello there",
            "good morning",
            "good afternoon",
            "good evening",
            "how are you",
            "how are you?",
            "how r u",
            "what's up",
            "whats up",
            "who are you",
            "thank you",
            "thanks",
            "ok",
            "okay",
        }

        return normalized in casual_messages

    def _build_casual_reply(self, content: str) -> str:
        normalized = " ".join(content.lower().split())

        if normalized in {"thank you", "thanks"}:
            return "You're welcome. Tell me what you want to work on."

        if normalized in {"who are you"}:
            return "I’m Codebot. I can help with code, APIs, databases, and app issues."

        if normalized in {"how are you", "how are you?", "how r u", "what's up", "whats up"}:
            return "I’m ready to help. Tell me what you want to do."

        return "Hello. What do you want help with?"

    def _execute_tool_calls(self, message: AIMessage) -> list[ToolMessage]:
        tool_messages = []

        for tool_call in message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})

            for tool in self.tools:
                if tool.name != tool_name:
                    continue

                result = tool.invoke(tool_args)
                tool_messages.append(
                    ToolMessage(
                        content=result,
                        tool_call_id=tool_call.get("id"),
                        name=tool_name,
                    )
                )
                print(f"✅ Tool executed: {tool_name}({tool_args}) -> {result}")
                break

        return tool_messages

    async def run_streaming(self, query):
        """Interactive loop using LangGraph streaming"""

        # while True:
        #     user_input = await asyncio.to_thread(input, "You: ")

        # if query.lower() in ["exit", "quit"]:
        #     print("Exiting...")
        #     break

        inputs = {"messages": [HumanMessage(content=query)]}

        async for event in self.app.astream(inputs):

            for node, output in event.items():

                # Agent response node
                if node == "agent_response":
                    msg = output["messages"][-1]

                    if isinstance(msg, AIMessage) and msg.content:
                        print('ok',msg.content)

                # Tool execution node
                if node == "tools":
                    print("⚙️ Tool executed")


if __name__ == "__main__":
    service = OpenAIToolGraph()
    # Default to streaming interactive run
    import asyncio
    asyncio.run(service.run_streaming())
