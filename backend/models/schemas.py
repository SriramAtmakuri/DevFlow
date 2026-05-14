from pydantic import BaseModel, Field
from typing import Optional, Literal

SUPPORTED_MODELS = Literal["gemini-flash", "gemini-pro", "claude-haiku", "gpt-4o-mini"]


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    n_results: int = Field(default=5, ge=1, le=20)
    model: SUPPORTED_MODELS = "gemini-flash"
    rerank: bool = True


class HybridSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    n_results: int = Field(default=5, ge=1, le=20)
    use_web: bool = True
    model: SUPPORTED_MODELS = "gemini-flash"
    rerank: bool = True


class ChatStreamRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: str = Field(..., min_length=1)
    model: SUPPORTED_MODELS = "gemini-flash"
    use_web: bool = False


class ManualDocumentRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    content: str = Field(..., min_length=10)
    url: Optional[str] = None
    collection_id: Optional[int] = None


class SaveWebResultRequest(BaseModel):
    title: str = Field(..., min_length=1)
    url: str = Field(..., min_length=1)
    content: str = Field(..., min_length=10)


class IndexResponse(BaseModel):
    success: bool
    message: str
    source_id: int


class UploadResponse(BaseModel):
    success: bool
    message: str
    job_id: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    chunks: int
    error: Optional[str] = None


class StatsResponse(BaseModel):
    sources: int
    documents: int
    searches: int
    chromadb_count: int


class UploadFullResponse(BaseModel):
    success: bool
    message: str
    file_type: str
    source_id: int
    chunks: int
    text_length: int


class UserRegisterRequest(BaseModel):
    email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$')
    password: str = Field(..., min_length=8)
    username: str = Field(..., min_length=3, max_length=50)


class UserLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    username: str


class CollectionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class CollectionResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: str
    source_count: int
