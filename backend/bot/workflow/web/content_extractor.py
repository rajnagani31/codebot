import asyncio
import re
from html import unescape
from html.parser import HTMLParser
from urllib.request import Request, urlopen


class _ReadableHtmlParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self._inside_title = False
        self._skip_depth = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs):
        if tag == "title":
            self._inside_title = True
            return
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1
            return
        if tag in {"p", "li", "article", "section", "div", "br", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._inside_title = False
            return
        if tag in {"script", "style", "noscript"} and self._skip_depth > 0:
            self._skip_depth -= 1
            return
        if tag in {"p", "li", "article", "section", "div", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str):
        if self._inside_title:
            value = data.strip()
            if value:
                self.title = f"{self.title} {value}".strip()
            return
        if self._skip_depth > 0:
            return
        value = re.sub(r"\s+", " ", unescape(data)).strip()
        if value:
            self.parts.append(value)


class WebContentService:
    def __init__(self, *, per_request_timeout: int = 8):
        self.per_request_timeout = per_request_timeout
        self.user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )

    async def fetch_many(self, urls: list[str]) -> list[dict[str, str | None]]:
        tasks = [asyncio.create_task(self.fetch_and_extract(url)) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        normalized: list[dict[str, str | None]] = []

        for url, result in zip(urls, results, strict=False):
            if isinstance(result, Exception):
                normalized.append(
                    {
                        "url": url,
                        "title": None,
                        "text": None,
                        "status": "failed",
                    }
                )
                continue
            normalized.append(result)

        return normalized

    async def fetch_and_extract(self, url: str) -> dict[str, str | None]:
        return await asyncio.wait_for(asyncio.to_thread(self._fetch_and_extract_sync, url), timeout=self.per_request_timeout)

    def summarize(self, *, query: str, title: str, snippet: str, content: str, max_chars: int = 420) -> str:
        text = " ".join(part for part in [snippet, content] if part).strip()
        if not text:
            return f"{title}: no readable content extracted."
        text = re.sub(r"\s+", " ", text)
        summary = text[:max_chars].rsplit(" ", 1)[0].strip() if len(text) > max_chars else text
        return summary or text[:max_chars]

    def clean_text(self, text: str, max_chars: int = 2000) -> str:
        normalized = re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+", " ", text)).strip()
        return normalized[:max_chars]

    def _fetch_and_extract_sync(self, url: str) -> dict[str, str | None]:
        request = Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        with urlopen(request, timeout=self.per_request_timeout) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            html = response.read().decode(charset, errors="ignore")

        parser = _ReadableHtmlParser()
        parser.feed(html)
        text = self.clean_text("\n".join(parser.parts))

        return {
            "url": url,
            "title": parser.title or url,
            "text": text,
            "status": "completed",
        }
