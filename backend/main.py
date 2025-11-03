from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
from dotenv import load_dotenv

from database.db import Database
from rag.indexer import Indexer
from rag.retriever import Retriever
from rag.generator import GeminiRAG
from connectors.bookmarks import BookmarkParser
from connectors.files import FileConnector

load_dotenv()

app = FastAPI(title="DevFlow API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db = Database()
indexer = Indexer()
retriever = Retriever()
rag = GeminiRAG()

class SearchQuery(BaseModel):
    query: str
    n_results: int = 5

class ManualDocument(BaseModel):
    title: str
    content: str
    url: Optional[str] = None

@app.get("/")
async def root():
    stats = db.get_stats()
    return {"status": "running", "message": "DevFlow API", "stats": stats}

@app.post("/api/search")
async def search(query: SearchQuery):
    try:
        results = retriever.search(query.query, query.n_results)
        if not results['documents']:
            return {
                "answer": "No relevant documents found.",
                "sources": [],
                "query": query.query
            }
        response = rag.generate_answer(
            query=query.query,
            context=results['documents'],
            sources=results['metadatas']
        )
        db.add_search(query.query, len(results['documents']))
        return {**response, "query": query.query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/index/manual")
async def add_manual_document(doc: ManualDocument):
    try:
        source_id = db.add_source("manual", None, doc.title)
        chunks, metadatas, ids = indexer.prepare_documents(
            [doc.content], [doc.title], [doc.url or f"manual_{source_id}"],
            source_id, "manual"
        )
        retriever.add_documents(chunks, metadatas, ids)
        db.update_source_status(source_id, "indexed")
        doc_id = indexer.generate_id(doc.content)
        db.add_document(doc_id, source_id, doc.title, doc.url)
        return {"success": True, "message": "Document added", "source_id": source_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sources")
async def get_sources():
    try:
        sources = db.get_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: int):
    try:
        retriever.delete_by_source(source_id)
        db.delete_source(source_id)
        return {"success": True, "message": "Source deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stats")
async def get_stats():
    try:
        stats = db.get_stats()
        stats['chromadb_count'] = retriever.count()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
