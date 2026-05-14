from fastapi import APIRouter
from database.db import Database

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
db = Database()

_retriever = None


def _get_retriever():
    global _retriever
    if _retriever is None:
        from rag.retriever import Retriever
        _retriever = Retriever()
    return _retriever


@router.get("")
async def get_analytics():
    data = db.get_analytics()
    data["chromadb_count"] = _get_retriever().count()
    return data
