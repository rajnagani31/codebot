import asyncio
import re
from typing import Any
from urllib.request import Request, urlopen

from bs4 import BeautifulSoup, NavigableString, Tag

CONTENT_ROOT_SELECTORS = (
    "#content-area",
    ".mdx-content",
    "article",
    "main",
    "[role='main']",
    ".post-content",
    ".markdown-body",
)

NOISE_SELECTORS = (
    "script, style, nav, footer, aside, form, svg, button, input, textarea, "
    "meta, link, noscript, iframe, [aria-hidden='true'], [hidden], "
    ".sidebar, .menu, .ad, .tabs-header, .pagination, .breadcrumb, .table-of-contents, "
    ".copy-button, .theme-toggle, .feedback-widget"
)

HEADING_PREFIX = {
    "h1": "# ",
    "h2": "## ",
    "h3": "### ",
    "h4": "#### ",
    "h5": "##### ",
    "h6": "###### ",
}

SKIP_LINE_VALUES = {
    "Copy page",
}


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def clean_content_root(root: Tag) -> Tag:
    for node in root.select(NOISE_SELECTORS):
        node.decompose()
    return root


def find_content_root(soup: BeautifulSoup) -> Tag:
    for selector in CONTENT_ROOT_SELECTORS:
        node = soup.select_one(selector)
        if node is not None:
            return clean_content_root(node)
    body = soup.body if soup.body is not None else soup
    return clean_content_root(body)


def extract_code_language(node: Tag) -> str:
    data_language = node.get("data-language")
    if isinstance(data_language, str) and data_language.strip():
        return data_language.strip()

    for class_name in node.get("class") or []:
        if class_name.startswith("language-"):
            return class_name.removeprefix("language-")

    code_child = node.find(["code", "div"], class_=re.compile(r"language-"))
    if code_child is None:
        return ""

    for class_name in code_child.get("class") or []:
        if class_name.startswith("language-"):
            return class_name.removeprefix("language-")

    return ""


def render_table(table: Tag) -> str | None:
    rows: list[str] = []
    for row in table.find_all("tr"):
        cells = [
            normalize_text(cell.get_text(" ", strip=True))
            for cell in row.find_all(["th", "td"])
        ]
        cells = [cell for cell in cells if cell]
        if cells:
            rows.append("| " + " | ".join(cells) + " |")

    return "\n".join(rows) if rows else None


def render_list(list_node: Tag, indent: int = 0) -> str | None:
    lines: list[str] = []
    ordered = list_node.name == "ol"

    for index, item in enumerate(list_node.find_all("li", recursive=False), start=1):
        marker = f"{index}." if ordered else "-"
        prefix = "  " * indent + marker + " "

        inline_parts: list[str] = []
        nested_parts: list[str] = []

        for child in item.children:
            if isinstance(child, NavigableString):
                text = normalize_text(str(child))
                if text:
                    inline_parts.append(text)
                continue

            if not isinstance(child, Tag):
                continue

            if child.name in {"ul", "ol"}:
                nested_block = render_list(child, indent + 1)
                if nested_block:
                    nested_parts.append(nested_block)
                continue

            if child.name in {"pre", "table"}:
                nested_block = render_block(child)
                if nested_block:
                    nested_parts.append(nested_block)
                continue

            text = normalize_text(child.get_text(" ", strip=True))
            if text:
                inline_parts.append(text)

        item_text = normalize_text(" ".join(inline_parts))
        if item_text:
            lines.append(prefix + item_text)
        elif nested_parts:
            lines.append(prefix.rstrip())

        for nested_part in nested_parts:
            lines.extend(nested_part.splitlines())

    return "\n".join(lines) if lines else None


def render_block(node: Tag) -> str | None:
    classes = node.get("class") or []
    if node.name == "div" and any(
        "code-block" in class_name or "codeblock" in class_name
        for class_name in classes
    ):
        code = node.get_text("\n", strip=True)
        if not code:
            return None
        language = extract_code_language(node)
        opener = f"```{language}".rstrip()
        return f"{opener}\n{code}\n```"

    if node.name in HEADING_PREFIX:
        text = normalize_text(node.get_text(" ", strip=True))
        return HEADING_PREFIX[node.name] + text if text else None

    if node.name == "p":
        text = normalize_text(node.get_text(" ", strip=True))
        return text if text else None

    if node.name in {"ul", "ol"}:
        return render_list(node)

    if node.name == "blockquote":
        text = normalize_text(node.get_text(" ", strip=True))
        return f"> {text}" if text else None

    if node.name == "pre":
        code = node.get_text("\n", strip=True)
        if not code:
            return None
        language = extract_code_language(node)
        opener = f"```{language}".rstrip()
        return f"{opener}\n{code}\n```"

    if node.name == "table":
        return render_table(node)

    if node.name in {"section", "article", "main", "div"}:
        child_blocks = render_children(node)
        return "\n\n".join(child_blocks) if child_blocks else None

    return None


