from typing import List, Dict, Tuple
import hashlib
from sentence_transformers import SentenceTransformer
from rag.lang import detect_language

_model: SentenceTransformer = None


def get_embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        # multilingual-e5-base: 94 languages, 768-dim
        # Requires "query: " prefix for queries, "passage: " prefix for documents
        _model = SentenceTransformer("intfloat/multilingual-e5-base")
    return _model


class Indexer:
    def __init__(self):
        self.model = get_embedding_model()

    def chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        i = 0
        while i < len(words):
            chunk = " ".join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
            i += chunk_size - overlap
        return chunks

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, batch_size=32, show_progress_bar=False)
        return embeddings.tolist()

    def generate_id(self, text: str, prefix: str = "doc") -> str:
        return f"{prefix}_{hashlib.md5(text.encode()).hexdigest()[:16]}"

    def prepare_documents(
        self,
        texts: List[str],
        titles: List[str],
        urls: List[str],
        source_id: int,
        source_type: str,
    ) -> Tuple[List[str], List[List[float]], List[Dict], List[str]]:
        all_chunks: List[str] = []
        all_embeddings: List[List[float]] = []
        all_metadatas: List[Dict] = []
        all_ids: List[str] = []

        for text, title, url in zip(texts, titles, urls):
            chunks = self.chunk_text(text)
            if not chunks:
                continue

            lang = detect_language(text)

            # multilingual-e5: passages must use "passage: " prefix for best quality.
            # Raw chunk text is stored; prefixed version is only used for embedding generation.
            prefixed = [f"passage: {chunk}" for chunk in chunks]
            embeddings = self.generate_embeddings(prefixed)

            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                chunk_id = self.generate_id(f"{url}_{i}")
                all_chunks.append(chunk)
                all_embeddings.append(embedding)
                all_ids.append(chunk_id)
                all_metadatas.append({
                    "title": title,
                    "url": url or "",
                    "source_id": source_id,
                    "source_type": source_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "lang": lang,
                })

        return all_chunks, all_embeddings, all_metadatas, all_ids
