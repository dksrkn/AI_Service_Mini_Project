from langchain_community.vectorstores import FAISS
from app.retrieval.embeddings import E5EmbeddingWrapper
from app.retrieval.document_loader import load_pdf_documents, split_documents
from app.config import RAW_DOCS_DIR, VECTORSTORE_DIR

REBUILD_VECTORSTORE = True


def build_or_load_vectorstore():
    embeddings = E5EmbeddingWrapper()
    index_path = VECTORSTORE_DIR / "faiss_index"

    if index_path.exists() and not REBUILD_VECTORSTORE:
        return FAISS.load_local(
            str(index_path),
            embeddings,
            allow_dangerous_deserialization=True
        )

    docs = load_pdf_documents(str(RAW_DOCS_DIR))
    split_docs = split_documents(docs)

    vectorstore = FAISS.from_documents(split_docs, embeddings)
    vectorstore.save_local(str(index_path))
    return vectorstore