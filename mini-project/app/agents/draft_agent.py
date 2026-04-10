import re
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.prompts.draft_prompt import DRAFT_PROMPT
from app.utils.trl_utils import build_trl_limitations_note
from app.utils.state_utils import append_agent_message


# -------- 길이 제한 --------
MAX_CHARS_PER_TOPIC_RAG = 2200
MAX_CHARS_PER_TECH_WEB = 2200
MAX_CHARS_QUERY = 1200
MAX_CHARS_TRL = 1500
MAX_CHARS_REFERENCE = 2000
MAX_TOTAL_PROMPT = 18000

MAX_WEB_ITEMS_PER_TECH = 5
MAX_RAG_ITEMS_PER_TOPIC = 3
MAX_CHARS_REVIEW_FEEDBACK = 1800


def sanitize_text(text: str) -> str:
    """
    OpenAI 요청 JSON을 깨뜨릴 수 있는 문자 제거
    """
    if not isinstance(text, str):
        text = str(text)

    # null byte 제거
    text = text.replace("\x00", " ")

    # 제어문자 제거 (\n, \t는 유지)
    text = re.sub(r"[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]", " ", text)

    # surrogate / 깨진 유니코드 제거
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")

    # 너무 많은 공백 정리
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def trim_text(text: str, max_chars: int) -> str:
    return sanitize_text(text)[:max_chars]


def build_rag_text(rag_context_items: list) -> str:
    """
    일반 RAG context — topic별 균등 분배
    """
    by_topic = defaultdict(list)
    for item in rag_context_items:
        by_topic[item.get("topic", "UNKNOWN")].append(item)

    lines = []
    for topic, items in by_topic.items():
        topic_text_parts = [f"\n===== {topic} (일반 RAG) =====\n"]

        for item in items[:MAX_RAG_ITEMS_PER_TOPIC]:
            topic_text_parts.append(
                f"""
[PDF]
파일명: {item.get('source_file', 'unknown')}
역할: {item.get('doc_role', 'general')}
내용:
{trim_text(item.get('content', ''), 900)}
"""
            )

        topic_text = "\n".join(topic_text_parts)
        lines.append(trim_text(topic_text, MAX_CHARS_PER_TOPIC_RAG))

    return "\n".join(lines)


def build_rag_by_topic_text(rag_by_topic: dict) -> str:
    """
    topic별 RAG context — topic별 균등 분배
    """
    lines = []

    for topic, docs in rag_by_topic.items():
        topic_text_parts = [f"\n===== {topic} CONTEXT =====\n"]

        for item in docs[:MAX_RAG_ITEMS_PER_TOPIC]:
            topic_text_parts.append(
                f"""
[PDF]
파일명: {item.get('source_file', 'unknown')}
역할: {item.get('doc_role', 'general')}
내용:
{trim_text(item.get('content', ''), 1000)}
"""
            )

        topic_text = "\n".join(topic_text_parts)
        lines.append(trim_text(topic_text, MAX_CHARS_PER_TOPIC_RAG))

    return "\n".join(lines)


def build_web_text(web_context_items: list) -> str:
    """
    WEB context — 기술별 균등 분배
    """
    by_tech = defaultdict(list)
    for item in web_context_items:
        by_tech[item.get("technology", "UNKNOWN")].append(item)

    lines = []

    for tech, items in by_tech.items():
        tech_text_parts = [f"\n===== {tech} WEB =====\n"]

        for item in items[:MAX_WEB_ITEMS_PER_TECH]:
            tech_text_parts.append(
                f"""
[WEB]
경쟁사: {sanitize_text(item.get('competitor', ''))}
제목: {trim_text(item.get('title', ''), 250)}
요약: {trim_text(item.get('snippet', ''), 500)}
URL: {sanitize_text(item.get('url', ''))}
TRL: {sanitize_text(item.get('trl_label', ''))} (confidence: {sanitize_text(item.get('trl_confidence', ''))})
TRL 근거: {trim_text(item.get('trl_reason', ''), 250)}
"""
            )

        tech_text = "\n".join(tech_text_parts)
        lines.append(trim_text(tech_text, MAX_CHARS_PER_TECH_WEB))

    return "\n".join(lines)


