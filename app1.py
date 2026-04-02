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

"""
read this file and implement everything were mentioned in this file : /home/ubuntu/Documents/test/Codebot/WEB_SEARCH_TOOL_APPROACH.md
Web search toggle management by user and agent or developer
Auto / Off / On

 Off: never bind web tools
 Auto: bind tool, model decides when needed
 On: bind tool and add prompt instruction to prefer current web sources
Best UX:

small toggle near prompt box
source cards under answer
loading states like Searching web..., Reading sources...

web search url flow might be:
only teck top 3 urls

fetch only these three urls with headers and cleaned text, then feed into context as sources with metadata (title, url, snippet, etc.)


-> make url fetching process in asyncio for get all three urls in parallel, and set timeout for each fetch to avoid long waits if is needed

Database design make a this type not only for web search but also every single process
which mode user used in this messages

only query and response llm
query + agent = langgrapgh agent flow
query + web search = web search flow
query + agent + web search = agent with web search flow

currently we not apply cache for web search results, but we can consider to cache the web search results for some time (e.g. 1 hour) to avoid repeated web search for same query in short time, and also to improve performance for agent with web search flow

Phase 1
add use_web request flag
create WebSearchProvider
create WebContentService
add web_search tool
bind tool optionally
return source summaries only

Phase 2
add read_web_page
add web_search_runs and web_sources
store citations in metadata_json
reuse vector_data for source chunks

Phase 3
add cache and dedupe (avide this functionality for now, but we can consider to add it in future if needed)
add frontend source cards
add SSE progress events
add search analytics and retry handling

Phase 4
Level 1: Main mode
    Show one main choice:

    Auto -> every thing is backend hardcoded, like model(gpt-4.o-mini), system prompt (same as current flow)
    Manual -> show all options and let user choose, like model choice, system prompt template choice, web search toggle, agent toggle, etc. in UI and also managed by api and backend flow
            model: gpt-4o-mini, gpt-4o, gpt-5,gemini models etc
            prompt style: chat, code, debug, review
            web search: off, auto, on
    Note : currently no need to show auto and manual choice in UI, only show manual choice and if user want auto then they can select all manual options as auto, like model choice auto, prompt style auto, web search auto etc. if user not select any option then also we can conside it as auto mode
add UI interface for llm choice model choice and web search toggle and system prompt template management

Best choice structure use choice configuration like this:
{
  "query": "how to optimize postgres vector search",
  "thread_id": "thread_123",
  "choice_config": {
    "mode": "auto",
    "model_mode": "auto",
    "model_name": null,
    "prompt_mode": "auto",
    "prompt_name": null,
    "web_mode": "auto"
  }
}

Manual example:

{
  "choice_config": {
    "mode": "manual",
    "model_mode": "manual",
    "model_name": "gpt-4o",
    "prompt_mode": "manual",
    "prompt_name": "debug",
    "web_mode": "on"
  }
}

read also this UI CHOICE MD file and implement everything were mentioned in this file : /home/ubuntu/Documents/test/Codebot/CHOICE_UI_LOGIC_APPROACH.md
read model selection
system prompt template selection
web search toggle management

"""



# AFTER APPLU INSTRUCTION

"""
Explain me our new code flow and this used via @router.post("/chat/stream") api endpoint.
    give me flow structur or diagram how how our api flow work after user ask any time of qestion 
    example : query-> create mode -> create db data -> fetch vector -> build llm messages -> start streaming response -> end -> store last new data and vector etc now give new flow..
-> also explain me the code flow when user ask question related to tool usage, like "how to use web search tool?" or "what is web search tool?" or "can you use web search tool to find latest information about xxx?" etc.

1. why we remove langgraph agent flow for now, give me the reason?
2. why tool system not work and called,  when user ask about tool related qestion?
3. why don't see our vector search result in our response, even user ask question related to vector search data?
"""