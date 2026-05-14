# DevFlow

A production-grade, full-stack RAG platform for developers. Index documents, PDFs, and web pages — then query them in any of 94+ languages with streaming LLM responses, multilingual semantic search, cross-encoder reranking, HyDE retrieval, and a hybrid knowledge base + live web pipeline. Ships with PostgreSQL, Redis, Alembic migrations, JWT auth, Sentry observability, S3 storage, a custom Go scraper microservice, GraphQL + REST APIs, and a Next.js frontend — all containerised and CI-tested.

## Features

### RAG & Search
- **Multilingual semantic search** — query and index documents in 94+ languages; responses always match the query language
- **HyDE retrieval** — averages embeddings of the query and an LLM-generated hypothetical answer for improved recall
- **Cross-encoder reranking** — multilingual reranker rescores retrieved chunks before generation
- **Hybrid search** — queries knowledge base first, falls back to live web results when coverage is low
- **Language-aware caching** — cache keys include detected language so Spanish and English queries never collide
- **Streaming chat** — SSE stream with per-session conversation memory (last 20 messages, 24h TTL), model selection, and collection scoping
- **Multi-model LLM** — Gemini 1.5 Flash/Pro, Claude Haiku, GPT-4o Mini; swap per request

### Ingestion
- **File upload** — PDF, DOCX, TXT up to 10 MB; magic byte validation ensures content matches extension; background job with poll-for-status
- **URL indexing** — scrape and index any URL with semantic deduplication (cosine similarity threshold 0.92)
- **Manual documents** — add content directly via API
- **Web result save** — save a hybrid search result directly into the knowledge base
- **Collections** — organise sources into named workspaces; sources can belong to multiple collections
- **Bulk delete** — remove multiple sources in one call
- **Source inspection** — view individual indexed chunks per source

### Infrastructure
- **PostgreSQL** primary database (SQLAlchemy + Alembic migrations); SQLite for local dev
- **ChromaDB** persistent vector store (`devflow_docs_v2`, cosine similarity, 768-dim)
- **Redis** caching (1h TTL, configurable) + JWT revocation blocklist + chat session history
- **Per-user rate limiting** — JWT sub extracted from Bearer token, falls back to IP
- **Request ID middleware** — UUID trace per request, `X-Request-ID` response header, ms timing in logs
- **Structured logging** — Loguru with JSON rotation (50 MB, 14-day retention), request ID in every line
- **Sentry observability** — full-stack: FastAPI + SQLAlchemy integrations on the backend, `@sentry/nextjs` on the frontend; 10% trace sampling
- **Health endpoint** — checks DB, Redis, and ChromaDB; returns 503 if database is down
- **GZip compression** on all responses
- **Optional S3 backup** — uploaded files mirrored to S3 when `AWS_S3_BUCKET` is set
- **GraphQL API** with GraphiQL explorer alongside REST
- **Search history auto-pruning** — database capped at 5000 most recent entries
- **Go web scraper** — purpose-built concurrent scraping microservice (up to 20 URLs/request, goroutine-per-URL, 10s timeout, 2 MB cap); graceful Python fallback

### Auth
- JWT access tokens (24h expiry) signed with `python-jose`
- bcrypt password hashing via `passlib`
- Token revocation via Redis blocklist; TTL matches token expiry

### CI
- GitHub Actions: full Python test suite, Go build + vet, Next.js type check + production build
- All three jobs run on every push and PR to `main`

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Redux Toolkit, RTK Query, Framer Motion, Recharts |
| Backend | FastAPI, Python 3.11, Pydantic v2, LangChain |
| Embeddings | `intfloat/multilingual-e5-base` — 94 languages, 768-dim |
| Reranker | `cross-encoder/mmarco-mMiniLMv2-L12-H384-v1` — 100 languages |
| LLM | Gemini 1.5 Flash/Pro · Claude Haiku · GPT-4o Mini |
| Vector DB | ChromaDB (persistent, cosine) |
| Database | PostgreSQL 16 (prod) / SQLite (dev) — SQLAlchemy + Alembic |
| Caching | Redis 7 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Web Search | Brave Search API + concurrent Go scraper |
| Observability | Sentry SDK (backend + frontend), Loguru structured logs |
| Infra | Docker Compose, GitHub Actions CI, Render |

---

## Multilingual Support

DevFlow supports 94+ languages end-to-end:

