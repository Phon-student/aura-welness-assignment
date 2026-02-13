from typing import List, Dict, Any, Optional
import json
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service with stub mode for demo"""
    
    def __init__(self):
        self.stub_mode = settings.LLM_STUB_MODE
        self.model = settings.LLM_MODEL
        
    def build_system_prompt(self, tenant_name: str) -> str:
        """Build system prompt for knowledge assistant"""
        return f"""You are an internal knowledge assistant for {tenant_name}. Your role is to answer employee questions based ONLY on the provided context documents.

Rules:
1. Only use information from the provided context
2. If the context does not contain relevant information, say "I cannot answer this based on available documents"
3. Always cite which document(s) you used
4. Be concise and direct
5. Never make up information

Output format: JSON with fields: answer, sources, confidence"""

    def build_user_prompt(self, question: str, context_chunks: List[Dict[str, Any]]) -> str:
        """Build user prompt with context"""
        if not context_chunks:
            return f"""No relevant documents were found for this question.

Question: {question}

Respond with:
{{
  "answer": "I cannot answer this question based on the available internal documents.",
  "sources": [],
  "confidence": "none"
}}"""
        
        context_text = "\n\n".join([
            f"[Document: {chunk.get('document_title', 'Unknown')}]\n{chunk['content']}"
            for chunk in context_chunks
        ])
        
        return f"""Context documents:
{context_text}

Question: {question}

Respond in JSON format:
{{
  "answer": "your answer here",
  "sources": ["document title 1", "document title 2"],
  "confidence": "high|medium|low|none"
}}"""

    async def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        tenant_name: str = "Company"
    ) -> Dict[str, Any]:
        """Generate answer using LLM (or stub)"""
        
        system_prompt = self.build_system_prompt(tenant_name)
        user_prompt = self.build_user_prompt(question, context_chunks)
        
        if self.stub_mode:
            return self._generate_stub_response(question, context_chunks)
        
        # Real LLM call would go here
        # For production, integrate with OpenAI/Anthropic API
        return self._generate_stub_response(question, context_chunks)
    
    def _generate_stub_response(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate a realistic stub response based on context"""
        
        if not context_chunks:
            return {
                "answer": "I cannot answer this question based on the available internal documents.",
                "sources": [],
                "confidence": "none",
                "prompt_tokens": 50,
                "completion_tokens": 20,
                "total_tokens": 70
            }
        
        # Extract relevant information from context
        top_chunk = context_chunks[0]
        content = top_chunk["content"]
        doc_title = top_chunk.get("document_title", "Internal Document")
        
        # Simple extractive answer (take first relevant sentence)
        sentences = content.split('.')
        answer_sentence = sentences[0].strip() + '.' if sentences else content[:200]
        
        # Determine confidence based on score
        score = top_chunk.get("score", 0.5)
        if score > 0.7:
            confidence = "high"
        elif score > 0.5:
            confidence = "medium"
        else:
            confidence = "low"
        
        sources = list(set([
            chunk.get("document_title", "Internal Document")
            for chunk in context_chunks[:3]
        ]))
        
        return {
            "answer": answer_sentence,
            "sources": sources,
            "confidence": confidence,
            "prompt_tokens": 150 + len(content) // 4,
            "completion_tokens": 50,
            "total_tokens": 200 + len(content) // 4
        }
