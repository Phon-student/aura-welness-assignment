from fastapi import APIRouter, Request
from sqlalchemy import text
from app.database import SessionLocal
from app.schemas import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    """Check health of all services"""
    
    # Check PostgreSQL
    postgres_ok = False
    try:
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        postgres_ok = True
    except Exception:
        pass
    
    # Check Redis
    redis_ok = False
    try:
        cache_service = request.app.state.cache_service
        redis_ok = cache_service.health_check()
    except Exception:
        pass
    
    # Check Qdrant
    qdrant_ok = False
    try:
        vector_service = request.app.state.vector_service
        qdrant_ok = vector_service.health_check()
    except Exception:
        pass
    
    all_healthy = postgres_ok and redis_ok and qdrant_ok
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        postgres=postgres_ok,
        redis=redis_ok,
        qdrant=qdrant_ok
    )
