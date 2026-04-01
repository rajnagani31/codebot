import asyncio
import json
from html.parser import HTMLParser
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from .base import WebSearchProvider


class _DuckDuckGoHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.results: list[dict] = []
        self._current: dict | None = None
        self._current_field: str | None = None
        self._capture_anchor = False
        self._capture_snippet = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class") or ""

        if tag == "div" and "result" in classes.split():
            self._current = {"title": "", "url": "", "snippet": ""}
            self._current_field = None
            return

        if self._current is None:
            return

        if tag == "a" and "result__a" in classes:
            self._capture_anchor = True
            self._current_field = "title"
            self._current["url"] = attrs_dict.get("href") or ""
            return

        if tag == "a" and attrs_dict.get("data-testid") == "result-title-a":
            self._capture_anchor = True
            self._current_field = "title"
            self._current["url"] = attrs_dict.get("href") or ""
            return

        if tag == "div" and ("result__snippet" in classes or attrs_dict.get("data-result") == "snippet"):
            self._capture_snippet = True
            self._current_field = "snippet"

    def handle_endtag(self, tag: str):
        if tag == "a":
            self._capture_anchor = False
            if self._current_field == "title":
                self._current_field = None
        elif tag == "div" and self._capture_snippet:
            self._capture_snippet = False
            self._current_field = None
            if self._current and self._current.get("title") and self._current.get("url"):
                self.results.append(self._current)
                self._current = None

    def handle_data(self, data: str):
        if self._current is None or self._current_field is None:
            return
        value = data.strip()
        if not value:
            return
        existing = self._current.get(self._current_field, "")
        self._current[self._current_field] = f"{existing} {value}".strip()


class DuckDuckGoSearchProvider(WebSearchProvider):
    provider_name = "duckduckgo"
    search_url = "https://html.duckduckgo.com/html/?q={query}"
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )

    async def search(self, query: str, *, max_results: int = 3) -> dict[str, object]:
        html = await asyncio.to_thread(self._fetch_search_html, query)
        parser = _DuckDuckGoHtmlParser()
        parser.feed(html)
        normalized_results: list[dict[str, object]] = []

        for rank, item in enumerate(parser.results[:max_results], start=1):
            url = item.get("url") or ""
            parsed = urlparse(url)
            normalized_results.append(
                {
                    "rank": rank,
                    "title": str(item.get("title") or ""),
                    "url": url,
                    "domain": parsed.netloc,
                    "snippet": str(item.get("snippet") or ""),
                    "published_at": None,
                }
            )

        return {
            "query": query,
            "provider": self.provider_name,
            "results": normalized_results,
        }

    def _fetch_search_html(self, query: str) -> str:
        request = Request(
            self.search_url.format(query=quote(query)),
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=8) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="ignore")
