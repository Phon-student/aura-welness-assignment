from fastapi import FastAPI, Depends, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import engine, Base, get_db
from app.routers import documents, questions, tenants, health
from app.services.vector_service import VectorService
from app.services.cache_service import CacheService

logging.basicConfig(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Knowledge Assistant API...")
    
    # Initialize vector service
    vector_service = VectorService()
    await vector_service.initialize()
    app.state.vector_service = vector_service
    
    # Initialize cache service
    cache_service = CacheService()
    app.state.cache_service = cache_service
    
    logger.info("Services initialized successfully")
    yield
    
    # Shutdown
    logger.info("Shutting down...")


app = FastAPI(
    title="Internal Knowledge Assistant",
    description="AI-powered internal document Q&A system",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(tenants.router, prefix="/tenants", tags=["Tenants"])
app.include_router(documents.router, prefix="/documents", tags=["Documents"])
app.include_router(questions.router, tags=["Questions"])
