from app.retrieval.vectorstore import build_or_load_vectorstore
from app.retrieval.document_loader import load_pdf_documents, split_documents
from app.retrieval.hybrid_retriever import HybridRetriever
from app.config import RAW_DOCS_DIR
from app.utils.state_utils import append_agent_message


TOPIC_QUERY_MAP = {
    "HBM": [
        "HBM architecture high bandwidth memory thermal limitation",
        "HBM 3D stacked memory TSV bandwidth power limitation",
        "HBM4 direction high bandwidth memory packaging thermal issue",
    ],
    "PIM": [
        "processing in memory architecture adoption challenge",
        "PIM processing-near-memory processing-using-memory architecture",
        "HBM-PIM in-memory computing adoption limitation coherence programming model",
    ],
    "CXL": [
        "CXL architecture memory expansion pooling disaggregation",
        "Compute Express Link memory semantics cache coherence type 3 device",
        "CXL memory expansion unified memory pooling deployment limitation",
    ],
}


def detect_topics_from_query(query: str) -> list[str]:
    q = query.lower()
    topics = []

    if "hbm" in q:
        topics.append("HBM")
    if "pim" in q:
        topics.append("PIM")
    if "cxl" in q:
        topics.append("CXL")

    return topics


def _doc_to_chunk(doc):
    return {
        "source_file": doc.metadata.get("source_file", "unknown"),
        "topic": doc.metadata.get("topic", "UNKNOWN"),
        "doc_role": doc.metadata.get("doc_role", "general"),
        "page": doc.metadata.get("page", ""),
        "content": doc.page_content,
    }


def _dedupe_docs(docs):
    unique = []
    seen = set()

    for doc in docs:
        key = (
            doc.metadata.get("source_file", ""),
            doc.metadata.get("page", ""),
            doc.page_content[:200],
        )
        if key not in seen:
            seen.add(key)
            unique.append(doc)

    return unique


def rag_agent(state):
    print("\n[RAG Agent] started")

    vectorstore = build_or_load_vectorstore()
    docs = split_documents(load_pdf_documents(str(RAW_DOCS_DIR)))
    retriever = HybridRetriever(vectorstore, docs)

    query = state["global_info"]["query"]
    topics = detect_topics_from_query(query)

    print(f"[RAG Agent] topics = {topics}")

    rag_by_topic = {}
    all_docs = []

    # topic별 quota
    topic_limit = 3

    if not topics:
        general_docs = retriever.retrieve(
            query=query,
            topic=None,
            k_dense=6,
            k_sparse=6,
            limit=6,
        )
        general_docs = _dedupe_docs(general_docs)
        rag_by_topic["GENERAL"] = [_doc_to_chunk(doc) for doc in general_docs]
        all_docs.extend(general_docs)

    else:
        for topic in topics:
            topic_docs = []

            queries = TOPIC_QUERY_MAP.get(topic, [topic])
            for q in queries:
                retrieved = retriever.retrieve(
                    query=q,
                    topic=topic,
                    k_dense=4,
                    k_sparse=4,
                    limit=topic_limit,
                )
                topic_docs.extend(retrieved)

            topic_docs = _dedupe_docs(topic_docs)[:topic_limit]
            rag_by_topic[topic] = [_doc_to_chunk(doc) for doc in topic_docs]
            all_docs.extend(topic_docs)

            print(f"[RAG Agent] {topic} docs = {len(topic_docs)}")

    all_docs = _dedupe_docs(all_docs)
    rag_chunks = [_doc_to_chunk(doc) for doc in all_docs]

    state["retrieval_data"]["rag_raw_chunks"] = rag_chunks
    state["retrieval_data"]["rag_by_topic"] = rag_by_topic
    append_agent_message(
        state,
        "rag_agent",
        f"retrieved {len(rag_chunks)} document chunks across topics {list(rag_by_topic.keys())}",
    )

    print(f"[RAG Agent] retrieved_docs(total) = {len(rag_chunks)}")
    print(f"[RAG Agent] rag_by_topic keys = {list(rag_by_topic.keys())}")
    print([doc.metadata.get("topic") for doc in docs[:10]])
    print("[RAG Agent] finished")

    return state
