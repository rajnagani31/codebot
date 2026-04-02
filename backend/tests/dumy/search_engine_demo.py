import asyncio
import os
import sys

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from bot.workflow.web.content_extractor import WebContentService
from bot.workflow.web.providers.duckduckgo_provider import DuckDuckGoSearchProvider


async def main():
    query = "what is today in india?"
    provider = DuckDuckGoSearchProvider()
    content_service = WebContentService()

    payload = await provider.search(query, max_results=3)
    results = payload.get("results", [])

    print(f"Query: {query}")
    print(f"Provider: {payload.get('provider')}")
    print("-" * 80)

    for item in results:
        print(f"Rank   : {item.get('rank')}")
        print(f"Title  : {item.get('title')}")
        print(f"URL    : {item.get('url')}")
        print(f"Domain : {item.get('domain')}")
        print(f"Snippet: {item.get('snippet')}")
        print("-" * 80)

    urls = [item.get("url") for item in results if item.get("url")]
    if not urls:
        print("No URLs found.")
        return
    print("------------------------------------------------------url", urls)
    pages = await content_service.fetch_many(urls)

    print("\nReadable content")
    print("=" * 80)
    for page in pages:
        text = (page.get("text") or "")[:500]
        print(f"URL   : {page.get('url')}")
        print(f"Title : {page.get('title')}")
        print(f"Status: {page.get('status')}")
        print(f"Text  : {text}")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
