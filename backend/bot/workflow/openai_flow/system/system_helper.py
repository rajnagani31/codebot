from langchain_core.messages import BaseMessage, SystemMessage

from bot.workflow.openai_flow.system.system_prompt import build_system_prompt


class GetSytemInstruction:
    def build_messages(
        self,
        *,
        messages: list[BaseMessage],
        previous_context: str = "",
        prompt_name: str = "chat",
        web_enabled: bool = False,
        web_preferred: bool = False,
    ) -> list[BaseMessage]:
        system_message = build_system_prompt(
            prompt_name,
            previous_context=previous_context or "",
            web_enabled=web_enabled,
            web_preferred=web_preferred,
        )
        return [SystemMessage(content=system_message), *messages]
