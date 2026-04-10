from tavily import TavilyClient
from app.config import TAVILY_API_KEY
from datetime import datetime, timedelta

_client = TavilyClient(api_key=TAVILY_API_KEY)


def tavily_search(query: str, max_results: int = 5, days: int = 365):
    """
    days: 검색 기간 (기본 1년)
    - 경쟁사 동향/시장 신호: days=180 (6개월)
    - 기술 현황/논문 기반: days=365 (1년)
    """
    response = _client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answer=False,
        include_raw_content=False,
        days=days,       
    )
    return response.get("results", [])