import faiss
import numpy as np
from typing import List, Dict
import pickle
import os

class Retriever:
    def __init__(self, persist_directory: str = "./faiss_db"):
        self.persist_directory = persist_directory
        self.index_path = os.path.join(persist_directory, "index.faiss")
        self.metadata_path = os.path.join(persist_directory, "metadata.pkl")
        
        os.makedirs(persist_directory, exist_ok=True)
        
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(self.metadata_path, 'rb') as f:
                self.metadata = pickle.load(f)
        else:
            self.index = faiss.IndexFlatL2(384)
            self.metadata = []
    
    def add_documents(self, documents: List[str], metadatas: List[Dict], ids: List[str]):
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        embeddings = model.encode(documents)
        embeddings = np.array(embeddings).astype('float32')
        
        self.index.add(embeddings)
        
        for doc, meta, doc_id in zip(documents, metadatas, ids):
            self.metadata.append({**meta, "text": doc, "id": doc_id})
        
        faiss.write_index(self.index, self.index_path)
        with open(self.metadata_path, 'wb') as f:
            pickle.dump(self.metadata, f)
    
    def search(self, query: str, n_results: int = 5) -> Dict:
        if self.index.ntotal == 0:
            return {"documents": [], "metadatas": [], "distances": []}
        
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        query_embedding = model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        distances, indices = self.index.search(query_embedding, min(n_results, self.index.ntotal))
        
        documents = []
        metadatas = []
        for idx in indices[0]:
            if idx < len(self.metadata):
                meta = self.metadata[idx]
                documents.append(meta.get("text", ""))
                metadatas.append({k: v for k, v in meta.items() if k != "text"})
        
        return {
            "documents": documents,
            "metadatas": metadatas,
            "distances": distances[0].tolist()
        }
    
    def delete_by_source(self, source_id: int):
        new_metadata = [m for m in self.metadata if m.get("source_id") != source_id]
        if len(new_metadata) < len(self.metadata):
            self.metadata = new_metadata
            self.index = faiss.IndexFlatL2(384)
            if self.metadata:
                from sentence_transformers import SentenceTransformer
                model = SentenceTransformer('all-MiniLM-L6-v2')
                texts = [m["text"] for m in self.metadata]
                embeddings = model.encode(texts)
                embeddings = np.array(embeddings).astype('float32')
                self.index.add(embeddings)
            faiss.write_index(self.index, self.index_path)
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
    
    def count(self) -> int:
        return self.index.ntotal