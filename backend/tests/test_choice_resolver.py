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
                mode="general",
            )
        )

        self.assertEqual(resolved.prompt_name, "general")
        self.assertEqual(resolved.web_mode, "on")
        self.assertTrue(resolved.web_enabled)
        self.assertTrue(resolved.web_preferred)
        self.assertTrue(resolved.current_info_requested)

    def test_web_off_stays_off_for_latest_queries(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="What is the latest OpenAI API pricing?",
                mode="general",
                choice_config=ChoiceConfig(mode="manual", web_mode="off"),
            )
        )

        self.assertEqual(resolved.prompt_name, "general")
        self.assertEqual(resolved.web_mode, "off")
        self.assertFalse(resolved.web_enabled)
        self.assertFalse(resolved.web_preferred)
        self.assertTrue(resolved.current_info_requested)

    def test_manual_web_research_prompt_still_prefers_web(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="Summarize PostgreSQL replication options.",
                mode="general",
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


    def test_web_preferred_upgrades_model_to_gpt4o(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="What is the latest React version?",
                mode="general",
            )
        )

        self.assertTrue(resolved.web_preferred)
        self.assertEqual(resolved.model_name, "gpt-4o")

    def test_no_web_preferred_stays_on_mini(self):
        resolved = ChoiceResolver().resolve(
            ChoiceResolverInput(
                query="Explain how closures work in JavaScript",
                mode="general",
            )
        )

        self.assertFalse(resolved.web_preferred)
        self.assertEqual(resolved.model_name, "gpt-4o-mini")


class SystemPromptTests(unittest.TestCase):
    def test_prompt_gives_natural_fallback_when_web_off_and_current_info_requested(self):
        prompt = build_system_prompt(
            "general",
            web_enabled=False,
            web_preferred=False,
            current_info_requested=True,
        )

        self.assertNotIn("Web search tools are disabled", prompt)
        self.assertNotIn("web search is off", prompt.lower())
        self.assertIn("Handling Current Information Requests", prompt)
        self.assertIn("best answer you can", prompt)


if __name__ == "__main__":
    unittest.main()
