import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from pypdf import PdfReader
from rank_bm25 import BM25Okapi

from app.config import RAW_DOCS_DIR
from app.retrieval.document_loader import infer_doc_tags, load_pdf_documents, split_documents
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.vectorstore import build_or_load_vectorstore


SECTION_PATTERNS = {
    "SUMMARY": [r"## SUMMARY", r"SUMMARY"],
    "HBM": [r"### 2\.1\. HBM 기술 현황", r"2\.1\. HBM 기술 현황"],
    "PIM": [r"### 2\.2\. PIM 기술 현황", r"2\.2\. PIM 기술 현황"],
    "CXL": [r"### 2\.3\. CXL 기술 현황", r"2\.3\. CXL 기술 현황"],
    "COMPETITOR": [r"### 3\.1\. 경쟁사별 기술 개발 방향", r"3\.1\. 경쟁사별 기술 개발 방향"],
    "LIMITATION": [r"### 4\.3\. 한계", r"4\.3\. 한계"],
}

SECTION_ORDER = ["SUMMARY", "HBM", "PIM", "CXL", "COMPETITOR", "LIMITATION"]


def read_report_text(report_path: Path) -> str:
    suffix = report_path.suffix.lower()

    if suffix == ".pdf":
        reader = PdfReader(str(report_path))
        texts = [(page.extract_text() or "") for page in reader.pages]
        return "\n".join(texts)

    if suffix in {".md", ".markdown", ".txt"}:
        return report_path.read_text(encoding="utf-8")

    raise ValueError(f"Unsupported report format: {report_path.suffix}")


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def find_heading_position(text: str, patterns: list[str]) -> int | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return match.start()
    return None


def extract_sections(text: str) -> dict[str, str]:
    text = normalize_text(text)
    positions = []

    for name in SECTION_ORDER:
        pos = find_heading_position(text, SECTION_PATTERNS[name])
        if pos is not None:
            positions.append((pos, name))

    positions.sort()
    sections = {}

    for idx, (start, name) in enumerate(positions):
        end = positions[idx + 1][0] if idx + 1 < len(positions) else len(text)
        sections[name] = text[start:end].strip()

    return sections