def render_children(parent: Tag) -> list[str]:
    blocks: list[str] = []
    inline_buffer: list[str] = []

    def flush_inline_buffer() -> None:
        if not inline_buffer:
            return
        text = normalize_text(" ".join(inline_buffer))
        if text and text not in SKIP_LINE_VALUES:
            blocks.append(text)
        inline_buffer.clear()

    for child in parent.children:
        if isinstance(child, NavigableString):
            text = normalize_text(str(child))
            if text:
                inline_buffer.append(text)
            continue

        if not isinstance(child, Tag):
            continue

        if child.name in {
            "section",
            "article",
            "main",
            "div",
            "p",
            "ul",
            "ol",
            "pre",
            "blockquote",
            "table",
        } or child.name in HEADING_PREFIX:
            flush_inline_buffer()
            block = render_block(child)
            if block:
                blocks.append(block)
            continue

        if child.name == "br":
            flush_inline_buffer()
            continue

        text = normalize_text(child.get_text(" ", strip=True))
        if text:
            inline_buffer.append(text)

    flush_inline_buffer()
    return blocks


class WebContentService:
    def __init__(self, *, per_request_timeout: int = 8):
        self.per_request_timeout = per_request_timeout
        self.user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )

    async def fetch_many(self, urls: list[str]) -> list[dict[str, Any]]:
        tasks = [asyncio.create_task(self.fetch_and_extract(url)) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        normalized: list[dict[str, Any]] = []

        for url, result in zip(urls, results, strict=False):
            if isinstance(result, Exception):
                normalized.append(
                    {
                        "url": url,
                        "title": None,
                        "text": None,
                        "preview": None,
                        "status": "failed",
                    }
                )
                continue
            normalized.append(result)

        return normalized

    async def fetch_and_extract(self, url: str) -> dict[str, Any]:
        return await asyncio.wait_for(
            asyncio.to_thread(self._fetch_and_extract_sync, url),
            timeout=self.per_request_timeout,
        )

    def summarize(
        self,
        *,
        query: str,
        title: str,
        snippet: str,
        content: str,
        max_chars: int = 420,
    ) -> str:
        text = " ".join(part for part in [snippet, content] if part).strip()
        if not text:
            return f"{title}: no readable content extracted."

        text = re.sub(r"\s+", " ", text)
        summary = (
            text[:max_chars].rsplit(" ", 1)[0].strip()
            if len(text) > max_chars
            else text
        )
        return summary or text[:max_chars]

    def clean_text(self, text: str, max_chars: int | None = 4000) -> str:
        normalized = re.sub(r"\n{3,}", "\n\n", text).strip()
        if max_chars is None:
            return normalized
        return normalized[:max_chars]

    def build_preview(
        self, blocks: list[str], *, max_chars: int = 1600, max_blocks: int = 6
    ) -> str:
        preview_blocks: list[str] = []

        for block in blocks:
            block_text = block.strip()
            if not block_text:
                continue

            if len(preview_blocks) >= max_blocks:
                break

            candidate_blocks = [*preview_blocks, block_text]
            candidate_text = "\n\n".join(candidate_blocks)

            if len(candidate_text) <= max_chars:
                preview_blocks.append(block_text)
                continue

            if not preview_blocks:
                preview_blocks.append(self._truncate_block(block_text, max_chars))
            break

        return "\n\n".join(preview_blocks).strip()

    def extract_from_html(self, *, url: str, html: str) -> dict[str, Any]:
        soup = BeautifulSoup(html, "html.parser")
        title = normalize_text(soup.title.get_text(" ", strip=True)) if soup.title else url
        root = find_content_root(soup)
        blocks = render_children(root)
        text = self.clean_text("\n\n".join(blocks), max_chars=None)
        preview = self.build_preview(blocks)

        return {
            "url": url,
            "title": title or url,
            "text": text,
            "preview": preview,
            "status": "completed",
        }

    def _truncate_block(self, block: str, max_chars: int) -> str:
        if len(block) <= max_chars:
            return block

        if block.startswith("```"):
            lines = block.splitlines()
            opener = lines[0]
            body_lines: list[str] = []
            remaining = max_chars - len(opener) - len("\n```\n...")

            for line in lines[1:]:
                if line.strip() == "```":
                    continue
                if remaining <= 0:
                    break
                if len(line) + 1 > remaining:
                    body_lines.append(line[: max(remaining - 3, 0)].rstrip())
                    break
                body_lines.append(line)
                remaining -= len(line) + 1

            body_lines.append("...")
            return "\n".join([opener, *body_lines, "```"])

        if block.startswith("|"):
            kept_rows: list[str] = []
            current_length = 0

            for row in block.splitlines():
                projected_length = current_length + len(row) + (1 if kept_rows else 0)
                if kept_rows and projected_length > max_chars:
                    break
                kept_rows.append(row)
                current_length = projected_length

            return "\n".join(kept_rows)

        truncated = block[:max_chars].rsplit(" ", 1)[0].strip()
        if not truncated:
            truncated = block[:max_chars].strip()
        return f"{truncated}..."

    def _fetch_and_extract_sync(self, url: str) -> dict[str, Any]:
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

        return self.extract_from_html(url=url, html=html)
