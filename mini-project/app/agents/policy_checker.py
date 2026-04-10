import json
from typing import List

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from app.config import (
    COMPETITORS,
    OPENAI_API_KEY,
    OPENAI_MODEL,
    REPORT_TEMPLATE_SECTIONS,
    TARGET_TECHS,
)
from app.prompts.policy_prompt import POLICY_CHECK_PROMPT
from app.utils.state_utils import append_agent_message

SUBJECT_COMPANY = "SK hynix"


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


def extract_trl_table_rows(draft: str) -> List[dict]:
    rows = []
    for line in draft.splitlines():
        striped = line.strip()
        if not striped.startswith("|") or striped.count("|") < 5:
            continue

        cells = [cell.strip() for cell in striped.strip("|").split("|")]
        if len(cells) < 5:
            continue
        if cells[0] == "기술" or set("".join(cells)) <= {"-", " "}:
            continue

        rows.append({
            "technology": cells[0],
            "company": cells[1],
            "trl": cells[2],
            "estimate": cells[3],
            "reason": cells[4],
        })
    return rows


def normalize_technology(value: str) -> str:
    cleaned = value.strip().upper()
    if cleaned == "HBM":
        return "HBM4"
    return cleaned


def normalize_company(value: str) -> str:
    lowered = value.strip().lower()
    if lowered == "samsung":
        return "Samsung"
    if lowered == "micron":
        return "Micron"
    if lowered in {"sk hynix", "skhynix", "hynix"}:
        return SUBJECT_COMPANY
    return value.strip()


def find_trl_mentions(draft: str) -> dict:
    mentions = {}
    current_section = ""

    for raw_line in draft.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("### "):
            current_section = line
        elif line.startswith("**Samsung**"):
            current_section = "Samsung"
        elif line.startswith("**Micron**"):
            current_section = "Micron"

        company = None
        if "Samsung" in line or "삼성" in line:
            company = "Samsung"
        elif "Micron" in line or "마이크론" in line:
            company = "Micron"
        elif current_section in {"Samsung", "Micron"}:
            company = current_section

        tech = None
        upper = line.upper()
        if "HBM4" in upper or "HBM" in upper:
            tech = "HBM4"
        elif "PIM" in upper:
            tech = "PIM"
        elif "CXL" in upper:
            tech = "CXL"

        if not company or not tech:
            continue

        trl_value = None
        if "TRL 9" in line:
            trl_value = "TRL 9"
        elif "TRL 8" in line:
            trl_value = "TRL 8"
        elif "TRL 7" in line:
            trl_value = "TRL 7"
        elif "TRL 4-6" in line or "TRL 4~6" in line:
            trl_value = "TRL 4-6"
        elif "TRL 6" in line:
            trl_value = "TRL 6"
        elif "TRL 5" in line:
            trl_value = "TRL 5"
        elif "TRL 4" in line:
            trl_value = "TRL 4"
        elif "TRL 1-3" in line or "TRL 1~3" in line:
            trl_value = "TRL 1-3"
        elif "판단 불가" in line:
            trl_value = "판단 불가"

        if not trl_value:
            continue

        key = (tech, company)
        mentions.setdefault(key, set()).add(trl_value)

    return mentions


def check_trl_consistency(draft: str):
    feedback = []
    mentions = find_trl_mentions(draft)

    for (tech, company), values in sorted(mentions.items()):
        normalized = set(values)
        if len(normalized) > 1:
            joined = ", ".join(sorted(normalized))
            feedback.append(f"TRL 내부 모순: {tech}-{company} 값이 {joined}로 불일치함")

    return len(feedback) == 0, feedback


