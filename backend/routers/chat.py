import json
import uuid
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from loguru import logger

from cache.redis_cache import get_redis
from models.schemas import ChatStreamRequest

router = APIRouter(prefix="/api/chat", tags=["chat"])

_db = None
_retriever = None
_reranker = None
_rag = None
_web_searcher = None


def _get_db():
    global _db
    if _db is None:
        from database.db import Database
        _db = Database()
    return _db


def _get_retriever():
    global _retriever
    if _retriever is None:
        from rag.retriever import Retriever
        _retriever = Retriever()
    return _retriever


def _get_reranker():
    global _reranker
    if _reranker is None:
        from rag.reranker import Reranker
        _reranker = Reranker()
    return _reranker


def _get_rag():
    global _rag
    if _rag is None:
        from rag.generator import GeminiRAG
        _rag = GeminiRAG()
    return _rag


def _get_web_searcher():
    global _web_searcher
    if _web_searcher is None:
        from connectors.web_search import WebSearcher
        _web_searcher = WebSearcher()
    return _web_searcher

HISTORY_TTL = 60 * 60 * 24  # 24h


def _get_history(session_id: str):
    client = get_redis()
    if not client:
        return []
    try:
        raw = client.get(f"devflow:chat:{session_id}")
        return json.loads(raw) if raw else []
    except Exception:
        return []


def _save_history(session_id: str, history: list):
    client = get_redis()
    if not client:
        return
    try:
        client.setex(f"devflow:chat:{session_id}", HISTORY_TTL, json.dumps(history))
    except Exception:
        pass


@router.post("/stream")
async def stream_chat(data: ChatStreamRequest):
    session_id = data.session_id
    history = _get_history(session_id)

    collection_source_ids = None
    if data.collection_id:
        sources = _get_db().get_sources(collection_id=data.collection_id)
        collection_source_ids = [s["id"] for s in sources]

    doc_results = _get_retriever().search(
        data.message,
        n_results=6,
        collection_source_ids=collection_source_ids,
        use_hyde=data.use_hyde,
    )
    documents = doc_results["documents"] or []
    metadatas = doc_results["metadatas"] or []

    if documents:
        documents, metadatas = _get_reranker().rerank(data.message, documents, metadatas, top_k=4)

    web_sources = []
    if data.use_web and len(documents) < 2:
        web_results = _get_web_searcher().search_and_scrape(data.message, count=2)
        web_sources = [r["content"] for r in web_results]
        web_meta = [{"title": r["title"], "url": r["url"], "source": "web"} for r in web_results]
        documents += web_sources
        metadatas += web_meta

    async def event_stream():
        full_answer = ""
        try:
            async for chunk in _get_rag().astream_answer(
                query=data.message,
                context=documents,
                sources=metadatas,
                history=history,
                model=data.model,
            ):
                full_answer += chunk
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"

            # Save updated history to Redis
            history.append({"role": "user", "content": data.message})
            history.append({"role": "assistant", "content": full_answer})
            _save_history(session_id, history[-20:])  # keep last 20 messages

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'chunk': f'Error: {str(e)}'})}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history/{session_id}")
async def get_session_history(session_id: str):
    return {"session_id": session_id, "messages": _get_history(session_id)}


@router.delete("/history/{session_id}")
async def clear_session_history(session_id: str):
    client = get_redis()
    if client:
        client.delete(f"devflow:chat:{session_id}")
    return {"success": True}


@router.get("/new-session")
async def new_session():
    return {"session_id": str(uuid.uuid4())}
