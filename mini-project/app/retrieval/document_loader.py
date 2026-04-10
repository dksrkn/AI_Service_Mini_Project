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

    # -------------------------
    # PIM
    # -------------------------
    # 기존 PIM foundation
    if "2012.03112" in lower_name:
        return {
            "topic": "PIM",
            "doc_role": "technical_foundation",
            "load": True,
        }

    if lower_name == "pim.pdf":
        return {
            "topic": "PIM",
            "doc_role": "technical_foundation",
            "load": True,
        }

    # 새로 추가한 PIM benchmark
    if "2105.03814" in lower_name:
        return {
            "topic": "PIM",
            "doc_role": "benchmark",
            "load": True,
        }

    # 새로 추가한 PIM application / proposal
    if "2310.09385" in lower_name:
        return {
            "topic": "PIM",
            "doc_role": "application",
            "load": True,
        }

    # -------------------------
    # CXL
    # -------------------------
    if "2306.11227" in lower_name:
        return {
            "topic": "CXL",
            "doc_role": "technical_foundation",
            "load": True,
        }

    if "2412.20249" in lower_name:
        return {
            "topic": "CXL",
            "doc_role": "recent_survey",
            "load": True,
        }

    if lower_name == "cxl.pdf" or lower_name == "cxl(1).pdf":
        return {
            "topic": "CXL",
            "doc_role": "technical_foundation",
            "load": True,
        }

    if "jesd325" in lower_name:
        return {
            "topic": "CXL",
            "doc_role": "technical_foundation",
            "load": True,
        }

    # -------------------------
    # HBM
    # -------------------------
    if "comparative study of thermal dissipation" in lower_name:
        return {
            "topic": "HBM",
            "doc_role": "limitation_thermal",
            "load": True,
        }

    if "thermal" in lower_name:
        return {
            "topic": "HBM",
            "doc_role": "limitation_thermal",
            "load": True,
        }

    if lower_name == "hbm.pdf":
        return {
            "topic": "HBM",
            "doc_role": "technical_foundation",
            "load": True,
        }

    # -------------------------
    # 제외할 문서 (노이즈)
    # -------------------------
    if "jep166" in lower_name or "jepsamsung" in lower_name or "jepsk" in lower_name:
        return {
            "topic": "UNKNOWN",
            "doc_role": "noise",
            "load": False,
        }

    if "jep30" in lower_name or "jep30-e100i" in lower_name:
        return {
            "topic": "UNKNOWN",
            "doc_role": "noise",
            "load": False,
        }

    if "jep148" in lower_name:
        return {
            "topic": "UNKNOWN",
            "doc_role": "noise",
            "load": False,
        }

    return {
        "topic": "UNKNOWN",
        "doc_role": "general",
        "load": False,
    }


def load_pdf_documents(folder: str) -> list[Document]:
    folder_path = Path(folder)
    docs: list[Document] = []

    pdf_files = list(folder_path.glob("*.pdf"))
    print(f"[Document Loader] found pdf files = {[p.name for p in pdf_files]}")

    for path in pdf_files:
        tags = infer_doc_tags(path.name)

        if not tags.get("load", False):
            print(
                f"[Document Loader] file={path.name} "
                f"-> skipped (topic={tags['topic']}, role={tags['doc_role']})"
            )
            continue

        loader = PyPDFLoader(str(path))
        loaded_docs = loader.load()

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

        # 설명형 / survey / benchmark / application 문서는 조금 크게 자름
        if role in {"technical_foundation", "recent_survey", "benchmark", "application"}:
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