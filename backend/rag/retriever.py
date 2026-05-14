import os
from typing import List, Dict, Optional
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

    def search(
        self,
        query: str,
        n_results: int = 5,
        collection_source_ids: Optional[List[int]] = None,
        use_hyde: bool = False,
    ) -> Dict:
        count = self.collection.count()
        if count == 0:
            return {"documents": [], "metadatas": [], "distances": []}
        if collection_source_ids is not None and not collection_source_ids:
            return {"documents": [], "metadatas": [], "distances": []}

        query_embedding = self._hyde_embedding(query) if use_hyde else self.model.encode([query]).tolist()
        n = min(n_results, count)

        kwargs: Dict = dict(
            query_embeddings=query_embedding,
            n_results=n,
            include=["documents", "metadatas", "distances"],
        )
        if collection_source_ids is not None:
            kwargs["where"] = {"source_id": {"$in": collection_source_ids}}

        results = self.collection.query(**kwargs)
        return {
            "documents": results["documents"][0] if results["documents"] else [],
            "metadatas": results["metadatas"][0] if results["metadatas"] else [],
            "distances": results["distances"][0] if results["distances"] else [],
        }

    def get_chunks_by_source(self, source_id: int) -> List[Dict]:
        results = self.collection.get(
            where={"source_id": source_id},
            include=["documents", "metadatas"],
        )
        chunks = []
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
            chunks.append({
                "id": results["ids"][i],
                "text": doc,
                "chunk_index": meta.get("chunk_index", i),
                "total_chunks": meta.get("total_chunks", len(results["documents"])),
            })
        chunks.sort(key=lambda x: x["chunk_index"])
        return chunks

    def is_duplicate(self, text: str, threshold: float = 0.92) -> bool:
        """Return True if very similar content already exists (cosine similarity > threshold)."""
        if self.collection.count() == 0:
            return False
        try:
            embedding = self.model.encode([text]).tolist()
            results = self.collection.query(
                query_embeddings=embedding,
                n_results=1,
                include=["distances"],
            )
            if results["distances"] and results["distances"][0]:
                similarity = 1.0 - results["distances"][0][0]
                return similarity > threshold
        except Exception:
            pass
        return False

    def _hyde_embedding(self, query: str) -> List[List[float]]:
        """HyDE: average embeddings of the original query and an LLM-generated hypothetical answer."""
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv("GEMINI_API_KEY", ""),
                temperature=0.1,
                max_tokens=120,
            )
            hyp = llm.invoke(
                f"Write a concise technical answer (2-3 sentences) to: {query}"
            ).content.strip()
            orig_emb = self.model.encode([query])[0]
            hyp_emb = self.model.encode([hyp])[0]
            combined = ((orig_emb + hyp_emb) / 2).tolist()
            return [combined]
        except Exception:
            return self.model.encode([query]).tolist()

    def delete_by_source(self, source_id: int):
        results = self.collection.get(
            where={"source_id": source_id},
            include=["documents"],
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def count(self) -> int:
        return self.collection.count()
