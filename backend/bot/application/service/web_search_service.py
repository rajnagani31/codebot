from datetime import datetime
from urllib.parse import urlparse

from ..config import SessionLocal
from ..model.web_search import WebSearchRun, WebSource
from ...workflow.pg_vector.pg_vector_service import PGVectorService
from ...workflow.web.content_extractor import WebContentService
from ...workflow.web.providers.base import WebSearchProvider
from ...workflow.web.providers.duckduckgo_provider import DuckDuckGoSearchProvider


class WebSearchService:
    def __init__(
        self,
        *,
        provider: WebSearchProvider | None = None,
        content_service: WebContentService | None = None,
        vector_service: PGVectorService | None = None,
    ):
        self.provider = provider or DuckDuckGoSearchProvider()
        self.content_service = content_service or WebContentService()
        self.vector_service = vector_service or PGVectorService(create_schema=False)

    async def search(
        self,
        *,
        query: str,
        user_id: int,
        thread_id: str,
        message_id: str,
        max_results: int = 3,
    ) -> dict:
        search_payload = await self.provider.search(query, max_results=max_results)
        search_results = list(search_payload.get("results", []))[:max_results]
        urls = [str(item.get("url") or "") for item in search_results if item.get("url")]
        fetched_pages = await self.content_service.fetch_many(urls)

        sources: list[dict] = []
        for item, page in zip(search_results, fetched_pages, strict=False):
            title = str(page.get("title") or item.get("title") or item.get("url") or "")
            content_text = str(page.get("text") or "")
            summary = self.content_service.summarize(
                query=query,
                title=title,
                snippet=str(item.get("snippet") or ""),
                content=content_text,
            )
            sources.append(
                {
                    "rank": int(item.get("rank") or 0),
                    "title": title,
                    "url": str(item.get("url") or ""),
                    "domain": str(item.get("domain") or urlparse(str(item.get("url") or "")).netloc),
                    "snippet": str(item.get("snippet") or ""),
                    "summary": summary,
                    "content_text": content_text,
                    "published_at": item.get("published_at"),
                    "status": page.get("status") or "completed",
                }
            )

        run_id = self.store_sources(
            query=query,
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            sources=sources,
            provider_name=str(search_payload.get("provider") or self.provider.provider_name),
        )

        return self.build_context_pack(query=query, run_id=run_id, sources=sources)

    async def read_web_page(self, url: str) -> dict:
        page = await self.content_service.fetch_and_extract(url)
        summary = self.content_service.summarize(
            query=url,
            title=str(page.get("title") or url),
            snippet="",
            content=str(page.get("text") or ""),
            max_chars=520,
        )
        return {
            "title": page.get("title") or url,
            "url": url,
            "summary": summary,
            "content_text": page.get("text") or "",
        }

    def build_context_pack(self, *, query: str, run_id: str, sources: list[dict]) -> dict:
        source_summaries = [
            {
                "rank": source["rank"],
                "title": source["title"],
                "url": source["url"],
                "domain": source["domain"],
                "snippet": source["snippet"],
                "summary": source["summary"],
            }
            for source in sources
        ]
        source_lines = [
            f"[{source['rank']}] {source['title']} ({source['domain']})\nURL: {source['url']}\nSummary: {source['summary']}"
            for source in source_summaries
        ]
        return {
            "run_id": run_id,
            "query": query,
            "sources": source_summaries,
            "context_text": "\n\n".join(source_lines),
            "tool_payload": {
                "query": query,
                "run_id": run_id,
                "sources": source_summaries,
            },
        }

    def store_sources(
        self,
        *,
        query: str,
        user_id: int,
        thread_id: str,
        message_id: str,
        sources: list[dict],
        provider_name: str,
    ) -> str:
        session = SessionLocal()
        now = datetime.utcnow()
        run = WebSearchRun(
            user_id=user_id,
            thread_id=thread_id,
            message_id=message_id,
            query=query,
            provider=provider_name,
            status="completed",
            result_count=len(sources),
            metadata_json={"source_count": len(sources)},
            created_at=now,
            completed_at=now,
        )

        try:
            session.add(run)
            session.flush()

            for source in sources:
                session.add(
                    WebSource(
                        run_id=run.id,
                        user_id=user_id,
                        thread_id=thread_id,
                        message_id=message_id,
                        rank=source["rank"],
                        title=source["title"],
                        url=source["url"],
                        domain=source["domain"],
                        snippet=source["snippet"],
                        summary=source["summary"],
                        content_text=source["content_text"],
                        metadata_json={
                            "status": source["status"],
                            "published_at": source.get("published_at"),
                        },
                    )
                )

                if source["content_text"]:
                    try:
                        self.vector_service.store(
                            user_id=user_id,
                            text=source["content_text"],
                            type_="web_source",
                            metadata={
                                "thread_id": thread_id,
                                "message_id": message_id,
                                "web_search_run_id": run.id,
                                "url": source["url"],
                                "title": source["title"],
                                "domain": source["domain"],
                            },
                        )
                    except Exception:
                        # Keep the chat response usable even if vector persistence is unavailable.
                        pass

            session.commit()
            return run.id
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
