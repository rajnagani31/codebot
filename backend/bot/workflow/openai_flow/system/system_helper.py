from langchain_core.messages import BaseMessage
from langchain_core.messages import SystemMessage
from bot.workflow.openai_flow.system.system_prompt import system_prompt
from enum import Enum

class PrompteChoice(Enum):
    CODE_GENERATOR = "code_generator"
    FEW_SHORT_PROMPT = "few_short_prompt"
    DEBUG_CODE_STEP = "debug_code_step_style"

class GetSytemInstruction:
    def build_messages(self, messages: list[BaseMessage], previous_context: str = ""):

        system_message = system_prompt(prompt_type = PrompteChoice.DEBUG_CODE_STEP, previous_context = previous_context or "")
        # print("system_message",system_message)
        # print('value',PrompteChoice.CODE_GENERATOR)
        full_messages = [
            SystemMessage(content=system_message),
            *messages
        ]
        return full_messages
