from sentence_transformers import SentenceTransformer
from typing import List, Dict
import hashlib

class Indexer:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        return chunks
    
    def generate_id(self, text: str, prefix: str = "doc") -> str:
        hash_obj = hashlib.md5(text.encode())
        return f"{prefix}_{hash_obj.hexdigest()[:16]}"
    
    def prepare_documents(self, texts: List[str], titles: List[str], urls: List[str], 
                         source_id: int, source_type: str) -> tuple:
        all_chunks = []
        all_metadatas = []
        all_ids = []
        
        for text, title, url in zip(texts, titles, urls):
            chunks = self.chunk_text(text)
            for i, chunk in enumerate(chunks):
                chunk_id = self.generate_id(f"{url}_{i}")
                all_chunks.append(chunk)
                all_ids.append(chunk_id)
                all_metadatas.append({
                    "title": title,
                    "url": url or "",
                    "source_id": source_id,
                    "source_type": source_type,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                })
        return all_chunks, all_metadatas, all_ids
