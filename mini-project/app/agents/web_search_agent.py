from typing import List
from app.config import TARGET_TECHS, COMPETITORS
from app.utils.tavily_utils import tavily_search
from app.utils.trl_utils import infer_trl_from_evidence
from app.utils.state_utils import append_agent_message


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


def build_supplement_queries(missing_info_log: list) -> List[str]:
    """Loop A 재진입 시 편향된 기술에 대해 반대 관점 보완 쿼리 생성"""
    queries = []
    for log in missing_info_log:
        for tech in TARGET_TECHS:
            if tech not in log:
                continue
            if "긍정 편향" in log:
                # 긍정 편향 → 부정/한계 관점 보완
                for comp in COMPETITORS:
                    queries.append(f"{comp} {tech} failure risk limitation concern analyst")
                    queries.append(f"{tech} technical challenge unsolved problem semiconductor")
            elif "부정 편향" in log:
                # 부정 편향 → 긍정/진척 관점 보완
                for comp in COMPETITORS:
                    queries.append(f"{comp} {tech} breakthrough progress achievement 2025")
                    queries.append(f"{tech} success commercialization milestone semiconductor")
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


def dedupe_results(results: list[dict]) -> list[dict]:
    unique = []
    seen = set()

    for item in results:
        key = (
            item.get("technology", ""),
            item.get("competitor", ""),
            item.get("url", ""),
            item.get("title", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return unique


def web_search_agent(state):
    print("\n[Web Search Agent] started")

    loop_a_count = state["supervisor_ctrl"].get("loop_a_count", 0)
    missing_logs = state["supervisor_ctrl"].get("missing_info_log", [])

    if loop_a_count > 0 and missing_logs:
        # 재검색: 편향 보완 쿼리만 실행
        queries = build_supplement_queries(missing_logs)
        print(f"[Web Search Agent] RETRY mode, supplement queries = {len(queries)}")
    else:
        # 최초 검색: 전체 쿼리 실행
        queries = build_queries()
        print(f"[Web Search Agent] total queries = {len(queries)}")

    # 재검색 시 기존 결과에 누적, 최초 검색 시 새로 시작
    if loop_a_count > 0:
        all_results = state["retrieval_data"].get("web_raw_results", [])
    else:
        all_results = []

    error_count = 0

    for q in queries:
        try:
            # 경쟁사 동향 쿼리는 6개월, 기술 현황은 1년
            if any(comp in q for comp in COMPETITORS):
                hits = tavily_search(q, max_results=4, days=180)
            else:
                hits = tavily_search(q, max_results=4, days=365)

            for hit in hits:
                joined = f"{hit.get('title', '')} {hit.get('content', '')}"
                techs = detect_technologies(joined)
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
            error_count += 1
            continue

    all_results = dedupe_results(all_results)
    state["retrieval_data"]["web_raw_results"] = all_results
    mode = "retry" if loop_a_count > 0 else "initial"
    append_agent_message(
        state,
        "web_search_agent",
        f"{mode} web search completed with {len(queries)} queries, {len(all_results)} collected results, {error_count} query errors",
    )
    print(f"[Web Search Agent] results = {len(all_results)}")
    print("[Web Search Agent] finished")
    return state
