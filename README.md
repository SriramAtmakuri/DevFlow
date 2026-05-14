# DevFlow

An AI-powered knowledge base for developers. Index your docs, PDFs, and web pages — then query them with natural language using a full RAG pipeline.

## Features

- **Semantic search** across your own documents using vector embeddings
- **Hybrid search** — queries your knowledge base first, falls back to live web results
- **Streaming chat** with session memory and multi-model support (Gemini, Claude, GPT-4)
- **File ingestion** — upload PDF, DOCX, and TXT files with background indexing
- **Collections** to organise sources into workspaces
- **Analytics dashboard** — query patterns, cache hit rate, model usage
- **Redis caching** — repeated queries served instantly without LLM calls
- **JWT authentication** with token revocation via Redis blocklist
- **GraphQL API** alongside REST, with GraphiQL explorer

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Redux Toolkit, RTK Query, Framer Motion |
| Backend | FastAPI, Python 3.11, Pydantic v2, LangChain |
| AI / RAG | Google Gemini 1.5 Flash, sentence-transformers, cross-encoder reranking |
| Vector DB | ChromaDB (persistent) |
| Caching | Redis |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Web Search | Brave Search API + concurrent Go scraper |
| Infra | Docker Compose, GitHub Actions CI, Render |

## Setup

### Backend

```bash
cd backend
cp .env.example .env
# Fill in: GEMINI_API_KEY, BRAVE_API_KEY, JWT_SECRET_KEY, REDIS_URL, ALLOWED_ORIGINS
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
# Create .env.local with: NEXT_PUBLIC_API_URL=<your backend URL>
npm install
npm run dev
```

### Docker (full stack)

```bash
docker-compose up --build
```

## Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio key |
| `BRAVE_API_KEY` | Brave Search API key |
| `ANTHROPIC_API_KEY` | Anthropic key (optional, for Claude models) |
| `OPENAI_API_KEY` | OpenAI key (optional, for GPT models) |
| `JWT_SECRET_KEY` | Strong random secret for token signing |
| `REDIS_URL` | Redis connection string |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed frontend origins |
| `NEXT_PUBLIC_API_URL` | Backend URL for the frontend |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/register` | Create account |
| POST | `/api/auth/login` | Login, returns JWT |
| POST | `/api/auth/logout` | Revoke token |
| POST | `/api/search` | Semantic document search |
| POST | `/api/search/hybrid` | Hybrid doc + web search |
| POST | `/api/chat/stream` | Streaming chat (SSE) |
| POST | `/api/upload` | Upload file (PDF/DOCX/TXT) |
| GET | `/api/upload/status/{job_id}` | Check indexing job status |
| POST | `/api/index/manual` | Add document manually |
| GET | `/api/sources` | List all sources |
| DELETE | `/api/sources/{id}` | Delete source and its vectors |
| GET | `/api/collections` | List collections |
| POST | `/api/collections` | Create collection |
| GET | `/api/history` | Search history |
| GET | `/api/analytics` | Usage analytics |
| GET | `/api/stats` | System stats |
| ANY | `/graphql` | GraphQL endpoint |

## Deployment

All services are defined in `render.yaml`. Set the environment variables listed above in the Render dashboard — no secrets are stored in the repo.
