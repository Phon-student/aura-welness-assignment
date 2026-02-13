from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import logging
import uuid

from app.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.encoder: Optional[SentenceTransformer] = None
        
    async def initialize(self):
        """Initialize Qdrant client and embedding model"""
        try:
            # Parse Qdrant URL
            url = settings.QDRANT_URL
            if url.startswith("http://"):
                host = url.replace("http://", "").split(":")[0]
                port = int(url.split(":")[-1])
            else:
                host = "localhost"
                port = 6333
                
            self.client = QdrantClient(host=host, port=port)
            logger.info(f"Connected to Qdrant at {host}:{port}")
            
            # Load embedding model
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded")
            
        except Exception as e:
            logger.error(f"Failed to initialize vector service: {e}")
            raise
    
    def ensure_collection(self, tenant_id: int) -> str:
        """Ensure collection exists for tenant"""
        collection_name = f"tenant_{tenant_id}"
        
        try:
            collections = self.client.get_collections().collections
            exists = any(c.name == collection_name for c in collections)
            
            if not exists:
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(
                        size=settings.EMBEDDING_DIMENSION,
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created collection: {collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
            raise
            
        return collection_name
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text"""
        return self.encoder.encode(text).tolist()
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return self.encoder.encode(texts).tolist()
    
    def upsert_chunks(
        self,
        tenant_id: int,
        document_id: int,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """Store document chunks with embeddings"""
        collection_name = self.ensure_collection(tenant_id)
        
        # Generate embeddings
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embed_texts(texts)
        
        # Create points
        points = []
        vector_ids = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vector_id = str(uuid.uuid4())
            vector_ids.append(vector_id)
            
            points.append(PointStruct(
                id=vector_id,
                vector=embedding,
                payload={
                    "tenant_id": tenant_id,
                    "document_id": document_id,
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                    "document_title": chunk.get("document_title", ""),
                }
            ))
        
        # Upsert to Qdrant
        self.client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        logger.info(f"Upserted {len(points)} chunks for document {document_id}")
        return vector_ids
    
    def search(
        self,
        tenant_id: int,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Search for relevant chunks"""
        collection_name = f"tenant_{tenant_id}"
        
        # Check if collection exists
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                logger.warning(f"Collection {collection_name} does not exist")
                return []
        except Exception as e:
            logger.error(f"Error checking collection: {e}")
            return []
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search with tenant filter (defense in depth - collection is already tenant-scoped)
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="tenant_id",
                        match=MatchValue(value=tenant_id)
                    )
                ]
            ),
            limit=top_k,
            score_threshold=score_threshold
        )
        
        return [
            {
                "content": hit.payload["content"],
                "document_id": hit.payload["document_id"],
                "document_title": hit.payload.get("document_title", ""),
                "chunk_index": hit.payload["chunk_index"],
                "score": hit.score
            }
            for hit in results
        ]
    
    def delete_document_vectors(self, tenant_id: int, document_id: int):
        """Delete all vectors for a document"""
        collection_name = f"tenant_{tenant_id}"
        
        try:
            self.client.delete(
                collection_name=collection_name,
                points_selector=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                )
            )
            logger.info(f"Deleted vectors for document {document_id}")
        except Exception as e:
            logger.error(f"Error deleting vectors: {e}")
    
    def health_check(self) -> bool:
        """Check if Qdrant is healthy"""
        try:
            self.client.get_collections()
            return True
        except Exception:
            return False
