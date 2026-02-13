import hashlib
from typing import List, Dict, Any
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class DocumentService:
    def __init__(self):
        self.chunk_size = settings.CHUNK_SIZE
        self.chunk_overlap = settings.CHUNK_OVERLAP
    
    def hash_content(self, content: str) -> str:
        """Generate hash for content deduplication"""
        return hashlib.sha256(content.encode()).hexdigest()
    
    def chunk_document(self, content: str, document_title: str = "") -> List[Dict[str, Any]]:
        """Split document into overlapping chunks"""
        chunks = []
        
        # Simple sentence-aware chunking
        sentences = content.replace('\n', ' ').split('. ')
        
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            # Add period back if it was removed
            if not sentence.endswith('.'):
                sentence += '.'
            
            # Check if adding this sentence exceeds chunk size
            if len(current_chunk) + len(sentence) > self.chunk_size:
                if current_chunk:
                    chunks.append({
                        "content": current_chunk.strip(),
                        "chunk_index": chunk_index,
                        "document_title": document_title
                    })
                    chunk_index += 1
                    
                    # Keep overlap
                    words = current_chunk.split()
                    overlap_words = words[-self.chunk_overlap:] if len(words) > self.chunk_overlap else words
                    current_chunk = ' '.join(overlap_words) + ' ' + sentence
                else:
                    current_chunk = sentence
            else:
                current_chunk += ' ' + sentence if current_chunk else sentence
        
        # Add remaining content
        if current_chunk.strip():
            chunks.append({
                "content": current_chunk.strip(),
                "chunk_index": chunk_index,
                "document_title": document_title
            })
        
        logger.info(f"Document chunked into {len(chunks)} chunks")
        return chunks
