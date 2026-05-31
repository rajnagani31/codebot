from dataclasses import dataclass

from ..schema.chat_schema import (
    ChatMode,
    ChoiceConfig,
    PromptName,
    ResolvedChoiceConfig,
)

CURRENT_INFO_KEYWORDS = (
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
    "announcement",
)


@dataclass(slots=True)
class ChoiceResolverInput:
    query: str
    mode: ChatMode
    choice_config: ChoiceConfig | None = None


class ChoiceResolver:
    def resolve(self, payload: ChoiceResolverInput) -> ResolvedChoiceConfig:
        raw_choice = self._normalize_choice(payload.choice_config)
        current_info_requested = self._query_needs_current_info(payload.query)
        prompt_name = self._resolve_prompt_name(
            raw_choice=raw_choice,
            mode=payload.mode,
        )
        web_enabled, web_preferred = self._resolve_web_flags(
            raw_choice=raw_choice,
            prompt_name=prompt_name,
            current_info_requested=current_info_requested,
        )
        model_name = self._resolve_model_name(
            raw_choice=raw_choice,
            prompt_name=prompt_name,
            query=payload.query,
            web_preferred=web_preferred,
        )

        return ResolvedChoiceConfig(
            mode=raw_choice.mode,
            model_mode=raw_choice.model_mode,
            model_name=model_name,
            prompt_mode=raw_choice.prompt_mode,
            prompt_name=prompt_name,
            web_mode=raw_choice.web_mode,
            web_enabled=web_enabled,
            web_preferred=web_preferred,
            current_info_requested=current_info_requested,
            choice_config=raw_choice,
        )

    def _normalize_choice(self, choice_config: ChoiceConfig | None) -> ChoiceConfig:
        choice = (
            choice_config.model_copy() if choice_config is not None else ChoiceConfig()
        )

        if choice.mode == "manual":
            if choice.model_name:
                choice.model_mode = "manual"
            if choice.prompt_name:
                choice.prompt_mode = "manual"

        return choice

    def _resolve_prompt_name(
        self, *, raw_choice: ChoiceConfig, mode: ChatMode
    ) -> PromptName:
        if raw_choice.prompt_mode == "manual" and raw_choice.prompt_name:
            return raw_choice.prompt_name

        if mode == "code":
            return "code"
        if mode == "debug":
            return "debug"
        if mode == "review":
            return "review"
        return "general"

    def _resolve_model_name(
        self,
        *,
        raw_choice: ChoiceConfig,
        prompt_name: PromptName,
        query: str,
        web_preferred: bool = False,
    ) -> str:
        if raw_choice.model_mode == "manual" and raw_choice.model_name:
            return raw_choice.model_name

        if prompt_name in {"debug", "review", "web_research"}:
            return "gpt-4o"

        if web_preferred:
            return "gpt-4o"

        if prompt_name == "code" and len(query) > 200:
            return "gpt-4o"

        return "gpt-4o-mini"

    def _resolve_web_flags(
        self,
        *,
        raw_choice: ChoiceConfig,
        prompt_name: PromptName,
        current_info_requested: bool,
    ) -> tuple[bool, bool]:
        if raw_choice.web_mode == "off":
            return False, False

        web_enabled = True
        web_preferred = prompt_name == "web_research" or current_info_requested
        return web_enabled, web_preferred

    def _query_needs_current_info(self, query: str) -> bool:
        normalized_query = query.lower()
        return any(keyword in normalized_query for keyword in CURRENT_INFO_KEYWORDS)
