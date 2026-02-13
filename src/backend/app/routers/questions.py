from fastapi import APIRouter, Depends, HTTPException, Header, Request
from sqlalchemy.orm import Session
from typing import Optional
import uuid
import time

from app.database import get_db
from app.models import Tenant, AIRequest, AIResult, AuditLog
from app.schemas import QuestionRequest, QuestionResponse, SourceInfo
from app.services.llm_service import LLMService

router = APIRouter()


def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> int:
    """Extract and validate tenant ID from header"""
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
    try:
        return int(x_tenant_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tenant ID")


@router.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: Request,
    question_req: QuestionRequest,
    tenant_id: int = Depends(get_tenant_id),
    db: Session = Depends(get_db)
):
    """Ask a question about internal documents"""
    start_time = time.time()
    
    # Verify tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    # Get services
    cache_service = request.app.state.cache_service
    vector_service = request.app.state.vector_service
    
    # Rate limiting
    if not cache_service.check_rate_limit(tenant_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Generate request ID
    request_id = uuid.uuid4()
    
    # Check cache first
    cached = cache_service.get_cached_answer(tenant_id, question_req.question)
    if cached:
        # Return cached response
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log cached request
        ai_request = AIRequest(
            tenant_id=tenant_id,
            request_id=request_id,
            question=question_req.question,
            context_chunks=[]
        )
        db.add(ai_request)
        db.commit()
        
        ai_result = AIResult(
            request_id=request_id,
            tenant_id=tenant_id,
            answer=cached["answer"],
            sources=cached["sources"],
            confidence=cached["confidence"],
            latency_ms=latency_ms,
            was_cached=True
        )
        db.add(ai_result)
        db.commit()
        
        return QuestionResponse(
            answer=cached["answer"],
            sources=[SourceInfo(document=s, chunk="") for s in cached["sources"]],
            confidence=cached["confidence"],
            request_id=request_id
        )
    
    # Search for relevant context
    context_chunks = vector_service.search(
        tenant_id=tenant_id,
        query=question_req.question,
        top_k=5,
        score_threshold=0.3
    )
    
    # Generate answer
    llm_service = LLMService()
    llm_response = await llm_service.generate_answer(
        question=question_req.question,
        context_chunks=context_chunks,
        tenant_name=tenant.name
    )
    
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Store request
    ai_request = AIRequest(
        tenant_id=tenant_id,
        request_id=request_id,
        question=question_req.question,
        context_chunks=[c["content"] for c in context_chunks],
        prompt_tokens=llm_response.get("prompt_tokens")
    )
    db.add(ai_request)
    db.commit()
    
    # Store result
    ai_result = AIResult(
        request_id=request_id,
        tenant_id=tenant_id,
        answer=llm_response["answer"],
        sources=llm_response["sources"],
        confidence=llm_response["confidence"],
        completion_tokens=llm_response.get("completion_tokens"),
        total_tokens=llm_response.get("total_tokens"),
        latency_ms=latency_ms,
        was_cached=False
    )
    db.add(ai_result)
    db.commit()
    
    # Cache the response
    cache_service.cache_answer(
        tenant_id=tenant_id,
        question=question_req.question,
        answer={
            "answer": llm_response["answer"],
            "sources": llm_response["sources"],
            "confidence": llm_response["confidence"]
        }
    )
    
    # Audit log
    audit = AuditLog(
        tenant_id=tenant_id,
        action="question_asked",
        entity_type="ai_request",
        entity_id=ai_request.id,
        details={
            "question_length": len(question_req.question),
            "context_count": len(context_chunks),
            "confidence": llm_response["confidence"],
            "latency_ms": latency_ms
        }
    )
    db.add(audit)
    db.commit()
    
    # Build source info
    sources = []
    source_titles = set()
    for chunk in context_chunks:
        title = chunk.get("document_title", "Internal Document")
        if title not in source_titles:
            sources.append(SourceInfo(
                document=title,
                chunk=chunk["content"][:200] + "..." if len(chunk["content"]) > 200 else chunk["content"]
            ))
            source_titles.add(title)
    
    return QuestionResponse(
        answer=llm_response["answer"],
        sources=sources,
        confidence=llm_response["confidence"],
        request_id=request_id
    )
