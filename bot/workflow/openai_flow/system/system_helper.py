from langchain_core.messages import BaseMessage
from langchain_core.messages import SystemMessage
from bot.workflow.openai_flow.system.system_prompt import system_prompt

class GetSytemInstruction:
    def build_messages(self, messages: list[BaseMessage], previous_context: str = ""):
        system_message = system_prompt(previous_context or "")

        full_messages = [
            SystemMessage(content=system_message),
            *messages
        ]

        return full_messages
