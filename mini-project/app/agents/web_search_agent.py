from typing import List
from app.config import TARGET_TECHS, COMPETITORS
from app.utils.tavily_utils import tavily_search
from app.utils.trl_utils import infer_trl_from_evidence


def build_queries() -> List[str]:
    queries = []

    for tech in TARGET_TECHS:
        # 기술 자체 현황
        queries.append(f"{tech} latest semiconductor R&D progress")
        queries.append(f"{tech} research limitation bottleneck semiconductor")

        for comp in COMPETITORS:
            # 긍정 신호
            queries.append(f"{comp} {tech} roadmap announcement prototype sample production")
            # 부정/제약 신호
            queries.append(f"{comp} {tech} challenge limitation delay yield issue")
            # 간접 지표
            queries.append(f"{comp} {tech} patent conference hiring job posting")
    return queries


def infer_stance(text: str) -> str:
    lower = text.lower()
    neg_keys = ["delay", "issue", "risk", "challenge", "limitation", "yield", "bottleneck"]
    pos_keys = ["roadmap", "prototype", "sample", "production", "qualification", "announcement"]

    if any(k in lower for k in neg_keys):
        return "negative"
    if any(k in lower for k in pos_keys):
        return "positive"
    return "neutral"


def detect_technologies(text: str) -> list[str]:
    upper = text.upper()
    techs = []
    # CXL, PIM을 HBM보다 먼저 체크해서 복합 키워드 기사도 놓치지 않도록
    if "CXL" in upper or "COMPUTE EXPRESS LINK" in upper:
        techs.append("CXL")
    if "PIM" in upper or "PROCESSING-IN-MEMORY" in upper or "PROCESSING IN MEMORY" in upper:
        techs.append("PIM")
    if "HBM4" in upper:
        techs.append("HBM4")
    elif "HBM" in upper:
        techs.append("HBM4")
    return techs if techs else ["UNKNOWN"]


def detect_competitor(text: str):
    lower = text.lower()
    if "samsung" in lower:
        return "Samsung"
    if "micron" in lower:
        return "Micron"
    return None


def web_search_agent(state):
    print("\n[Web Search Agent] started")

    queries = build_queries()
    print(f"[Web Search Agent] total queries = {len(queries)}")

    all_results = []

    for q in queries:
        try:
            hits = tavily_search(q, max_results=4)
            for hit in hits:
                joined = f"{hit.get('title', '')} {hit.get('content', '')}"
                techs = detect_technologies(joined)  # 단수 → 복수 반환
                comp = detect_competitor(joined)
                trl_label, trl_confidence, trl_reason = infer_trl_from_evidence(joined)

                if techs == ["UNKNOWN"]:
                    continue
                if comp is not None and comp not in COMPETITORS:
                    continue

                # 하나의 기사가 여러 기술에 해당하면 각각 저장
                for tech in techs:
                    all_results.append({
                        "technology": tech,
                        "competitor": comp,
                        "title": hit.get("title", ""),
                        "snippet": hit.get("content", ""),
                        "url": hit.get("url", ""),
                        "source_type": "web",
                        "stance": infer_stance(joined),
                        "trl_label": trl_label,
                        "trl_confidence": trl_confidence,
                        "trl_reason": trl_reason,
                        "matched_query": q,
                    })
        except Exception as e:
            print(f"[Web Search Agent] error: {e}")
            continue

    state["retrieval_data"]["web_raw_results"] = all_results
    print(f"[Web Search Agent] results = {len(all_results)}")
    print("[Web Search Agent] finished")
    return state