- **Indexing** — any document language is detected (`langdetect`) and stored as metadata
- **Embedding** — `multilingual-e5-base` with correct asymmetric prefixing: `passage:` for indexed documents, `query:` for queries — as specified in the model paper for optimal retrieval quality
- **HyDE** — hypothetical answer generated in the detected query language via the LLM
- **Reranking** — `mmarco-mMiniLMv2` cross-encoder is MMARCO-trained across 100 languages
- **Generation** — LLM prompt instructs the model to respond in the same language as the question
- **Caching** — cache key includes the detected language code to prevent cross-language cache collisions
- **Migration** — existing v1 embeddings (all-MiniLM, 384-dim) can be re-embedded via `POST /api/admin/reindex-all`

---

## Frontend Pages

| Route | Description |
|---|---|
| `/search` | Semantic and hybrid search with source cards and web results |
| `/chat` | Streaming chat with session memory and collection scoping |
| `/sources` | Manage indexed sources — upload, URL index, manual add, bulk delete, chunk preview |
| `/collections` | Create and manage collections |
| `/history` | Paginated search history |
| `/analytics` | Charts: queries by day, cache hit rate, model usage, source types |
| `/login` | Login |
| `/register` | Register |

---

## Setup

### Prerequisites

- Python 3.11
- Node.js 20
- Redis (local or remote)
- PostgreSQL 16 (or omit `DATABASE_URL` to use SQLite for local dev)

### Backend

```bash
cd backend
cp .env.example .env
# Fill in required variables (see table below)
pip install -r requirements.txt
alembic upgrade head        # run migrations
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
# Create .env.local:
#   NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
```

### Go Scraper

```bash
cd go-scraper
go build -o scraper .
SCRAPER_PORT=8001 ./scraper
```

### Docker (full stack)

Spins up PostgreSQL 16, Redis 7, Go scraper, backend, and frontend with health-checked startup ordering.

```bash
cp backend/.env.example backend/.env
# Fill in API keys
docker-compose up --build
```

---

## Environment Variables

### Required

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Primary LLM — Gemini 1.5 Flash/Pro |
| `JWT_SECRET_KEY` | Strong random secret for token signing |
| `REDIS_URL` | Redis connection string (e.g. `redis://localhost:6379`) |
| `ALLOWED_ORIGINS` | Comma-separated allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | Backend URL consumed by the frontend |

### Optional

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./devflow.db` | PostgreSQL URL for production |
| `ANTHROPIC_API_KEY` | — | Enables Claude Haiku model |
| `OPENAI_API_KEY` | — | Enables GPT-4o Mini model |
| `BRAVE_API_KEY` | — | Brave Search API for web fallback |
| `GO_SCRAPER_URL` | `http://localhost:8001` | URL of the Go concurrent scraper service |
| `SENTRY_DSN` | — | Backend Sentry DSN for error tracking + tracing |
| `NEXT_PUBLIC_SENTRY_DSN` | — | Frontend Sentry DSN |
| `AWS_S3_BUCKET` | — | S3 bucket for upload mirroring |
| `AWS_S3_REGION` | `us-east-1` | S3 region |
| `AWS_ACCESS_KEY_ID` | — | AWS credentials for S3 |
| `AWS_SECRET_ACCESS_KEY` | — | AWS credentials for S3 |
| `CACHE_TTL` | `3600` | Redis cache TTL in seconds |
| `ENVIRONMENT` | `production` | Sentry environment tag |
| `CHROMA_PATH` | `./chroma_db` | ChromaDB persistence path |
| `POSTGRES_PASSWORD` | `devflow_secret` | Docker Compose PostgreSQL password |

---

## API Reference

### Auth

| Method | Path | Rate limit | Description |
|---|---|---|---|
| POST | `/api/auth/register` | 5/min | Create account, returns JWT |
| POST | `/api/auth/login` | 5/min | Login, returns JWT |
| POST | `/api/auth/logout` | — | Revoke token (adds to Redis blocklist) |

### Search

| Method | Path | Rate limit | Description |
|---|---|---|---|
| POST | `/api/search` | 30/min | Semantic search with optional HyDE and reranking |
| POST | `/api/search/hybrid` | 30/min | Semantic + web fallback search |

Both endpoints cache results in Redis, keyed by query, model, and detected language.

**Search request fields:**
- `query` — 1–1000 chars
- `n_results` — 1–20, default 5
- `model` — `gemini-flash` | `gemini-pro` | `claude-haiku` | `gpt-4o-mini`
- `rerank` — boolean, default `true`
- `use_hyde` — boolean, default `false`
- `use_web` — boolean (hybrid only), default `true`

