from fastapi import APIRouter, Query
from database.db import Database

router = APIRouter(prefix="/api/history", tags=["history"])
db = Database()


@router.get("")
async def get_history(limit: int = Query(default=50, ge=1, le=200)):
    return {"history": db.get_search_history(limit)}
