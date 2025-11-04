from typing import List, Dict

class Retriever:
    def __init__(self):
        # Simple in-memory storage (no vector DB)
        self.documents = []
        self.metadatas = []
        self.ids = []
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        self.documents.extend(documents)
        self.metadatas.extend(metadatas)
        self.ids.extend(ids)
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        # Simple keyword search (no semantic search for now)
        query_lower = query.lower()
        results = []
        
        for doc, meta in zip(self.documents, self.metadatas):
            if any(word in doc.lower() for word in query_lower.split()):
                results.append((doc, meta))
                if len(results) >= n_results:
                    break
        
        if not results:
            return {"documents": [], "metadatas": [], "distances": []}
        
        docs = [r[0] for r in results]
        metas = [r[1] for r in results]
        
        return {
            "documents": docs,
            "metadatas": metas,
            "distances": [0.0] * len(docs)
        }
    
    def delete_by_source(self, source_id: int):
        indices_to_remove = [i for i, m in enumerate(self.metadatas) if m.get("source_id") == source_id]
        for index in sorted(indices_to_remove, reverse=True):
            del self.documents[index]
            del self.metadatas[index]
            del self.ids[index]
    
    def count(self) -> int:
        return len(self.documents)
