from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Tenant, Document, DocumentChunk, AuditLog
from app.schemas import DocumentCreate, DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter()


def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> int:
    """Extract and validate tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
    try:
        return int(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")


@router.post("", response_model=DocumentResponse)
async def create_document(
    request: Request,
    document: DocumentCreate,
    tenant_id: int = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Ingest a document for a tenant"""
    
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Initialize services
    doc_service = DocumentService()
    vector_service = request.app.state.vector_service
    
    # Generate content hash
    content_hash = doc_service.hash_content(document.content)
    
    # Check for duplicate
    existing = db.query(Document).filter(
        Document.tenant_id == tenant_id,
        Document.content_hash == content_hash
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Document already exists")
    
    # Create document record
    db_document = Document(
        tenant_id=tenant_id,
        title=document.title,
        content=document.content,
        source=document.source,
        content_hash=content_hash
    )
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    
    # Chunk document
    chunks = doc_service.chunk_document(document.content, document.title)
    
    # Store embeddings in vector DB
    vector_ids = vector_service.upsert_chunks(
        tenant_id=tenant_id,
        document_id=db_document.id,
        chunks=chunks
    )
    
    # Store chunk records in PostgreSQL
    for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
        db_chunk = DocumentChunk(
            document_id=db_document.id,
            tenant_id=tenant_id,
            chunk_index=i,
            content=chunk["content"],
            vector_id=vector_id
        )
        db.add(db_chunk)
    
    # Update chunk count
    db_document.chunk_count = len(chunks)
    db.commit()
    
    # Audit log
    audit = AuditLog(
        tenant_id=tenant_id,
        action="document_created",
        entity_type="document",
        entity_id=db_document.id,
        details={"title": document.title, "chunks": len(chunks)}
    )
    db.add(audit)
    db.commit()
    
    return db_document


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    tenant_id: int = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """List all documents for a tenant"""
    return db.query(Document).filter(
        Document.tenant_id == tenant_id,
        Document.is_active == True
    ).all()


@router.delete("/{document_id}")
async def delete_document(
    request: Request,
    document_id: int,
    tenant_id: int = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Delete a document"""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.tenant_id == tenant_id  # Tenant isolation
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete from vector DB
    vector_service = request.app.state.vector_service
    vector_service.delete_document_vectors(tenant_id, document_id)
    
    # Soft delete
    document.is_active = False
    db.commit()
    
    # Audit log
    audit = AuditLog(
        tenant_id=tenant_id,
        action="document_deleted",
        entity_type="document",
        entity_id=document_id
    )
    db.add(audit)
    db.commit()
    
    return {"status": "deleted"}
