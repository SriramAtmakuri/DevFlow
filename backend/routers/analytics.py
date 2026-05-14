from fastapi import APIRouter
from database.db import Database
from rag.retriever import Retriever

router = APIRouter(prefix="/api/analytics", tags=["analytics"])
db = Database()


@router.get("")
async def get_analytics():
    data = db.get_analytics()
    data["chromadb_count"] = Retriever().count()
    return data
