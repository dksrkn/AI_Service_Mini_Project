from typing import List
from sentence_transformers import SentenceTransformer
from langchain_core.embeddings import Embeddings
from app.config import EMBEDDING_MODEL_NAME


class E5EmbeddingWrapper(Embeddings):
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        passages = [f"passage: {t}" for t in texts]
        return self.model.encode(
            passages,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).tolist()

    def embed_query(self, text: str) -> List[float]:
        query = f"query: {text}"
        return self.model.encode(
            [query],
            normalize_embeddings=True,
            convert_to_numpy=True
        )[0].tolist()