import os
import sys
import unittest

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from bot.workflow.web.content_extractor import WebContentService


class WebContentServiceTests(unittest.TestCase):
    def test_extract_from_html_preserves_code_and_tables(self):
        html = """
        <html>
          <head>
            <title>Example Docs</title>
          </head>
          <body>
            <main>
              <h1>Example Docs</h1>
              <p>This page includes sample code and a table.</p>
              <pre class="language-python"><code>def add(a, b):
    return a + b</code></pre>
              <table>
                <tr><th>Name</th><th>Value</th></tr>
                <tr><td>alpha</td><td>1</td></tr>
                <tr><td>beta</td><td>2</td></tr>
              </table>
              <ul>
                <li>First item</li>
                <li>Second item</li>
              </ul>
            </main>
          </body>
        </html>
        """

        service = WebContentService()
        page = service.extract_from_html(url="https://docs.langchain.com/oss/python/langchain/rag#loading-documents", html=html)

        self.assertEqual(page["title"], "Example Docs")
        self.assertEqual(page["status"], "completed")
        self.assertIn("# Example Docs", page["text"])
        self.assertIn("```python", page["text"])
        self.assertIn("def add(a, b):", page["text"])
        self.assertIn("| Name | Value |", page["text"])
        self.assertIn("| alpha | 1 |", page["text"])
        self.assertIn("- First item", page["text"])
        self.assertIn("```python", page["preview"])
        self.assertIn("| Name | Value |", page["preview"])


if __name__ == "__main__":
    unittest.main()
