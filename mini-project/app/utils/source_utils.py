from typing import List, Dict
from app.config import ALLOWED_TECHS, COMPETITORS


def detect_technology(text: str) -> str:
    upper = text.upper()
    if "HBM4" in upper or "HBM" in upper:
        return "HBM4"
    if "PIM" in upper:
        return "PIM"
    if "CXL" in upper:
        return "CXL"
    return "UNKNOWN"


def detect_competitor(text: str):
    lower = text.lower()
    if "samsung" in lower:
        return "Samsung"
    if "micron" in lower:
        return "Micron"
    return None


def detect_stance(text: str) -> str:
    lower = text.lower()
    negative_keywords = ["limitation", "delay", "risk", "issue", "problem", "challenge"]
    positive_keywords = ["launch", "improvement", "success", "leadership", "roadmap", "expansion"]

    if any(k in lower for k in negative_keywords):
        return "negative"
    if any(k in lower for k in positive_keywords):
        return "positive"
    return "neutral"


def normalize_web_results(web_raw_results: List[str]) -> List[dict]:
    normalized = []
    for item in web_raw_results:
        tech = detect_technology(item)
        comp = detect_competitor(item)
        stance = detect_stance(item)

        if tech in ALLOWED_TECHS and (comp in COMPETITORS or comp is None):
            normalized.append({
                "technology": tech,
                "competitor": comp,
                "claim": item[:400],
                "source": "web_search",
                "url": "",
                "stance": stance,
                "confidence": "medium",
                "matched_query": item[:120]
            })
    return normalized