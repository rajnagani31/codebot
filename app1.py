import bs4
from langchain_community.document_loaders import WebBaseLoader, PlaywrightURLLoader
from bs4 import BeautifulSoup
import re, requests, os

def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Remove scripts/styles
    for s in soup(["script", "style", "nav", "footer"]):
        s.decompose()
    # Get text and clean whitespace
    text = soup.get_text()
    # Normalize whitespace: multiple spaces/newlines → single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text


# Only keep post title, headers, and content from the full HTML.
bs4_strainer = bs4.SoupStrainer(class_=("post-title", "post-header", "post-content"))
loader = WebBaseLoader(
    web_paths=("https://lilianweng.github.io/posts/2023-06-23-agent/",),
    bs_kwargs={"parse_only": bs4_strainer},
)
docs = loader.load()

assert len(docs) == 1
# print(f"Total characters: {len(docs[0].page_content)}")
# print(docs[0].page_content[:500])


# loader = WebBaseLoader(web_paths=("https://docs.langchain.com/oss/python/langchain/rag#loading-documents",))
# news = WebBaseLoader(web_path=("https://www.screener.in/company/ETERNAL/consolidated/",), bs_kwargs={"parse_only": BeautifulSoup}, text_content_generators=[clean_html])

# CORRECT: list stays as single argument
# loader = WebBaseLoader(web_paths=["https://docs.langchain.com/oss/python/langchain/rag#loading-documents"])

# docs = news.load()
# assert len(docs) == 1
# print(f"Total characters: {len(docs[0].page_content)}")
# print(docs[0].page_content[:])


# loader = PlaywrightURLLoader(
#     urls=["https://www.screener.in/company/ETERNAL/consolidated/"],
#     remove_selectors=[
#         "nav", 
#         "footer", 
#         "[class*='header']", 
#         "[class*='ad']", 
#         ".CompanyHeader-module_header__footer_1x2tY",  # Screener-specific
#         "table.ProTable-module_root__table_3T8vA"  # Skip raw tables if too noisy
#     ],
#     wait_until="networkidle",
#     headless=True  # Faster, no browser window
# )
# docs = loader.load()
# print(f"Total characters: {len(docs[0].page_content)}")



headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36..."
}

def fetch_with_headers(url):
    resp = requests.get(url, headers=headers)
    soup = BeautifulSoup(resp.text, "html.parser")
    # Remove all non-content elements
    for elem in soup.select("nav, footer, header, script, style, .ad, .sidebar, .menu, meta, link, noscript"):
        elem.decompose()
    # Extract structured sections with labels
    sections = []
    for section in soup.select("section, .company-ratios, .ranges-table, .data-table, #quarters, #profit-loss, #balance-sheet, #cash-flow"):
        heading = section.find(["h2", "h3", "h4"])
        title = heading.get_text(strip=True) if heading else ""
        rows = []
        for tr in section.find_all("tr"):
            cells = [td.get_text(strip=True) for td in tr.find_all(["th", "td"])]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            section_text = f"\n--- {title} ---\n" if title else "\n"
            section_text += "\n".join(rows)
            sections.append(section_text)
    # Fallback: if no structured sections found, get cleaned text
    if not sections:
        text = soup.get_text(separator="\n")
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()
    return "\n".join(sections)


url = "https://docs.langchain.com/oss/python/langchain/rag#loading-documents"
text = fetch_with_headers(url)
print(f"Total characters: {len(text)}")
print(text[:2000])