def check_trl_table_quality(draft: str):
    feedback = []
    rows = extract_trl_table_rows(draft)

    if not rows:
        return False, ["TRL 비교 표 누락 또는 파싱 불가"]

    expected_pairs = {(tech, comp) for tech in TARGET_TECHS for comp in COMPETITORS}
    actual_pairs = set()

    for row in rows:
        tech = normalize_technology(row["technology"])
        company = normalize_company(row["company"])
        trl = row["trl"].strip()
        estimate = row["estimate"].strip()
        reason = row["reason"].strip()

        if not company or company.lower() == "none":
            feedback.append(f"TRL 표 기업 값 누락: {row}")
            continue

        if tech not in TARGET_TECHS:
            feedback.append(f"TRL 표 기술 범위 위반: {tech}")
            continue

        if company == SUBJECT_COMPANY:
            # 분석 주체로 표에 등장할 수 있으므로 위반으로 보지 않는다.
            actual_pairs.add((tech, company))
            continue

        if company not in COMPETITORS:
            feedback.append(f"TRL 표 경쟁사 범위 위반: {company}")
            continue

        if not reason:
            feedback.append(f"TRL 표 판단 근거 누락: {tech}-{company}")

        if "TRL 4" in trl or "TRL 5" in trl or "TRL 6" in trl or "TRL 4-6" in trl:
            if "추정" not in estimate:
                feedback.append(f"TRL 표 추정 여부 누락: {tech}-{company}")

        actual_pairs.add((tech, company))

    missing_pairs = sorted(expected_pairs - actual_pairs)
    if missing_pairs:
        missing_text = ", ".join(f"{tech}-{comp}" for tech, comp in missing_pairs)
        feedback.append(f"TRL 표 필수 행 누락: {missing_text}")

    return len(feedback) == 0, feedback


def build_evidence_summary(state) -> str:
    rag_chunks = state["retrieval_data"].get("rag_raw_chunks", [])
    web_results = state["retrieval_data"].get("web_raw_results", [])

    rag_topics = {}
    for chunk in rag_chunks:
        topic = chunk.get("topic", "UNKNOWN")
        rag_topics[topic] = rag_topics.get(topic, 0) + 1

    web_pairs = {}
    for item in web_results:
        key = (
            item.get("technology", "UNKNOWN"),
            item.get("competitor") or "UNKNOWN",
        )
        web_pairs[key] = web_pairs.get(key, 0) + 1

    lines = [
        f"- RAG chunk count: {len(rag_chunks)}",
        f"- RAG topics: {json.dumps(rag_topics, ensure_ascii=False)}",
        f"- WEB result count: {len(web_results)}",
        f"- WEB tech/company distribution: {json.dumps({f'{k[0]}:{k[1]}': v for k, v in web_pairs.items()}, ensure_ascii=False)}",
    ]
    return "\n".join(lines)


class PolicyReviewResult(BaseModel):
    policy_pass: bool = Field(default=False)
    issues: List[str] = Field(default_factory=list)


def run_llm_policy_review(state, draft: str):
    try:
        llm = ChatOpenAI(
            model=OPENAI_MODEL,
            api_key=OPENAI_API_KEY,
            temperature=0,
        ).with_structured_output(PolicyReviewResult)

        prompt = POLICY_CHECK_PROMPT.format(
            query=state["global_info"]["query"],
            evidence_summary=build_evidence_summary(state),
            draft=draft,
        )
        result = llm.invoke(prompt)
        filtered_issues = []
        for issue in result.issues:
            # 과도하게 엄격한 표현은 blocking issue에서 제외
            if "Samsung, Micron 외의 다른 경쟁사가 포함되지 않음" in issue:
                continue
            if "보고서 톤이 R&D 전문가 수준이 아님" in issue:
                continue
            filtered_issues.append(issue)

        return len(filtered_issues) == 0, filtered_issues
    except Exception as e:
        return False, [f"LLM 정책 검토 실패: {e}"]


def policy_checker(state):
    draft = state["draft_work"]["current_draft"]

    structure_ok, structure_fb = check_structure(draft)
    trl_ok, trl_fb = check_trl_policy(draft)
    rag_ok, rag_fb = check_rag_coverage(state)
    web_ok, web_fb = check_web_coverage(state)
    stance_ok, stance_fb = check_stance_balance(state)
    table_ok, table_fb = check_trl_table_quality(draft)
    consistency_ok, consistency_fb = check_trl_consistency(draft)
    llm_ok, llm_fb = run_llm_policy_review(state, draft)

    state["draft_work"]["structure_passed"] = structure_ok
    state["draft_work"]["policy_passed"] = trl_ok and table_ok and consistency_ok and llm_ok
    state["draft_work"]["evidence_balance_passed"] = rag_ok and web_ok and stance_ok

    state["supervisor_ctrl"]["review_feedback"] = (
        structure_fb + trl_fb + rag_fb + web_fb + stance_fb + table_fb + consistency_fb + llm_fb
    )
    append_agent_message(
        state,
        "policy_checker",
        f"policy review completed with {len(state['supervisor_ctrl']['review_feedback'])} issues",
    )
    return state
