import asyncio
from html.parser import HTMLParser
from urllib.parse import parse_qs, quote, unquote, urlparse
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
        self._snippet_tag: str | None = None
        self._result_div_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]):
        attrs_dict = dict(attrs)
        classes = attrs_dict.get("class") or ""

        if tag == "div" and "result" in classes.split():
            self._append_current_result()
            self._current = {"title": "", "url": "", "snippet": ""}
            self._current_field = None
            self._capture_anchor = False
            self._capture_snippet = False
            self._snippet_tag = None
            self._result_div_depth = 1
            return

        if self._current is None:
            return

        if tag == "div":
            self._result_div_depth += 1

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

        if tag in {"a", "div"} and (
            "result__snippet" in classes or attrs_dict.get("data-result") == "snippet"
        ):
            self._capture_snippet = True
            self._current_field = "snippet"
            self._snippet_tag = tag

    def handle_endtag(self, tag: str):
        if tag == "a":
            self._capture_anchor = False
            if self._current_field == "title":
                self._current_field = None

        if tag == self._snippet_tag and self._capture_snippet:
            self._capture_snippet = False
            self._current_field = None
            self._snippet_tag = None

        if tag == "div" and self._current is not None:
            self._result_div_depth -= 1
            if self._result_div_depth <= 0:
                self._append_current_result()

    def handle_data(self, data: str):
        if self._current is None or self._current_field is None:
            return
        value = data.strip()
        if not value:
            return
        existing = self._current.get(self._current_field, "")
        self._current[self._current_field] = f"{existing} {value}".strip()

    def close(self):
        super().close()
        self._append_current_result()

    def _append_current_result(self):
        if self._current and self._current.get("title") and self._current.get("url"):
            self.results.append(self._current)
        self._current = None
        self._current_field = None
        self._capture_anchor = False
        self._capture_snippet = False
        self._snippet_tag = None
        self._result_div_depth = 0


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
            url = self._normalize_result_url(str(item.get("url") or ""))
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

    def _normalize_result_url(self, url: str) -> str:
        if not url:
            return ""

        if url.startswith("//"):
            url = f"https:{url}"

        parsed = urlparse(url)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            target = parse_qs(parsed.query).get("uddg", [""])[0]
            if target:
                return unquote(target)

        return url
