from langchain_core.messages import BaseMessage
from langchain_core.messages import SystemMessage, HumanMessage
# from system_prompt import system_prompt
from bot.workflow.openai_flow.system.system_prompt import system_prompt

class GetSytemInstruction:
    def build_messages(self, messages: list[BaseMessage]):
    
        system_message = system_prompt()
    
        full_messages = [
            SystemMessage(content=system_message),
            *messages   #  keep full history
        ]

        return full_messages
    
print(GetSytemInstruction().build_messages('hello'))