# openai_tool/openai_tool_graph.py

from typing import Annotated, TypedDict, Literal, Optional
import asyncio
import sys
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, ToolMessage, AIMessage, BaseMessage
from bot.workflow.qudrant.vector_service import VectorService
from bot.workflow.openai_flow.system.system_helper import GetSytemInstruction

# Use relative imports for modules in the same openai_tool package
from .openai_tools import *  # Your @tool functions
from bot.workflow.openai_flow.openai_adapter.openai_llm_service import OpenAILLMService


class State(TypedDict):
    messages: Annotated[list, add_messages]


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

    async def agent_response(self, state: State):
        """Agent: LLM decides which tools to call"""
        print("🧠 Agent streaming response...")

        messages = state["messages"]

        # greeting shortcut
        if messages[-1].content.lower() in ["hi", "hello", "hi, thier"]:
            print('it\'s working')
            return {"messages": [AIMessage(content="Hello! How can I assist you today?!!")]}

        # STREAM the LLM response
        response = await self.stream_llm(messages)

        # print("\nLLM final message:", response)

        return {"messages": [response]}

    def execute_tools(self, state: State):
        """Execute the tool calls from agent"""
        print("🔧 3. Executing tools called by agent...")

        last_message = state["messages"][-1]
        if not isinstance(last_message, AIMessage) or not getattr(last_message, "tool_calls", None):
            return state

        tool_messages = []
        for tool_call in last_message.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call.get("args", {})

            # Execute tool
            for t in self.tools:
                if t.name == tool_name:
                    result = t.invoke(tool_args)
                    tool_messages.append(
                        ToolMessage(
                            content=result,
                            tool_call_id=tool_call.get("id"),
                            name=tool_name,
                        )
                    )
                    print(f"✅ Tool executed: {tool_name}({tool_args}) -> {result}")
                    break

        return {"messages": tool_messages}

    def should_continue(self, state: State) -> Literal["tools", END]:  # type: ignore
        last_message = state["messages"][-1]
        print("🔍 2. Checking if agent called tools...")
        if isinstance(last_message, AIMessage) and getattr(last_message, "tool_calls", None):
            return "tools"
        return END

    async def stream_llm(self, messages: list, previous_context: str = "") -> AIMessage:
        """Stream tokens while preserving tool calls"""

        accumulated = None
        print('previous_context',previous_context)
        
        # ✅ Inject context into system prompt
        full_message = GetSytemInstruction().build_messages(
            messages=messages,
            previous_context=previous_context
        )

        async for chunk in self.llm._chat_model.astream(full_message):

            if chunk.content:
                sys.stdout.flush()

            if accumulated is None:
                accumulated = chunk
            else:
                accumulated = accumulated + chunk

        return accumulated

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
