import unittest

from backend.bot.application.schema.chat_schema import ChoiceConfig
from backend.bot.application.service.choice_resolver import (
    ChoiceResolver,
    ChoiceResolverInput,
)
from backend.bot.workflow.openai_flow.system.system_prompt import build_system_prompt


class ChoiceResolverTests(unittest.TestCase):
    def test_defaults_web_on_without_switching_to_web_research(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="What is the latest React version?",
                mode="chat",
            )
        )

        self.assertEqual(resolved.prompt_name, "chat")
        self.assertEqual(resolved.web_mode, "on")
        self.assertTrue(resolved.web_enabled)
        self.assertTrue(resolved.web_preferred)
        self.assertTrue(resolved.current_info_requested)

    def test_web_off_stays_off_for_latest_queries(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="What is the latest OpenAI API pricing?",
                mode="chat",
                choice_config=ChoiceConfig(mode="manual", web_mode="off"),
            )
        )

        self.assertEqual(resolved.prompt_name, "chat")
        self.assertEqual(resolved.web_mode, "off")
        self.assertFalse(resolved.web_enabled)
        self.assertFalse(resolved.web_preferred)
        self.assertTrue(resolved.current_info_requested)

    def test_manual_web_research_prompt_still_prefers_web(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="Summarize PostgreSQL replication options.",
                mode="chat",
                choice_config=ChoiceConfig(
                    mode="manual",
                    prompt_mode="manual",
                    prompt_name="web_research",
                    web_mode="on",
                ),
            )
        )

        self.assertEqual(resolved.prompt_name, "web_research")
        self.assertTrue(resolved.web_enabled)
        self.assertTrue(resolved.web_preferred)


class SystemPromptTests(unittest.TestCase):
    def test_prompt_warns_when_current_info_is_requested_but_web_is_off(self):
        prompt = build_system_prompt(
            "chat",
            web_enabled=False,
            web_preferred=False,
            current_info_requested=True,
        )

        self.assertIn("Web search tools are disabled.", prompt)
        self.assertIn("web search is off", prompt.lower())


if __name__ == "__main__":
    unittest.main()
