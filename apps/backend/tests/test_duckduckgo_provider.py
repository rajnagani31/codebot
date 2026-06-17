import unittest

from backend.bot.workflow.web.providers.duckduckgo_provider import (
    DuckDuckGoSearchProvider,
    _DuckDuckGoHtmlParser,
)

SAMPLE_HTML = """
<div class="serp__results">
  <div id="links" class="results">
    <div class="result results_links results_links_deep web-result ">
      <div class="links_main links_deep result__body">
        <h2 class="result__title">
          <a
            rel="nofollow"
            class="result__a"
            href="//duckduckgo.com/l/?uddg=https%3A%2F%2Ftodaydatetime.com%2F&amp;rut=abc"
          >
            Today's Date and Time - Accurate Clock &amp; Time Tools
          </a>
        </h2>
        <div class="result__extras">
          <div class="result__extras__url">
            <a class="result__url" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Ftodaydatetime.com%2F&amp;rut=abc">
              todaydatetime.com
            </a>
          </div>
        </div>
        <a class="result__snippet" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Ftodaydatetime.com%2F&amp;rut=abc">
          Find today's date and time instantly with our precise clock.
        </a>
        <div class="clear"></div>
      </div>
    </div>
  </div>
</div>
"""


class DuckDuckGoSearchProviderTests(unittest.TestCase):
    def test_parser_parses_anchor_snippet_and_unwraps_redirect_url(self):
        provider = DuckDuckGoSearchProvider()
        parser = _DuckDuckGoHtmlParser()
        parser.feed(SAMPLE_HTML)
        parser.close()

        self.assertEqual(len(parser.results), 1)
        raw_result = parser.results[0]
        normalized_url = provider._normalize_result_url(raw_result["url"])

        self.assertEqual(
            raw_result["title"], "Today's Date and Time - Accurate Clock & Time Tools"
        )
        self.assertEqual(normalized_url, "https://todaydatetime.com/")
        self.assertIn("today's date and time instantly", raw_result["snippet"].lower())


if __name__ == "__main__":
    unittest.main()
