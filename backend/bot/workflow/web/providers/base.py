from abc import ABC, abstractmethod
from typing import Any


class WebSearchProvider(ABC):
    provider_name = "base"

    @abstractmethod
    async def search(self, query: str, *, max_results: int = 3) -> dict[str, Any]:
        raise NotImplementedError
