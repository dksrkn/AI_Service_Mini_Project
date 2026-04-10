import re
from collections import defaultdict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

from app.config import OPENAI_API_KEY, OPENAI_MODEL
from app.prompts.draft_prompt import DRAFT_PROMPT
from app.utils.trl_utils import build_trl_limitations_note

MAX_CHARS_PER_TOPIC_RAG = 3000
MAX_CHARS_PER_TECH_WEB  = 3000
MAX_CHARS_QUERY         = 1500
MAX_CHARS_TRL           = 2000
MAX_CHARS_REFERENCE     = 3000


def sanitize_text(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\x00", " ")
    text = re.sub(r"[\x01-\x08\x0B-\x0C\x0E-\x1F\x7F]", " ", text)
    text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return text


def trim_text(text: str, max_chars: int) -> str:
    text = sanitize_text(text)
    return text[:max_chars]


def build_rag_text(rag_context_items: list) -> str:
    """일반 RAG context — topic별 균등 분배"""
    by_topic = defaultdict(list)
    for item in rag_context_items:
        by_topic[item.get("topic", "UNKNOWN")].append(item)

    lines = []
    for topic, items in by_topic.items():
        topic_text = f"\n===== {topic} (일반 RAG) =====\n"
        for item in items:
            topic_text += f"""
[PDF]
파일명: {item.get('source_file', 'unknown')}
역할: {item.get('doc_role', 'general')}
내용:
{sanitize_text(item.get('content', ''))}
"""
        lines.append(trim_text(topic_text, MAX_CHARS_PER_TOPIC_RAG))
    return "\n".join(lines)


def build_rag_by_topic_text(rag_by_topic: dict) -> str:
    """topic별 RAG context — topic별 균등 분배"""
    lines = []
    for topic, docs in rag_by_topic.items():
        topic_text = f"\n===== {topic} CONTEXT =====\n"
        for item in docs:
            topic_text += f"""
[PDF]
파일명: {item.get('source_file', 'unknown')}
역할: {item.get('doc_role', 'general')}
내용:
{sanitize_text(item.get('content', ''))}
"""
        lines.append(trim_text(topic_text, MAX_CHARS_PER_TOPIC_RAG))
    return "\n".join(lines)


def build_web_text(web_context_items: list) -> str:
    """WEB context — 기술별 균등 분배"""
    by_tech = defaultdict(list)
    for item in web_context_items:
        by_tech[item.get("technology", "UNKNOWN")].append(item)

    lines = []
    for tech, items in by_tech.items():
        tech_text = f"\n===== {tech} WEB =====\n"
        for item in items[:10]:
            tech_text += f"""
[WEB]
경쟁사: {item.get('competitor', '')}
제목: {sanitize_text(item.get('title', ''))}
요약: {sanitize_text(item.get('snippet', ''))}
URL: {item.get('url', '')}
TRL: {item.get('trl_label', '')} (confidence: {item.get('trl_confidence', '')})
TRL 근거: {sanitize_text(item.get('trl_reason', ''))}
"""
        lines.append(trim_text(tech_text, MAX_CHARS_PER_TECH_WEB))
    return "\n".join(lines)


def build_reference_text(rag_context_items: list, web_context_items: list) -> str:
    """REFERENCE 섹션 작성용 실제 소스 목록"""
    pdf_sources = sorted(set(
        item.get("source_file", "")
        for item in rag_context_items
        if item.get("source_file")
    ))

    web_sources = sorted(set(
        f"{item.get('title', '(제목 없음)')} | {item.get('url', '')}"
        for item in web_context_items
        if item.get("url")
    ))

    lines = ["[PDF 소스 목록]"]
    for f in pdf_sources:
        lines.append(f"- {f}")
    lines.append("\n[WEB 소스 목록]")
    for w in web_sources:
        lines.append(f"- {w}")
    return "\n".join(lines)


def draft_agent(state):
    print("\n[Draft Agent] started")

    llm = ChatOpenAI(
        model=OPENAI_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=0.1
    )

    rag_context_items = state["retrieval_data"].get("rag_raw_chunks", [])
    rag_by_topic      = state["retrieval_data"].get("rag_by_topic", {})
    web_context_items = state["retrieval_data"].get("web_raw_results", [])

    print(f"[Draft Agent] rag_context_items = {len(rag_context_items)}")
    print(f"[Draft Agent] web_context_items = {len(web_context_items)}")
    print(f"[Draft Agent] rag_by_topic keys = {list(rag_by_topic.keys())}")

    # 기술별 web 결과 분포 로깅
    web_by_tech = defaultdict(int)
    for item in web_context_items:
        web_by_tech[item.get("technology", "UNKNOWN")] += 1
    print(f"[Draft Agent] web_by_tech distribution = {dict(web_by_tech)}")

    rag_text          = build_rag_text(rag_context_items)
    rag_by_topic_text = build_rag_by_topic_text(rag_by_topic)
    web_text          = build_web_text(web_context_items)
    reference_sources = build_reference_text(rag_context_items, web_context_items)

    query_text        = trim_text(state["global_info"]["query"], MAX_CHARS_QUERY)
    trl_limitations   = trim_text(build_trl_limitations_note(), MAX_CHARS_TRL)
    reference_sources = trim_text(reference_sources, MAX_CHARS_REFERENCE)

    prompt = DRAFT_PROMPT.format(
        query=query_text,
        rag_context=rag_text,
        rag_by_topic=rag_by_topic_text,
        web_context=web_text,
        trl_limitations=trl_limitations,
        reference_sources=reference_sources,
    )

    prompt = sanitize_text(prompt)

    print(f"[Draft Agent] prompt length = {len(prompt)} chars")
    print("[Draft Agent] calling LLM...")

    response = llm.invoke([HumanMessage(content=prompt)])

    print("[Draft Agent] draft generated")

    state["draft_work"]["current_draft"] = response.content
    state["draft_work"]["trl_justification"] = trl_limitations
    return state