def build_reference_text(rag_context_items: list, web_context_items: list) -> str:
    """
    REFERENCE 섹션 작성용 실제 소스 목록
    """
    pdf_sources = sorted(
        set(
            item.get("source_file", "")
            for item in rag_context_items
            if item.get("source_file")
        )
    )

    web_sources = sorted(
        set(
            f"{sanitize_text(item.get('title', '(제목 없음)'))} | {sanitize_text(item.get('url', ''))}"
            for item in web_context_items[:30]
            if item.get("url")
        )
    )

    lines = ["[PDF 소스 목록]"]
    for f in pdf_sources:
        lines.append(f"- {f}")

    lines.append("\n[WEB 소스 목록]")
    for w in web_sources:
        lines.append(f"- {w}")

    return "\n".join(lines)


def build_review_feedback_text(review_feedback: list[str]) -> str:
    if not review_feedback:
        return "이전 검토 피드백 없음"

    lines = ["[이전 검토 피드백 - 반드시 모두 반영할 것]"]
    for item in review_feedback:
        lines.append(f"- {sanitize_text(item)}")
    return trim_text("\n".join(lines), MAX_CHARS_REVIEW_FEEDBACK)


def enforce_prompt_limit(
    query_text: str,
    rag_text: str,
    rag_by_topic_text: str,
    web_text: str,
    trl_limitations: str,
    reference_sources: str,
    review_feedback_text: str,
) -> dict:
    """
    prompt 전체 길이가 너무 길면 비중이 큰 섹션부터 줄인다.
    """
    sections = {
        "query_text": query_text,
        "rag_text": rag_text,
        "rag_by_topic_text": rag_by_topic_text,
        "web_text": web_text,
        "trl_limitations": trl_limitations,
        "reference_sources": reference_sources,
        "review_feedback_text": review_feedback_text,
    }

    temp_prompt = DRAFT_PROMPT.format(
        query=sections["query_text"],
        rag_context=sections["rag_text"],
        rag_by_topic=sections["rag_by_topic_text"],
        web_context=sections["web_text"],
        trl_limitations=sections["trl_limitations"],
        reference_sources=sections["reference_sources"],
        review_feedback=sections["review_feedback_text"],
    )
    temp_prompt = sanitize_text(temp_prompt)

    if len(temp_prompt) <= MAX_TOTAL_PROMPT:
        return sections

    # 많이 차지하는 순서대로 줄이기
    sections["web_text"] = trim_text(sections["web_text"], 5000)
    sections["rag_by_topic_text"] = trim_text(sections["rag_by_topic_text"], 5000)
    sections["rag_text"] = trim_text(sections["rag_text"], 3500)
    sections["reference_sources"] = trim_text(sections["reference_sources"], 1200)
    sections["review_feedback_text"] = trim_text(sections["review_feedback_text"], 1000)

    temp_prompt = DRAFT_PROMPT.format(
        query=sections["query_text"],
        rag_context=sections["rag_text"],
        rag_by_topic=sections["rag_by_topic_text"],
        web_context=sections["web_text"],
        trl_limitations=sections["trl_limitations"],
        reference_sources=sections["reference_sources"],
        review_feedback=sections["review_feedback_text"],
    )
    temp_prompt = sanitize_text(temp_prompt)

    if len(temp_prompt) <= MAX_TOTAL_PROMPT:
        return sections

    # 그래도 길면 더 강하게 축소
    sections["web_text"] = trim_text(sections["web_text"], 3000)
    sections["rag_by_topic_text"] = trim_text(sections["rag_by_topic_text"], 3000)
    sections["rag_text"] = trim_text(sections["rag_text"], 2500)
    sections["reference_sources"] = trim_text(sections["reference_sources"], 800)
    sections["review_feedback_text"] = trim_text(sections["review_feedback_text"], 700)

    return sections


