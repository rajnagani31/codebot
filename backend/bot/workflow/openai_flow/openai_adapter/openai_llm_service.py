import os
from enum import Enum

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


class LLMModels(Enum):
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4O = "gpt-4o"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5.4-mini"
    GPT_5_NENO = "gpt-5.4-nano"


class OpenAILLMService:
    def __init__(self, model_name: str = LLMModels.GPT_4O_MINI.value):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        if self.api_key is None:
            raise ValueError("OPENAI_API_KEY is not found")
        self._chat_model = None

    def bind_tools(self, tools: list):
        model = ChatOpenAI(
            model=self.model_name,
            streaming=True,
        )
        self._chat_model = model.bind_tools(tools) if tools else model
        return self
