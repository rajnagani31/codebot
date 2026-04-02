import asyncio
import os
import sys

BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

from bot.workflow.web.content_extractor import WebContentService


async def main():
    url = "https://example.com"
    service = WebContentService()

    page = await service.fetch_and_extract(url)

    print(f"URL   : {page.get('url')}")
    print(f"Title : {page.get('title')}")
    print(f"Status: {page.get('status')}")
    print("Text  :")
    print((page.get("text") or "")[:1000])


if __name__ == "__main__":
    asyncio.run(main())