def draft_agent(state):
    print("\n[Draft Agent] started")

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.1,
    )

    rag_context_items = state["retrieval_data"].get("rag_raw_chunks", [])
    rag_by_topic = state["retrieval_data"].get("rag_by_topic", {})
    web_context_items = state["retrieval_data"].get("web_raw_results", [])

    print(f"[Draft Agent] rag_context_items = {len(rag_context_items)}")
    print(f"[Draft Agent] web_context_items = {len(web_context_items)}")
    print(f"[Draft Agent] rag_by_topic keys = {list(rag_by_topic.keys())}")

    # 기술별 web 결과 분포 로깅
    web_by_tech = defaultdict(int)
    for item in web_context_items:
        web_by_tech[item.get("technology", "UNKNOWN")] += 1
    print(f"[Draft Agent] web_by_tech distribution = {dict(web_by_tech)}")

    rag_text = build_rag_text(rag_context_items)
    rag_by_topic_text = build_rag_by_topic_text(rag_by_topic)
    web_text = build_web_text(web_context_items)
    reference_sources = build_reference_text(rag_context_items, web_context_items)
    review_feedback_text = build_review_feedback_text(
        state["supervisor_ctrl"].get("review_feedback", [])
    )

    query_text = trim_text(state["global_info"]["query"], MAX_CHARS_QUERY)
    trl_limitations = trim_text(build_trl_limitations_note(), MAX_CHARS_TRL)
    reference_sources = trim_text(reference_sources, MAX_CHARS_REFERENCE)

    sections = enforce_prompt_limit(
        query_text=query_text,
        rag_text=rag_text,
        rag_by_topic_text=rag_by_topic_text,
        web_text=web_text,
        trl_limitations=trl_limitations,
        reference_sources=reference_sources,
        review_feedback_text=review_feedback_text,
    )

    prompt = DRAFT_PROMPT.format(
        query=sections["query_text"],
        rag_context=sections["rag_text"],
        rag_by_topic=sections["rag_by_topic_text"],
        web_context=sections["web_text"],
        trl_limitations=sections["trl_limitations"],
        reference_sources=sections["reference_sources"],
        review_feedback=sections["review_feedback_text"],
    )

    prompt = sanitize_text(prompt)

    print(f"[Draft Agent] prompt length = {len(prompt)} chars")
    print("[Draft Agent] calling LLM...")

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
    except Exception as e:
        print(f"[Draft Agent] LLM call failed: {e}")
        print("[Draft Agent] retrying with smaller prompt...")

        smaller_prompt = DRAFT_PROMPT.format(
            query=trim_text(sections["query_text"], 800),
            rag_context=trim_text(sections["rag_text"], 1800),
            rag_by_topic=trim_text(sections["rag_by_topic_text"], 1800),
            web_context=trim_text(sections["web_text"], 1800),
            trl_limitations=trim_text(sections["trl_limitations"], 1000),
            reference_sources=trim_text(sections["reference_sources"], 600),
            review_feedback=trim_text(sections["review_feedback_text"], 500),
        )
        smaller_prompt = sanitize_text(smaller_prompt)

        print(f"[Draft Agent] retry prompt length = {len(smaller_prompt)} chars")
        response = llm.invoke([HumanMessage(content=smaller_prompt)])

    print("[Draft Agent] draft generated")

    state["draft_work"]["current_draft"] = response.content
    state["draft_work"]["trl_justification"] = trl_limitations
    append_agent_message(
        state,
        "draft_agent",
        f"generated draft with prompt length {len(prompt)} chars using {len(rag_context_items)} rag chunks and {len(web_context_items)} web results",
    )
    return state
