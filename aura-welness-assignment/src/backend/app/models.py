from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import uuid


class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    documents = relationship("Document", back_populates="tenant")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    source = Column(String(500))
    content_hash = Column(String(64), nullable=False)
    chunk_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    tenant = relationship("Tenant", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    vector_id = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    
    document = relationship("Document", back_populates="chunks")


class AIRequest(Base):
    __tablename__ = "ai_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    request_id = Column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)
    question = Column(Text, nullable=False)
    context_chunks = Column(ARRAY(Text))
    prompt_tokens = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    user_id = Column(String(100))
    ip_address = Column(String(45))
    
    result = relationship("AIResult", back_populates="request", uselist=False)


class AIResult(Base):
    __tablename__ = "ai_results"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(UUID(as_uuid=True), ForeignKey("ai_requests.request_id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSONB)
    confidence = Column(String(20))
    completion_tokens = Column(Integer)
    total_tokens = Column(Integer)
    latency_ms = Column(Integer)
    was_cached = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    
    request = relationship("AIRequest", back_populates="result")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="SET NULL"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100))
    entity_id = Column(Integer)
    details = Column(JSONB)
    created_at = Column(DateTime, server_default=func.now())
