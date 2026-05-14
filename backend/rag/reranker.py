from typing import List, Dict, Tuple
from sentence_transformers import CrossEncoder

_model: CrossEncoder = None


def get_reranker() -> CrossEncoder:
    global _model
    if _model is None:
        # Multilingual cross-encoder: 100 languages, MMARCO-trained
        _model = CrossEncoder("cross-encoder/mmarco-mMiniLMv2-L12-H384-v1")
    return _model


class Reranker:
    def __init__(self):
        self.model = get_reranker()

    def rerank(
        self,
        query: str,
        documents: List[str],
        metadatas: List[Dict],
        top_k: int = 5,
    ) -> Tuple[List[str], List[Dict]]:
        if not documents:
            return documents, metadatas

        pairs = [(query, doc) for doc in documents]
        scores = self.model.predict(pairs)

        ranked = sorted(zip(scores, documents, metadatas), reverse=True)[:top_k]
        return [d for _, d, _ in ranked], [m for _, _, m in ranked]
