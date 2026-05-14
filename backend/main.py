import os
import sys
import uuid
from dotenv import load_dotenv

load_dotenv()

# ── Sentry (init before anything else) ───────────────────────────────────────

_SENTRY_DSN = os.getenv("SENTRY_DSN")
if _SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
    sentry_sdk.init(
        dsn=_SENTRY_DSN,
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
        ],
        traces_sample_rate=0.1,
        environment=os.getenv("ENVIRONMENT", "production"),
        release=os.getenv("RENDER_GIT_COMMIT", "dev"),
    )

from fastapi import FastAPI, HTTPException, UploadFile, File, Request, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from jose import JWTError, jwt

from database.db import Database
from rag.indexer import Indexer
from rag.retriever import Retriever
from rag.reranker import Reranker
from rag.generator import GeminiRAG
from connectors.web_search import WebSearcher
from connectors.file_upload import FileProcessor, validate_upload
from models.schemas import (
    SearchRequest, HybridSearchRequest, ManualDocumentRequest,
    SaveWebResultRequest, IndexResponse, UploadResponse,
    StatsResponse, UserRegisterRequest, UserLoginRequest, TokenResponse,
    JobStatusResponse, UrlIndexRequest, BulkDeleteRequest,
)
from auth.auth import init_users_table, register_user, authenticate_user, create_access_token, revoke_token, SECRET_KEY, ALGORITHM
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cache.redis_cache import make_cache_key, get_cached, set_cached
from rag.lang import detect_language
from graphql_schema import graphql_router
from routers import chat, history, analytics, collections
from middleware.request_id import RequestIDMiddleware

_bearer = HTTPBearer(auto_error=False)

# ── Logging ───────────────────────────────────────────────────────────────────

os.makedirs("logs", exist_ok=True)
logger.remove()
logger.configure(patcher=lambda record: record["extra"].setdefault("request_id", "-"))
logger.add(
    sys.stdout,
    format="{time:HH:mm:ss} | {level:<8} | {extra[request_id]:<12} | {message}",
    level="INFO",
    colorize=True,
)
logger.add(
    "logs/app.log",
    rotation="50 MB",
    retention="14 days",
    level="INFO",
    serialize=True,
)

# ── Per-user rate limiter ─────────────────────────────────────────────────────

def _rate_key(request: Request) -> str:
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            payload = jwt.decode(auth[7:], SECRET_KEY, algorithms=[ALGORITHM])
            uid = payload.get("sub")
            if uid:
                return f"user:{uid}"
        except (JWTError, Exception):
            pass
    return get_remote_address(request)

limiter = Limiter(key_func=_rate_key, default_limits=["200/minute"])

# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="DevFlow API",
    version="2.2.0",
    description="Production RAG knowledge base with streaming, multi-model, reranking",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)

_allowed_origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(graphql_router, prefix="/graphql")
app.include_router(chat.router)
app.include_router(history.router)
app.include_router(analytics.router)
app.include_router(collections.router)

# ── Services ──────────────────────────────────────────────────────────────────

db = Database()
indexer = Indexer()
retriever = Retriever()
reranker = Reranker()
rag = GeminiRAG()
web_searcher = WebSearcher()

init_users_table()
logger.info("DevFlow API v2.2.0 started")

# ── S3 helper (optional) ──────────────────────────────────────────────────────

async def _maybe_store_s3(filename: str, file_bytes: bytes) -> None:
    bucket = os.getenv("AWS_S3_BUCKET")
    if not bucket:
        return
    try:
        import boto3
        s3 = boto3.client("s3", region_name=os.getenv("AWS_S3_REGION", "us-east-1"))
        key = f"uploads/{uuid.uuid4().hex[:8]}/{filename}"
        s3.put_object(Bucket=bucket, Key=key, Body=file_bytes, ContentType="application/octet-stream")
        logger.info(f"Stored {filename} to s3://{bucket}/{key}")
    except Exception as e:
        logger.warning(f"S3 upload skipped (non-critical): {e}")

# ── Background jobs ───────────────────────────────────────────────────────────

def _index_file_task(job_id: str, filename: str, file_bytes: bytes):
    try:
        text_content, _ = FileProcessor.process_file(filename, file_bytes)
        if not text_content or len(text_content.strip()) < 10:
            db.update_job(job_id, "failed", error="Could not extract text")
            return
        source_id = db.add_source("file", filename, filename)
        chunks, embeddings, metadatas, ids = indexer.prepare_documents(
            [text_content], [filename], [filename], source_id, "file",
        )
        retriever.add_documents(chunks, embeddings, metadatas, ids)
        db.update_source_status(source_id, "indexed")
        db.add_document(indexer.generate_id(text_content), source_id, filename, filename)
        db.update_job(job_id, "completed", chunks=len(chunks))
        logger.info(f"Job {job_id}: indexed {filename} → {len(chunks)} chunks")
    except Exception as e:
        db.update_job(job_id, "failed", error=str(e))
        logger.error(f"Job {job_id} failed: {e}")


