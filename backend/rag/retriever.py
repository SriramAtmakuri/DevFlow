from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from typing import List, Dict
import uuid

class Retriever:
    def __init__(self):
        # Use in-memory Qdrant (no external service needed)
        self.client = QdrantClient(":memory:")
        self.collection_name = "devflow_documents"
        
        # Create collection (384 dimensions for all-MiniLM-L6-v2)
        try:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
        except:
            pass  # Collection already exists
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate embeddings
        embeddings = model.encode(documents)
        
        # Create points
        points = []
        for i, (doc, metadata, doc_id) in enumerate(zip(documents, metadatas, ids)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=embeddings[i].tolist(),
                payload={**metadata, "text": doc}
            ))
        
        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate query embedding
        query_embedding = model.encode(query).tolist()
        
        # Search
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=n_results
        )
        
        if not results:
            return {"documents": [], "metadatas": [], "distances": []}
        
        documents = [r.payload.get("text", "") for r in results]
        metadatas = [{k: v for k, v in r.payload.items() if k != "text"} for r in results]
        distances = [r.score for r in results]
        
        return {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances
        }
    
    def delete_by_source(self, source_id: int):
        # Delete all points with matching source_id
        self.client.delete(
            collection_name=self.collection_name,
            points_selector={
                "filter": {
                    "must": [
                        {"key": "source_id", "match": {"value": source_id}}
                    ]
                }
            }
        )
    
    def count(self) -> int:
        info = self.client.get_collection(collection_name=self.collection_name)
        return info.points_count