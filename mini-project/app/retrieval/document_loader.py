from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def infer_doc_tags(filename: str) -> dict:
    """
    파일명 기반으로 topic / doc_role 자동 판별
    파일명에 (1) 등이 붙어도 부분 문자열로 매칭되도록 처리
    """
    lower_name = filename.lower()

    # PIM
    if "2012.03112" in lower_name:
        return {
            "topic": "PIM",
            "doc_role": "technical_foundation",
        }

    # CXL
    if "2306.11227" in lower_name:
        return {
            "topic": "CXL",
            "doc_role": "technical_foundation",
        }

    if "2412.20249" in lower_name:
        return {
            "topic": "CXL",
            "doc_role": "recent_survey",
        }

    # HBM
    if "comparative study of thermal dissipation" in lower_name:
        return {
            "topic": "HBM",
            "doc_role": "limitation_thermal",
        }

    if "thermal" in lower_name:
        return {
            "topic": "HBM",
            "doc_role": "limitation_thermal",
        }

    if "hbm" in lower_name:
        return {
            "topic": "HBM",
            "doc_role": "technical_foundation",
        }

    return {
        "topic": "UNKNOWN",
        "doc_role": "general",
    }


def load_pdf_documents(folder: str) -> list[Document]:
    folder_path = Path(folder)
    docs: list[Document] = []

    pdf_files = list(folder_path.glob("*.pdf"))
    print(f"[Document Loader] found pdf files = {[p.name for p in pdf_files]}")

    for path in pdf_files:
        loader = PyPDFLoader(str(path))
        loaded_docs = loader.load()

        tags = infer_doc_tags(path.name)
        print(
            f"[Document Loader] file={path.name} "
            f"-> topic={tags['topic']}, role={tags['doc_role']}, pages={len(loaded_docs)}"
        )

        for doc in loaded_docs:
            doc.metadata["source_file"] = path.name
            doc.metadata["topic"] = tags["topic"]
            doc.metadata["doc_role"] = tags["doc_role"]

        docs.extend(loaded_docs)

    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    split_docs: list[Document] = []

    survey_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )
    experiment_splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=100,
    )

    for doc in docs:
        role = doc.metadata.get("doc_role", "general")

        if role in {"technical_foundation", "recent_survey"}:
            chunks = survey_splitter.split_documents([doc])
        else:
            chunks = experiment_splitter.split_documents([doc])

        for chunk in chunks:
            chunk.metadata["source_file"] = doc.metadata.get("source_file", "unknown")
            chunk.metadata["topic"] = doc.metadata.get("topic", "UNKNOWN")
            chunk.metadata["doc_role"] = doc.metadata.get("doc_role", "general")

        split_docs.extend(chunks)

    print(f"[Document Loader] total split chunks = {len(split_docs)}")
    return split_docs