import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional


# ── Types ─────────────────────────────────────────────────────────────────────

@strawberry.type
class SourceType:
    id: int
    type: str
    name: Optional[str]
    status: str
    indexed_at: Optional[str]
    created_at: str
    doc_count: int


@strawberry.type
class StatsType:
    sources: int
    documents: int
    searches: int
    chromadb_count: int


@strawberry.type
class CollectionType:
    id: int
    name: str
    description: Optional[str]
    source_count: int
    created_at: str


@strawberry.type
class HistoryItemType:
    id: int
    query: str
    results_count: int
    cached: int
    model: str
    created_at: str


@strawberry.type
class SearchResultType:
    answer: str
    model: str
    cached: bool
    source_count: int


@strawberry.type
class AnalyticsType:
    cache_hit_rate: float
    chromadb_count: int


@strawberry.type
class JobType:
    job_id: str
    status: str
    filename: str
    chunks: int
    error: Optional[str]


@strawberry.type
class MutationResult:
    success: bool
    message: str


# ── Query ─────────────────────────────────────────────────────────────────────

@strawberry.type
class Query:
    @strawberry.field
    def sources(self, collection_id: Optional[int] = None, limit: int = 50, offset: int = 0) -> List[SourceType]:
        from database.db import Database
        return [
            SourceType(
                id=r["id"], type=r["type"], name=r.get("name"),
                status=r["status"], indexed_at=r.get("indexed_at"),
                created_at=r["created_at"], doc_count=r.get("doc_count", 0),
            )
            for r in Database().get_sources(collection_id=collection_id, limit=limit, offset=offset)
        ]

    @strawberry.field
    def stats(self) -> StatsType:
        from database.db import Database
        from rag.retriever import Retriever
        s = Database().get_stats()
        return StatsType(
            sources=s["sources"], documents=s["documents"],
            searches=s["searches"], chromadb_count=Retriever().count(),
        )

    @strawberry.field
    def collections(self) -> List[CollectionType]:
        from database.db import Database
        return [
            CollectionType(
                id=c["id"], name=c["name"], description=c.get("description"),
                source_count=c.get("source_count", 0), created_at=c["created_at"],
            )
            for c in Database().get_collections()
        ]

    @strawberry.field
    def history(self, limit: int = 50) -> List[HistoryItemType]:
        from database.db import Database
        return [
            HistoryItemType(
                id=h["id"], query=h["query"], results_count=h["results_count"],
                cached=h["cached"], model=h["model"], created_at=h["created_at"],
            )
            for h in Database().get_search_history(limit)
        ]

    @strawberry.field
    def analytics(self) -> AnalyticsType:
        from database.db import Database
        from rag.retriever import Retriever
        d = Database().get_analytics()
        return AnalyticsType(
            cache_hit_rate=d.get("cache_hit_rate", 0.0),
            chromadb_count=Retriever().count(),
        )

    @strawberry.field
    def job_status(self, job_id: str) -> Optional[JobType]:
        from database.db import Database
        j = Database().get_job(job_id)
        if not j:
            return None
        return JobType(
            job_id=job_id, status=j["status"], filename=j["filename"],
            chunks=j.get("chunks", 0), error=j.get("error"),
        )


# ── Mutation ──────────────────────────────────────────────────────────────────

@strawberry.type
class Mutation:
    @strawberry.mutation
    def delete_source(self, source_id: int) -> MutationResult:
        from database.db import Database
        from rag.retriever import Retriever
        try:
            Retriever().delete_by_source(source_id)
            Database().delete_source(source_id)
            return MutationResult(success=True, message="Source deleted")
        except Exception as e:
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation
    def create_collection(self, name: str, description: Optional[str] = None) -> CollectionType:
        from database.db import Database
        db = Database()
        cid = db.create_collection(name, description)
        cols = db.get_collections()
        col = next((c for c in cols if c["id"] == cid), None)
        return CollectionType(
            id=cid, name=name, description=description,
            source_count=0, created_at=col["created_at"] if col else "",
        )

    @strawberry.mutation
    def delete_collection(self, collection_id: int) -> MutationResult:
        from database.db import Database
        try:
            Database().delete_collection(collection_id)
            return MutationResult(success=True, message="Collection deleted")
        except Exception as e:
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation
    def add_source_to_collection(self, source_id: int, collection_id: int) -> MutationResult:
        from database.db import Database
        try:
            Database().add_source_to_collection(source_id, collection_id)
            return MutationResult(success=True, message="Source added to collection")
        except Exception as e:
            return MutationResult(success=False, message=str(e))

    @strawberry.mutation
    def search(
        self, query: str, n_results: int = 5,
        model: str = "gemini-flash", use_hyde: bool = False,
    ) -> SearchResultType:
        from rag.retriever import Retriever
        from rag.reranker import Reranker
        from rag.generator import GeminiRAG
        from database.db import Database
        from cache.redis_cache import make_cache_key, get_cached, set_cached

        cache_key = make_cache_key("gql_search", {"q": query, "n": n_results, "m": model})
        cached = get_cached(cache_key)
        if cached:
            return SearchResultType(
                answer=cached["answer"], model=model,
                cached=True, source_count=len(cached.get("sources", [])),
            )

        retriever = Retriever()
        results = retriever.search(query, n_results, use_hyde=use_hyde)
        documents = results["documents"] or []
        metadatas = results["metadatas"] or []

        if documents:
            documents, metadatas = Reranker().rerank(query, documents, metadatas)

        if not documents:
            return SearchResultType(answer="No relevant documents found.", model=model, cached=False, source_count=0)

        response = GeminiRAG().generate_answer(query=query, context=documents, sources=metadatas, model=model)
        Database().add_search(query, len(documents), cached=False, model=model)
        set_cached(cache_key, response)

        return SearchResultType(
            answer=response["answer"], model=model,
            cached=False, source_count=len(documents),
        )


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, graphiql=True)
