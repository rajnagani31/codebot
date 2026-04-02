from dataclasses import dataclass

from ..schema.chat_schema import (
    ChatMode,
    ChoiceConfig,
    PromptName,
    ResolvedChoiceConfig,
)


AUTO_WEB_KEYWORDS = (
    "latest",
    "current",
    "today",
    "recent",
    "news",
    "release",
    "version",
    "docs",
    "documentation",
    "api",
    "pricing",
    "announce",
)


@dataclass(slots=True)
class ChoiceResolverInput:
    query: str
    mode: ChatMode
    choice_config: ChoiceConfig | None = None
    use_web: bool | None = None


class ChoiceResolver:
    def resolve(self, payload: ChoiceResolverInput) -> ResolvedChoiceConfig:
        raw_choice = self._normalize_choice(payload.choice_config, payload.use_web)
        prompt_name = self._resolve_prompt_name(raw_choice=raw_choice, mode=payload.mode, query=payload.query)
        model_name = self._resolve_model_name(raw_choice=raw_choice, prompt_name=prompt_name, query=payload.query)
        web_enabled, web_preferred = self._resolve_web_flags(raw_choice)

        return ResolvedChoiceConfig(
            mode=raw_choice.mode,
            model_mode=raw_choice.model_mode,
            model_name=model_name,
            prompt_mode=raw_choice.prompt_mode,
            prompt_name=prompt_name,
            web_mode=raw_choice.web_mode,
            web_enabled=web_enabled,
            web_preferred=web_preferred,
            choice_config=raw_choice,
        )

    def _normalize_choice(self, choice_config: ChoiceConfig | None, use_web: bool | None) -> ChoiceConfig:
        choice = choice_config.model_copy() if choice_config is not None else ChoiceConfig()
    
        if use_web is not None and choice_config is None:
            choice.web_mode = "on" if use_web else "off"

        if choice.mode == "manual":
            if choice.model_name:
                choice.model_mode = "manual"
            if choice.prompt_name:
                choice.prompt_mode = "manual"

        return choice

    def _resolve_prompt_name(self, *, raw_choice: ChoiceConfig, mode: ChatMode, query: str) -> PromptName:
        if raw_choice.prompt_mode == "manual" and raw_choice.prompt_name:
            return raw_choice.prompt_name

        normalized_query = query.lower()
        if any(keyword in normalized_query for keyword in AUTO_WEB_KEYWORDS):
            return "web_research"

        if mode == "code":
            return "code"
        if mode == "debug":
            return "debug"
        if mode == "review":
            return "review"
        return "chat"

    def _resolve_model_name(self, *, raw_choice: ChoiceConfig, prompt_name: PromptName, query: str) -> str:
        if raw_choice.model_mode == "manual" and raw_choice.model_name:
            return raw_choice.model_name

        if prompt_name in {"debug", "review", "web_research"}:
            return "gpt-4o"

        if prompt_name == "code" and len(query) > 200:
            return "gpt-4o"

        return "gpt-4o-mini"

    def _resolve_web_flags(self, raw_choice: ChoiceConfig) -> tuple[bool, bool]:
        if raw_choice.web_mode == "off":
            return False, False
        if raw_choice.web_mode == "on":
            return True, True
        return True, False
