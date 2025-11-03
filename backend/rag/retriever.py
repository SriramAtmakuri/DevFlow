import chromadb
from chromadb.config import Settings
from typing import List, Dict

class Retriever:
    def __init__(self, persist_directory: str = "./chroma_db"):
        self.client = chromadb.Client(Settings(
            persist_directory=persist_directory,
            anonymized_telemetry=False
        ))
        self.collection = self.client.get_or_create_collection(
            name="devflow_documents",
            metadata={"hnsw:space": "cosine"}
        )
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        self.collection.add(documents=documents, metadatas=metadatas, ids=ids)
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        results = self.collection.query(query_texts=[query], n_results=n_results)
        if not results['documents'][0]:
            return {"documents": [], "metadatas": [], "distances": []}
        return {
            "documents": results['documents'][0],
            "metadatas": results['metadatas'][0],
            "distances": results['distances'][0]
        }
    
    def delete_by_source(self, source_id: int):
        results = self.collection.get(where={"source_id": source_id})
        if results['ids']:
            self.collection.delete(ids=results['ids'])
    
    def count(self) -> int:
        return self.collection.count()