def extract_pdf_references(text: str) -> list[str]:
    text = normalize_text(text)

    reference_start = None
    for pattern in [r"## REFERENCE", r"REFERENCE"]:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            reference_start = match.start()
            break

    if reference_start is None:
        return []

    ref_text = text[reference_start:]
    pdf_block_match = re.search(
        r"\[PDF\](.*?)(?:\n\[WEB\]|\Z)",
        ref_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not pdf_block_match:
        return []

    pdf_block = pdf_block_match.group(1)
    refs = []
    for line in pdf_block.splitlines():
        cleaned = line.strip(" -\t")
        if cleaned.lower().endswith(".pdf"):
            refs.append(cleaned)

    return refs


def build_queries(sections: dict[str, str]) -> list[dict]:
    queries = []

    if sections.get("SUMMARY"):
        queries.append({
            "name": "SUMMARY",
            "topic": None,
            "text": sections["SUMMARY"][:1200],
        })

    for topic in ["HBM", "PIM", "CXL"]:
        if sections.get(topic):
            queries.append({
                "name": topic,
                "topic": topic,
                "text": sections[topic][:1500],
            })

    if sections.get("COMPETITOR"):
        queries.append({
            "name": "COMPETITOR",
            "topic": None,
            "text": sections["COMPETITOR"][:1200],
        })

    if sections.get("LIMITATION"):
        queries.append({
            "name": "LIMITATION",
            "topic": None,
            "text": sections["LIMITATION"][:1000],
        })

    return queries


def build_ground_truth(pdf_refs: list[str]) -> tuple[dict[str, set[str]], set[str]]:
    by_topic: dict[str, set[str]] = defaultdict(set)
    all_refs = set()

    for ref in pdf_refs:
        tags = infer_doc_tags(ref)
        topic = tags.get("topic", "UNKNOWN")
        if topic != "UNKNOWN":
            by_topic[topic].add(ref)
        all_refs.add(ref)

    return dict(by_topic), all_refs


class BM25OnlyRetriever:
    def __init__(self, docs):
        self.docs = docs
        self.tokenized_corpus = [doc.page_content.split() for doc in docs]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def retrieve(self, query: str, topic: str | None = None, limit: int = 20):
        scores = self.bm25.get_scores(query.split())
        ranked = sorted(
            list(zip(self.docs, scores)),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for doc, _ in ranked:
            if topic and doc.metadata.get("topic") != topic:
                continue
            results.append(doc)
            if len(results) >= limit:
                break
        return results


def build_retriever(docs, mode: str):
    if mode == "bm25":
        return BM25OnlyRetriever(docs), "bm25"

    try:
        vectorstore = build_or_load_vectorstore()
        return HybridRetriever(vectorstore, docs), "hybrid"
    except Exception as e:
        print(f"[Evaluation] hybrid retriever unavailable, falling back to BM25 only: {e}")
        return BM25OnlyRetriever(docs), "bm25"


def rank_source_files(retriever, query: str, topic: str | None, limit: int, mode: str) -> list[str]:
    if mode == "hybrid":
        docs = retriever.retrieve(
            query=query,
            topic=topic,
            k_dense=max(limit, 8),
            k_sparse=max(limit, 8),
            limit=max(limit * 3, 12),
        )
    else:
        docs = retriever.retrieve(
            query=query,
            topic=topic,
            limit=max(limit * 3, 12),
        )

    ranked = []
    seen = set()
    for doc in docs:
        source_file = doc.metadata.get("source_file", "")
        if source_file and source_file not in seen:
            seen.add(source_file)
            ranked.append(source_file)
        if len(ranked) >= limit:
            break

    return ranked


def reciprocal_rank(ranked: list[str], relevant: set[str]) -> float:
    for idx, item in enumerate(ranked, start=1):
        if item in relevant:
            return 1.0 / idx
    return 0.0


def hit_at_k(ranked: list[str], relevant: set[str], k: int) -> float:
    return 1.0 if any(item in relevant for item in ranked[:k]) else 0.0


def evaluate_report(report_path: Path, ks: list[int], limit: int, mode: str) -> dict:
    report_text = read_report_text(report_path)
    sections = extract_sections(report_text)
    queries = build_queries(sections)
    pdf_refs = extract_pdf_references(report_text)
    refs_by_topic, all_refs = build_ground_truth(pdf_refs)

    docs = split_documents(load_pdf_documents(str(RAW_DOCS_DIR)))
    retriever, actual_mode = build_retriever(docs, mode)

    results = []
    aggregate_hits = {k: [] for k in ks}
    aggregate_rr = []

    for query_info in queries:
        topic = query_info["topic"]
        relevant = refs_by_topic.get(topic, set()) if topic else set(all_refs)
        if not relevant:
            continue

        ranked = rank_source_files(retriever, query_info["text"], topic, limit, actual_mode)
        rr = reciprocal_rank(ranked, relevant)
        aggregate_rr.append(rr)

        hit_scores = {}
        for k in ks:
            score = hit_at_k(ranked, relevant, k)
            hit_scores[k] = score
            aggregate_hits[k].append(score)

        results.append({
            "query_name": query_info["name"],
            "topic": topic,
            "relevant_sources": sorted(relevant),
            "ranked_sources": ranked,
            "reciprocal_rank": rr,
            "hit_rate": {str(k): hit_scores[k] for k in ks},
        })

    summary = {
        "report_path": str(report_path),
        "retriever_mode": actual_mode,
        "pdf_references": sorted(pdf_refs),
        "query_count": len(results),
        "hit_rate": {
            str(k): (sum(scores) / len(scores) if scores else 0.0)
            for k, scores in aggregate_hits.items()
        },
        "mrr": (sum(aggregate_rr) / len(aggregate_rr) if aggregate_rr else 0.0),
        "per_query": results,
    }
    return summary


def print_summary(summary: dict) -> None:
    print("\n=== Retrieval Evaluation Summary ===")
    print(f"Report: {summary['report_path']}")
    print(f"Retriever mode: {summary['retriever_mode']}")
    print(f"PDF references: {summary['pdf_references']}")
    print(f"Evaluated queries: {summary['query_count']}")
    for k, score in summary["hit_rate"].items():
        print(f"Hit Rate@{k}: {score:.4f}")
    print(f"MRR: {summary['mrr']:.4f}")

    print("\n=== Per Query ===")
    for item in summary["per_query"]:
        print(f"[{item['query_name']}]")
        print(f"  relevant: {item['relevant_sources']}")
        print(f"  ranked  : {item['ranked_sources']}")
        print(f"  RR      : {item['reciprocal_rank']:.4f}")
        print(f"  hits    : {item['hit_rate']}")


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate raw PDF retrieval quality against a final report using Hit Rate@K and MRR.",
    )
    parser.add_argument(
        "--report",
        required=True,
        help="Path to the final report file (.pdf, .md, or .txt).",
    )
    parser.add_argument(
        "--ks",
        default="1,3,5",
        help="Comma-separated K values for Hit Rate@K. Default: 1,3,5",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of ranked source files per query. Default: 10",
    )
    parser.add_argument(
        "--save-json",
        default="",
        help="Optional path to save the evaluation result as JSON.",
    )
    parser.add_argument(
        "--mode",
        choices=["hybrid", "bm25"],
        default="hybrid",
        help="Retriever mode. Defaults to hybrid and falls back to bm25 if unavailable.",
    )
    args = parser.parse_args()

    report_path = Path(args.report).resolve()
    ks = [int(k.strip()) for k in args.ks.split(",") if k.strip()]
    summary = evaluate_report(report_path=report_path, ks=ks, limit=args.limit, mode=args.mode)
    print_summary(summary)

    if args.save_json:
        out_path = Path(args.save_json).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\nSaved JSON: {out_path}")


if __name__ == "__main__":
    main()
