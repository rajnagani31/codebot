import re

import bs4  # type: ignore
import requests
from bs4 import BeautifulSoup, NavigableString, Tag  # type: ignore

try:
    from langchain_community.document_loaders import PlaywrightURLLoader, WebBaseLoader
except ModuleNotFoundError:
    PlaywrightURLLoader = None
    WebBaseLoader = None


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for node in soup(["script", "style", "nav", "footer"]):
        node.decompose()
    text = soup.get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


if WebBaseLoader is not None:
    # Only keep post title, headers, and content from the full HTML.
    bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
    loader = WebBaseLoader(
        web_paths=("https://docs.langchain.com/oss/python/langchain/rag#loading-documents",),
        bs_kwargs={"parse_only": bs4_strainer},
    )
    docs = loader.load()
    # print('-------------',docs[0].page_content[:500])


# loader = PlaywrightURLLoader(
#     urls=["https://www.screener.in/company/ETERNAL/consolidated/"],
#     remove_selectors=[
#         "nav",
#         "footer",
#         "[class*='header']",
#         "[class*='ad']",
#         ".CompanyHeader-module_header__footer_1x2tY",
#         "table.ProTable-module_root__table_3T8vA",
#     ],
#     wait_until="networkidle",
#     headless=True,
# )


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}

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

    classes = node.get("class") or []
    for class_name in classes:
        if class_name.startswith("language-"):
            return class_name.removeprefix("language-")
    code_child = node.find(["code", "div"], class_=re.compile(r"language-"))
    if code_child is None:
        return ""
    for class_name in code_child.get("class") or []:
        if class_name.startswith("language-"):
            return class_name.removeprefix("language-")
    return ""


def render_table(table: Tag) -> list[str]:
    lines: list[str] = []
    for row in table.find_all("tr"):
        cells = [normalize_text(cell.get_text(" ", strip=True)) for cell in row.find_all(["th", "td"])]
        cells = [cell for cell in cells if cell]
        if cells:
            lines.append("| " + " | ".join(cells) + " |")
    return lines


def render_list(list_node: Tag, indent: int = 0) -> list[str]:
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
                nested_parts.extend(render_list(child, indent + 1))
                continue

            if child.name == "pre":
                nested_parts.extend(render_block(child))
                continue

            if child.name == "table":
                nested_parts.extend(render_table(child))
                continue

            text = normalize_text(child.get_text(" ", strip=True))
            if text:
                inline_parts.append(text)

        item_text = normalize_text(" ".join(inline_parts))
        if item_text:
            lines.append(prefix + item_text)
        elif nested_parts:
            lines.append(prefix.rstrip())

        lines.extend(nested_parts)

    return lines


def render_block(node: Tag) -> list[str]:
    classes = node.get("class") or []
    if node.name == "div" and any("code-block" in class_name or "codeblock" in class_name for class_name in classes):
        code = node.get_text("\n", strip=True)
        if not code:
            return []
        language = extract_code_language(node)
        return [f"```{language}".rstrip(), code, "```"]

    if node.name in HEADING_PREFIX:
        text = normalize_text(node.get_text(" ", strip=True))
        return [HEADING_PREFIX[node.name] + text] if text else []

    if node.name == "p":
        text = normalize_text(node.get_text(" ", strip=True))
        return [text] if text else []

    if node.name in {"ul", "ol"}:
        return render_list(node)

    if node.name == "blockquote":
        text = normalize_text(node.get_text(" ", strip=True))
        return ["> " + text] if text else []

    if node.name == "pre":
        code = node.get_text("\n", strip=True)
        if not code:
            return []
        language = extract_code_language(node)
        return [f"```{language}".rstrip(), code, "```"]

    if node.name == "table":
        return render_table(node)

    if node.name in {"section", "article", "main", "div"}:
        return render_children(node)

    return []


def render_children(parent: Tag) -> list[str]:
    lines: list[str] = []
    inline_buffer: list[str] = []

    def flush_inline_buffer():
        if not inline_buffer:
            return
        text = normalize_text(" ".join(inline_buffer))
        if text and text not in SKIP_LINE_VALUES:
            lines.append(text)
        inline_buffer.clear()

    for child in parent.children:
        if isinstance(child, NavigableString):
            text = normalize_text(str(child))
            if text:
                inline_buffer.append(text)
            continue

        if not isinstance(child, Tag):
            continue

        if child.name in {"section", "article", "main", "div", "p", "ul", "ol", "pre", "blockquote", "table"} or child.name in HEADING_PREFIX:
            flush_inline_buffer()
            lines.extend(render_block(child))
            continue

        if child.name == "br":
            flush_inline_buffer()
            continue

        text = normalize_text(child.get_text(" ", strip=True))
        if text:
            inline_buffer.append(text)

    flush_inline_buffer()
    return lines


def fetch_with_headers(url: str, max_chars: int | None = 5000) -> str:
    response = requests.get(url, headers=HEADERS, timeout=20)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    root = find_content_root(soup)
    lines = render_children(root)

    text = "\n\n".join(line for line in lines if line and not line.isspace())
    text = re.sub(r"\n{3,}", "\n\n", text).strip()

    if max_chars is not None:
        return text[:max_chars]
    return text


# url = "https://docs.langchain.com/oss/python/langchain/rag#loading-documents"
url = "https://docs.langchain.com/oss/python/langchain/rag.md"
text = fetch_with_headers(url, max_chars=5000)
print(f"Total characters: {len(text)}")
print(text)