def _index_url_task(job_id: str, url: str, title: str, collection_id: int = None):
    try:
        result = web_searcher.scrape_url(url)
        content = result.get("content", "")
        page_title = title or result.get("title", url)

        if not content or len(content.strip()) < 50:
            db.update_job(job_id, "failed", error="Could not extract content from URL")
            return

        sample = " ".join(content.split()[:200])
        if retriever.is_duplicate(sample):
            db.update_job(job_id, "failed", error="Similar content already exists in your knowledge base")
            return

        source_id = db.add_source("web", url, page_title)
        chunks, embeddings, metadatas, ids = indexer.prepare_documents(
            [content], [page_title], [url], source_id, "web",
        )
        retriever.add_documents(chunks, embeddings, metadatas, ids)
        db.update_source_status(source_id, "indexed")
        db.add_document(indexer.generate_id(content), source_id, page_title, url)
        if collection_id:
            db.add_source_to_collection(source_id, collection_id)
        db.update_job(job_id, "completed", chunks=len(chunks))
        logger.info(f"Job {job_id}: indexed URL {url} → {len(chunks)} chunks")
    except Exception as e:
        db.update_job(job_id, "failed", error=str(e))
        logger.error(f"Job {job_id} URL index failed: {e}")


# ── Auth ──────────────────────────────────────────────────────────────────────

@app.post("/api/auth/register", response_model=TokenResponse)
@limiter.limit("5/minute")
async def register(request: Request, data: UserRegisterRequest):
    user = register_user(data.email, data.username, data.password)
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return TokenResponse(access_token=token, user_id=user["id"], username=user["username"])


