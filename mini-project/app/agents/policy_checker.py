from app.config import REPORT_TEMPLATE_SECTIONS


def check_structure(draft: str):
    feedback = []
    for sec in REPORT_TEMPLATE_SECTIONS:
        if sec not in draft:
            feedback.append(f"필수 섹션 누락: {sec}")
    return len(feedback) == 0, feedback


def check_trl_policy(draft: str):
    feedback = []

    if "TRL 4" in draft or "TRL 5" in draft or "TRL 6" in draft or "TRL 4-6" in draft:
        if "추정" not in draft:
            feedback.append("TRL 4~6 구간은 반드시 추정으로 명시해야 함")

    if "4.3. 한계" not in draft and "4.3 한계" not in draft:
        feedback.append("한계 섹션 누락")

    return len(feedback) == 0, feedback


def check_rag_coverage(state):
    feedback = []
    rag_chunks = state["retrieval_data"].get("rag_raw_chunks", [])

    topics = {chunk.get("topic") for chunk in rag_chunks}
    for required in ["HBM", "PIM", "CXL"]:
        if required not in topics:
            feedback.append(f"RAG 기술 배경 부족: {required}")

    return len(feedback) == 0, feedback


def check_web_coverage(state):
    feedback = []
    web_results = state["retrieval_data"].get("web_raw_results", [])

    if not web_results:
        feedback.append("웹 검색 근거 부족: 경쟁사/TRL 분석 불가")

    return len(feedback) == 0, feedback

def check_stance_balance(state):
    feedback = []
    web_results = state["retrieval_data"].get("web_raw_results", [])

    from collections import defaultdict
    by_tech = defaultdict(lambda: {"positive": 0, "negative": 0, "neutral": 0})
    for item in web_results:
        tech = item.get("technology", "UNKNOWN")
        stance = item.get("stance", "neutral")
        by_tech[tech][stance] += 1

    for tech, counts in by_tech.items():
        total = sum(counts.values())
        if total == 0:
            continue
        pos_ratio = counts["positive"] / total
        neg_ratio = counts["negative"] / total
        # 한쪽이 80% 이상이면 편향으로 판단
        if pos_ratio >= 0.8:
            feedback.append(f"교차 근거 부족: {tech} 긍정 편향 ({int(pos_ratio*100)}%)")
        elif neg_ratio >= 0.8:
            feedback.append(f"교차 근거 부족: {tech} 부정 편향 ({int(neg_ratio*100)}%)")

    return len(feedback) == 0, feedback


def policy_checker(state):
    draft = state["draft_work"]["current_draft"]

    structure_ok, structure_fb = check_structure(draft)
    trl_ok, trl_fb = check_trl_policy(draft)
    rag_ok, rag_fb = check_rag_coverage(state)
    web_ok, web_fb = check_web_coverage(state)
    stance_ok, stance_fb = check_stance_balance(state)

    state["draft_work"]["structure_passed"] = structure_ok
    state["draft_work"]["policy_passed"] = trl_ok
    state["draft_work"]["evidence_balance_passed"] = rag_ok and web_ok and stance_ok

    state["supervisor_ctrl"]["review_feedback"] = (
        structure_fb + trl_fb + rag_fb + web_fb + stance_fb
    )
    return state