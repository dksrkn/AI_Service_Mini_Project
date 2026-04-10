from tavily import TavilyClient
from app.config import TAVILY_API_KEY

_client = TavilyClient(api_key=TAVILY_API_KEY)


def tavily_search(query: str, max_results: int = 5):
    response = _client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answer=False,
        include_raw_content=False,
    )
    return response.get("results", [])