@app.post("/api/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, data: UserLoginRequest):
    user = authenticate_user(data.email, data.password)
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
    return TokenResponse(access_token=token, user_id=user["id"], username=user["username"])


@app.post("/api/auth/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(_bearer)):
    if credentials:
        revoke_token(credentials.credentials)
    return {"success": True}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    checks: dict = {}

    try:
        db.get_stats()
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {type(e).__name__}"

    from cache.redis_cache import get_redis
    try:
        r = get_redis()
        checks["redis"] = "ok" if r else "unavailable"
    except Exception:
        checks["redis"] = "unavailable"

    try:
        retriever.count()
        checks["chromadb"] = "ok"
    except Exception as e:
        checks["chromadb"] = f"error: {type(e).__name__}"

    is_healthy = checks["database"] == "ok"
    return JSONResponse(
        status_code=200 if is_healthy else 503,
        content={"status": "ok" if is_healthy else "degraded", "checks": checks, "version": "2.2.0"},
    )


@app.get("/")
async def root():
    return {"status": "running", "version": "2.2.0", "stats": db.get_stats()}


# ── Search ────────────────────────────────────────────────────────────────────

@app.post("/api/search")
@limiter.limit("30/minute")
async def search(request: Request, data: SearchRequest):
    cache_key = make_cache_key("search", {"q": data.query, "n": data.n_results, "m": data.model, "lang": detect_language(data.query), "hyde": data.use_hyde, "rerank": data.rerank})
    cached = get_cached(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    results = retriever.search(data.query, data.n_results, use_hyde=data.use_hyde)
    documents, metadatas = results["documents"] or [], results["metadatas"] or []

    if documents and data.rerank:
        documents, metadatas = reranker.rerank(data.query, documents, metadatas)

    if not documents:
        return {"answer": "No relevant documents found.", "sources": [], "query": data.query, "cached": False}

    response = rag.generate_answer(query=data.query, context=documents, sources=metadatas, model=data.model)
    response.update({"query": data.query, "cached": False})
    db.add_search(data.query, len(documents), cached=False, model=data.model)
    set_cached(cache_key, response)
    logger.info(f"Search: '{data.query[:60]}' → {len(documents)} docs, model={data.model}")
    return response


@app.post("/api/search/hybrid")
@limiter.limit("30/minute")
async def hybrid_search(request: Request, data: HybridSearchRequest):
    cache_key = make_cache_key("hybrid", {"q": data.query, "web": data.use_web, "m": data.model, "lang": detect_language(data.query), "hyde": data.use_hyde, "rerank": data.rerank})
    cached = get_cached(cache_key)
    if cached:
        cached["cached"] = True
        return cached

    doc_results = retriever.search(data.query, data.n_results, use_hyde=data.use_hyde)
    documents = doc_results["documents"] or []
    metadatas = doc_results["metadatas"] or []

    if documents and data.rerank:
        documents, metadatas = reranker.rerank(data.query, documents, metadatas)

    web_sources, web_results = [], []
    if data.use_web and len(documents) < 2:
        web_results = web_searcher.search_and_scrape(data.query, count=3)
        web_sources = [r["content"] for r in web_results]

    all_sources = documents + web_sources
    if not all_sources:
        return {"answer": "No relevant information found.", "doc_sources": [], "web_sources": [],
                "query": data.query, "cached": False}

    web_meta = [{"title": r["title"], "url": r["url"], "source": "web"} for r in web_results]
    response = rag.generate_answer(
        query=data.query, context=all_sources, sources=metadatas + web_meta, model=data.model,
    )
    response.update({
        "doc_sources": metadatas, "web_sources": web_meta,
        "web_results_full": web_results, "query": data.query, "cached": False,
    })
    db.add_search(data.query, len(all_sources), cached=False, model=data.model)
    set_cached(cache_key, response)
    return response


# ── Sources ───────────────────────────────────────────────────────────────────

@app.post("/api/index/manual", response_model=IndexResponse)
async def add_manual_document(data: ManualDocumentRequest):
    source_id = db.add_source("manual", None, data.title)
    chunks, embeddings, metadatas, ids = indexer.prepare_documents(
        [data.content], [data.title], [data.url or f"manual_{source_id}"], source_id, "manual",
    )
    retriever.add_documents(chunks, embeddings, metadatas, ids)
    db.update_source_status(source_id, "indexed")
    db.add_document(indexer.generate_id(data.content), source_id, data.title, data.url)
    if data.collection_id:
        db.add_source_to_collection(source_id, data.collection_id)
    return IndexResponse(success=True, message="Document added", source_id=source_id)


@app.get("/api/sources")
async def get_sources(collection_id: int = None, limit: int = 50, offset: int = 0):
    return {"sources": db.get_sources(collection_id=collection_id, limit=limit, offset=offset)}


@app.delete("/api/sources/{source_id}")
async def delete_source(source_id: int):
    retriever.delete_by_source(source_id)
    db.delete_source(source_id)
    return {"success": True}


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    stats = db.get_stats()
    stats["chromadb_count"] = retriever.count()
    return stats


@app.post("/api/upload", response_model=UploadResponse)
@limiter.limit("10/minute")
async def upload_file(request: Request, background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    file_bytes = await file.read()
    try:
        validate_upload(file.filename or "", file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    job_id = str(uuid.uuid4())
    db.create_job(job_id, file.filename)
    background_tasks.add_task(_index_file_task, job_id, file.filename, file_bytes)
    background_tasks.add_task(_maybe_store_s3, file.filename, file_bytes)
    logger.info(f"Upload queued: {file.filename} → job {job_id}")
    return UploadResponse(success=True, message=f"Upload queued: {file.filename}", job_id=job_id)


@app.get("/api/upload/status/{job_id}", response_model=JobStatusResponse)
async def upload_status(job_id: str):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=job_id, status=job["status"], filename=job["filename"],
        chunks=job["chunks"], error=job.get("error"),
    )


@app.post("/api/index/url", response_model=UploadResponse)
@limiter.limit("10/minute")
async def index_url(request: Request, data: UrlIndexRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    db.create_job(job_id, data.url)
    background_tasks.add_task(_index_url_task, job_id, data.url, data.title or "", data.collection_id)
    logger.info(f"URL index queued: {data.url} → job {job_id}")
    return UploadResponse(success=True, message=f"URL queued: {data.url}", job_id=job_id)


def _reindex_all_task(job_id: str):
    try:
        migrated = retriever.migrate_from_v1()
        db.update_job(job_id, "completed", chunks=migrated)
        logger.info(f"Reindex-all job {job_id}: migrated {migrated} chunks")
    except Exception as e:
        db.update_job(job_id, "failed", error=str(e))
        logger.error(f"Reindex-all job {job_id} failed: {e}")


@app.post("/api/admin/reindex-all", response_model=UploadResponse)
async def reindex_all(background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    db.create_job(job_id, "reindex-all")
    background_tasks.add_task(_reindex_all_task, job_id)
    logger.info(f"Reindex-all queued → job {job_id}")
    return UploadResponse(success=True, message="Reindexing started", job_id=job_id)


@app.post("/api/sources/bulk-delete")
async def bulk_delete_sources(data: BulkDeleteRequest):
    for sid in data.ids:
        retriever.delete_by_source(sid)
        db.delete_source(sid)
    return {"success": True, "deleted": len(data.ids)}


@app.get("/api/sources/{source_id}/chunks")
async def get_source_chunks(source_id: int):
    chunks = retriever.get_chunks_by_source(source_id)
    return {"source_id": source_id, "chunks": chunks, "total": len(chunks)}


@app.post("/api/save-web-result", response_model=IndexResponse)
async def save_web_result(data: SaveWebResultRequest):
    source_id = db.add_source("web", data.url, data.title)
    chunks, embeddings, metadatas, ids = indexer.prepare_documents(
        [data.content], [data.title], [data.url], source_id, "web",
    )
    retriever.add_documents(chunks, embeddings, metadatas, ids)
    db.update_source_status(source_id, "indexed")
    db.add_document(indexer.generate_id(data.content), source_id, data.title, data.url)
    return IndexResponse(success=True, message=f"Saved '{data.title}'", source_id=source_id)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
