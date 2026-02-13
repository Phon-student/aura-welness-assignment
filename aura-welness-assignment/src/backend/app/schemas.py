from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


# Tenant schemas
class TenantCreate(BaseModel):
    name: str
    slug: str


class TenantResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Document schemas
class DocumentCreate(BaseModel):
    title: str
    content: str
    source: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    tenant_id: int
    title: str
    source: Optional[str]
    chunk_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Question schemas
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class SourceInfo(BaseModel):
    document: str
    chunk: str


class QuestionResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    confidence: str
    request_id: UUID


# Health schemas
class HealthResponse(BaseModel):
    status: str
    postgres: bool
    redis: bool
    qdrant: bool
