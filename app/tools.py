
from tavily import TavilyClient

from app.config import settings


def search_web(query: str) -> list[dict]:
    """Search the web using Tavily."""

    if not settings.tavily_api_key:
        return []

    client = TavilyClient(api_key=settings.tavily_api_key)

    response = client.search(
        query=query,
        max_results=5,
        search_depth="basic",
    )

    results = []

    for item in response.get("results", []):
        results.append(
            {
                "title": item.get("title", "Untitled"),
                "url": item.get("url", ""),
                "content": item.get("content", ""),
                "source_type": "web",
            }
        )

    return results
