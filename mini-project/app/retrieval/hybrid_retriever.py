from typing import List, Optional
from rank_bm25 import BM25Okapi
from langchain_core.documents import Document


class HybridRetriever:
    def __init__(self, vectorstore, docs: List[Document]):
        self.vectorstore = vectorstore
        self.docs = docs
        self.tokenized_corpus = [doc.page_content.split() for doc in docs]
        self.bm25 = BM25Okapi(self.tokenized_corpus)

    def retrieve(
        self,
        query: str,
        topic: Optional[str] = None,
        k_dense: int = 5,
        k_sparse: int = 5,
        limit: int = 5,
    ) -> List[Document]:
        dense_docs = self.vectorstore.max_marginal_relevance_search(
            query=query,
            k=k_dense,
            fetch_k=max(15, k_dense * 3),
        )

        sparse_scores = self.bm25.get_scores(query.split())
        sparse_ranked = sorted(
            list(zip(self.docs, sparse_scores)),
            key=lambda x: x[1],
            reverse=True
        )

        sparse_docs = []
        for doc, _ in sparse_ranked:
            if topic and doc.metadata.get("topic") != topic:
                continue
            sparse_docs.append(doc)
            if len(sparse_docs) >= k_sparse:
                break

        merged = []
        seen = set()

        for doc in dense_docs + sparse_docs:
            if topic and doc.metadata.get("topic") != topic:
                continue

            key = (
                doc.metadata.get("source_file", ""),
                doc.metadata.get("page", ""),
                doc.page_content[:200]
            )
            if key not in seen:
                seen.add(key)
                merged.append(doc)

            if len(merged) >= limit:
                break

        return merged