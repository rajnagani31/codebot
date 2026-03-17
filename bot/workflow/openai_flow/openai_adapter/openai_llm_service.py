# openai_adapter/openai_llm_service.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage
import os
import sys
from dotenv import load_dotenv
import time
from system.system_prompt import SYSTEM_PROMPT

# Resolve `openai_tool` import robustly so this module can be run
# both as a package and as a standalone script during development.
try:
    # Preferred when running as a package: nero.workflow.openai_flow.openai_adapter
    from ..openai_tool.openai_tools import get_current_weather
except Exception:
    try:
        # Absolute import when package root is on sys.path
        from openai_tool.openai_tools import get_current_weather
    except Exception:
        # Fallback: ensure parent package dir is on sys.path then import
        _here = os.path.dirname(__file__)
        _pkg_root = os.path.abspath(os.path.join(_here, '..'))
        if _pkg_root not in sys.path:
            sys.path.insert(0, _pkg_root)
        from openai_tool.openai_tools import get_current_weather

load_dotenv()

class OpenAILLMService:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = "gpt-4o-mini"
        if self.api_key is None:
            raise ValueError("OPENAI_API_KEY is not found")
        # Store bound ChatOpenAI instance
        self._chat_model = None

    def bind_tools(self, tools):
        """Bind tools to the model (CRITICAL for tool calling)"""
        self._chat_model = ChatOpenAI(
            model=self.model,
            streaming=True,
        ).bind_tools(tools)
        return self  # Return self for chaining

    def invoke(self, messages: list[BaseMessage]):
        """LangGraph expects .invoke() method.

        Ensures a valid `SystemMessage` is prepended. If `SYSTEM_PROMPT`
        is already a `SystemMessage` instance it will be used directly;
        otherwise it will be converted to a string and wrapped.
        """
        if not self._chat_model:
            raise ValueError("Must call bind_tools() first")

        # Build system message safely
        if isinstance(SYSTEM_PROMPT, SystemMessage):
            system_message = SYSTEM_PROMPT
        else:
            system_message = SystemMessage(content=str(SYSTEM_PROMPT))

        # Ensure messages is a list
        msgs = list(messages) if not isinstance(messages, list) else messages
        # system_message = SystemMessage(content=str(SYSTEM_PROMPT))
        # msgs = messages
        return self._chat_model.ainvoke([system_message] + msgs)

    def stream_invoke(self, messages: list[BaseMessage]):
        """Attempt to stream responses from the underlying chat model.

        Yields chunks (either BaseMessage instances or strings). Falls back
        to single-shot `invoke` if streaming is not supported.
        """
        if not self._chat_model:
            raise ValueError("Must call bind_tools() first")

        stream_fn = getattr(self._chat_model, "stream_invoke", None)
        if callable(stream_fn):
            for chunk in stream_fn(messages):
                yield chunk
            return

        # Fallback: single-shot invoke and yield the full response once
        resp = self.invoke(messages)
        yield resp

    def get_system_prompt(self):
        with open("prompts/system_prompt.md") as f:
            return SystemMessage(content=f.read())