### Chat

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat/stream` | Streaming SSE chat; returns `data: {"chunk": "..."}` events, ends with `data: [DONE]` |
| GET | `/api/chat/history/{session_id}` | Retrieve conversation history for a session |
| DELETE | `/api/chat/history/{session_id}` | Clear session history from Redis |
| GET | `/api/chat/new-session` | Generate a new session ID |

Chat session history stored in Redis (`devflow:chat:{session_id}`) with 24h TTL. Keeps last 20 messages.

### Ingestion

| Method | Path | Rate limit | Description |
|---|---|---|---|
| POST | `/api/upload` | 10/min | Upload PDF/DOCX/TXT (max 10 MB) — async, returns job ID |
| GET | `/api/upload/status/{job_id}` | — | Poll background indexing job |
| POST | `/api/index/url` | 10/min | Index a URL — async, returns job ID |
| POST | `/api/index/manual` | — | Add document content directly |
| POST | `/api/save-web-result` | — | Save a web search result to the knowledge base |

### Sources

| Method | Path | Description |
|---|---|---|
| GET | `/api/sources` | List sources, paginated; filter by `collection_id` |
| DELETE | `/api/sources/{id}` | Delete source and its vectors from ChromaDB |
| POST | `/api/sources/bulk-delete` | Delete multiple sources — body: `{"ids": [1, 2, 3]}` |
| GET | `/api/sources/{id}/chunks` | Inspect indexed chunks for a source |

### Collections

| Method | Path | Description |
|---|---|---|
| GET | `/api/collections` | List all collections with source counts |
| POST | `/api/collections` | Create collection — body: `{"name": "...", "description": "..."}` |
| DELETE | `/api/collections/{id}` | Delete collection (sources are not deleted) |
| GET | `/api/collections/{id}/sources` | List sources in a collection |
| POST | `/api/collections/{id}/sources/{source_id}` | Add source to collection |
| DELETE | `/api/collections/{id}/sources/{source_id}` | Remove source from collection |

### History & Analytics

| Method | Path | Description |
|---|---|---|
| GET | `/api/history` | Paginated search history (`?limit=50`, max 200) |
| GET | `/api/analytics` | Top queries, searches by day (7d), cache hit rate, model usage, source types |
| GET | `/api/stats` | Source count, document count, total searches, ChromaDB chunk count |

### Admin

| Method | Path | Description |
|---|---|---|
| POST | `/api/admin/reindex-all` | Re-embed all v1 (384-dim) content with multilingual-e5-base — async, returns job ID |

### System

| Method | Path | Description |
|---|---|---|
| GET | `/health` | DB + Redis + ChromaDB liveness; 503 if DB is down |
| GET | `/` | Status + stats summary |
| ANY | `/graphql` | GraphQL endpoint with GraphiQL explorer |

---

## GraphQL

Available at `/graphql` with GraphiQL explorer.

**Queries:** `sources`, `stats`, `collections`, `history`, `analytics`, `jobStatus`

**Mutations:** `deleteSource`, `createCollection`, `deleteCollection`, `addSourceToCollection`, `search`

All mutations and queries use lazy-loaded singletons — ML models are not re-instantiated per request.

---

## Database

### Migrations

```bash
cd backend
alembic upgrade head                                    # apply all migrations
alembic revision --autogenerate -m "description"        # generate new migration
```

**Tables:** `sources`, `documents`, `search_history`, `collections`, `source_collections`, `index_jobs`, `users`

`metadata.create_all()` is also called on app startup as a safety net for environments without Alembic.

### Connection pooling

- PostgreSQL: `QueuePool` — `pool_size=10`, `max_overflow=20`, `pool_timeout=30s`
- SQLite: `StaticPool` with `check_same_thread=False`
- Both use `pool_pre_ping=True`

---

## Testing

```bash
cd backend
pytest tests/ -v
```

Full API surface coverage: health, auth (register/login/logout/duplicate rejection/wrong-password), sources, pagination, stats, upload validation (extension, magic bytes, size), background job lifecycle, collections (CRUD), history, analytics, and manual indexing.

Each test run uses an isolated SQLite database. Sentry is disabled in tests. Rate limiting is active but scoped per test client.

---

## Deployment

### Render

Three services defined in `render.yaml`:

| Service | Runtime | Start command |
|---|---|---|
| `devflow-backend` | Python 3.11 | `alembic upgrade head && uvicorn main:app ...` |
| `devflow-go-scraper` | Go | `./scraper` |
| `devflow-frontend` | Node | `npm start` |

Set environment variables in the Render dashboard — no secrets are stored in the repository.

### Docker Compose

```bash
docker-compose up --build
```

Services: `postgres` (16-alpine), `redis` (7-alpine), `go-scraper`, `backend`, `frontend`. Backend waits for all three dependencies to pass their healthchecks before starting.
