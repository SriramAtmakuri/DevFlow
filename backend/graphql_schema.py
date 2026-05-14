import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List, Optional


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
class MutationResult:
    success: bool
    message: str


@strawberry.type
class Query:
    @strawberry.field
    def sources(self) -> List[SourceType]:
        from database.db import Database
        db = Database()
        return [
            SourceType(
                id=r["id"],
                type=r["type"],
                name=r.get("name"),
                status=r["status"],
                indexed_at=r.get("indexed_at"),
                created_at=r["created_at"],
                doc_count=r.get("doc_count", 0),
            )
            for r in db.get_sources()
        ]

    @strawberry.field
    def stats(self) -> StatsType:
        from database.db import Database
        from rag.retriever import Retriever
        s = Database().get_stats()
        return StatsType(
            sources=s["sources"],
            documents=s["documents"],
            searches=s["searches"],
            chromadb_count=Retriever().count(),
        )


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


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, graphiql=True)
