from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI



load_dotenv()





model = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0.0,
    max_retries=2,
    # other params...
)

class GroqLLMService:

    def __init__(self, model_name: str ) -> None:
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model_name = "openai/gpt-oss-20b" if model_name else None


        if self.api_key is None:
            raise ValueError("GROQ_API_KEY is not found")
        
        self._chat_model = None

    def bind_tools(self, tools: list):
        print(f"Binding tools: {[tool.name for tool in tools]} to model: {self.model_name}")
        model = ChatGroq(
            model = self.model_name,
            streaming=True
        )
        print('groq llm used')
        self._chat_model = model.bind_tools(tools) if tools else model
        return self
