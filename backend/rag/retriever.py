import os
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from rag.indexer import get_embedding_model

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# v2 collection uses multilingual-e5-base (768-dim)
# v1 "devflow_docs" used all-MiniLM-L6-v2 (384-dim) — kept for migration
COLLECTION_NAME = "devflow_docs_v2"
LEGACY_COLLECTION_NAME = "devflow_docs"


class Retriever:
    def __init__(self):
        self.client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
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

        if use_hyde:
            query_embedding = self._hyde_embedding(query)
        else:
            # multilingual-e5: queries must use "query: " prefix
            query_embedding = self.model.encode([f"query: {query}"]).tolist()

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
                "lang": meta.get("lang", "en"),
            })
        chunks.sort(key=lambda x: x["chunk_index"])
        return chunks

    def is_duplicate(self, text: str, threshold: float = 0.92) -> bool:
        if self.collection.count() == 0:
            return False
        try:
            embedding = self.model.encode([f"query: {text}"]).tolist()
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
        """HyDE: average embeddings of query and LLM-generated hypothetical answer.
        Hypothetical answer is generated in the detected query language."""
        from rag.lang import detect_language, lang_name
        lang = detect_language(query)
        lang_display = lang_name(lang)
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=os.getenv("GEMINI_API_KEY", ""),
                temperature=0.1,
                max_tokens=150,
            )
            prompt = (
                f"Write a concise technical answer (2-3 sentences) in {lang_display} to: {query}"
            )
            hyp = llm.invoke(prompt).content.strip()
            orig_emb = self.model.encode([f"query: {query}"])[0]
            hyp_emb = self.model.encode([f"passage: {hyp}"])[0]
            combined = ((orig_emb + hyp_emb) / 2).tolist()
            return [combined]
        except Exception:
            return self.model.encode([f"query: {query}"]).tolist()

    def delete_by_source(self, source_id: int):
        results = self.collection.get(
            where={"source_id": source_id},
            include=["documents"],
        )
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def count(self) -> int:
        return self.collection.count()

    def migrate_from_v1(self) -> int:
        """Re-embed all content from the legacy all-MiniLM collection into this one.
        Returns number of chunks migrated. Safe to call multiple times."""
        try:
            legacy = self.client.get_collection(LEGACY_COLLECTION_NAME)
        except Exception:
            return 0  # no legacy collection — nothing to migrate

        total = legacy.count()
        if total == 0:
            return 0

        # Fetch all docs from legacy collection
        results = legacy.get(include=["documents", "metadatas"])
        docs = results["documents"]
        metas = results["metadatas"]
        ids = results["ids"]

        if not docs:
            return 0

        # Clear v2 collection to avoid duplicates from partial previous migrations
        existing_ids = self.collection.get()["ids"]
        if existing_ids:
            self.collection.delete(ids=existing_ids)

        # Re-embed in batches with multilingual-e5 passage prefix
        batch_size = 64
        migrated = 0
        for i in range(0, len(docs), batch_size):
            batch_docs = docs[i:i + batch_size]
            batch_metas = metas[i:i + batch_size]
            batch_ids = ids[i:i + batch_size]

            prefixed = [f"passage: {doc}" for doc in batch_docs]
            new_embeddings = self.model.encode(
                prefixed, batch_size=32, show_progress_bar=False,
            ).tolist()

            # Add detected language to metadata if missing
            for meta in batch_metas:
                if "lang" not in meta:
                    meta["lang"] = "en"

            self.collection.add(
                documents=batch_docs,
                embeddings=new_embeddings,
                metadatas=batch_metas,
                ids=batch_ids,
            )
            migrated += len(batch_docs)

        return migrated
