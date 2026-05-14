from fastapi import APIRouter, HTTPException
from database.db import Database
from models.schemas import CollectionCreate

router = APIRouter(prefix="/api/collections", tags=["collections"])
db = Database()


@router.get("")
async def list_collections():
    return {"collections": db.get_collections()}


@router.post("")
async def create_collection(data: CollectionCreate):
    cid = db.create_collection(data.name, data.description)
    return {"success": True, "collection_id": cid}


@router.delete("/{collection_id}")
async def delete_collection(collection_id: int):
    db.delete_collection(collection_id)
    return {"success": True}


@router.post("/{collection_id}/sources/{source_id}")
async def add_source(collection_id: int, source_id: int):
    db.add_source_to_collection(source_id, collection_id)
    return {"success": True}


@router.delete("/{collection_id}/sources/{source_id}")
async def remove_source(collection_id: int, source_id: int):
    db.remove_source_from_collection(source_id, collection_id)
    return {"success": True}


@router.get("/{collection_id}/sources")
async def collection_sources(collection_id: int):
    return {"sources": db.get_sources(collection_id=collection_id)}
