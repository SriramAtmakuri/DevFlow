import os
from typing import List, Dict
import chromadb
from chromadb.config import Settings
from rag.indexer import get_embedding_model

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name="devflow_docs",
            metadata={"hnsw:space": "cosine"},
        )
        self.model = get_embedding_model()

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict],
        ids: List[str],
    ):
        if not documents:
            return
        existing = set(self.collection.get(ids=ids)["ids"])
        new_idx = [i for i, id_ in enumerate(ids) if id_ not in existing]
        if not new_idx:
            return
        self.collection.add(
            documents=[documents[i] for i in new_idx],
            embeddings=[embeddings[i] for i in new_idx],
            metadatas=[metadatas[i] for i in new_idx],
            ids=[ids[i] for i in new_idx],
        )

    def search(self, query: str, n_results: int = 5) -> Dict:
        count = self.collection.count()
        if count == 0:
            return {"documents": [], "metadatas": [], "distances": []}
        query_embedding = self.model.encode([query]).tolist()
        n = min(n_results, count)
        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def delete_by_source(self, source_id: int):
        results = self.collection.get(
            where={"source_id": source_id},
            include=["documents"],
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def count(self) -> int:
        return self.collection.count()
