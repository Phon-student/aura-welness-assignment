# Section A - Core AI System Design

## A1. Problem Framing

### Who is the user?
Internal employees across departments (HR, Operations, Marketing, Customer Support) who need quick access to company knowledge.

### What decision are they trying to make?
- Finding accurate answers to policy questions
- Locating procedures and guidelines
- Understanding company processes
- Making informed decisions based on internal documentation

### Why a rule-based system is insufficient?
1. **Natural Language Variability**: Employees phrase questions in countless ways ("How many vacation days?", "What's the PTO policy?", "Time off allowance?")
2. **Unstructured Documents**: Internal docs are markdown/text with varying formats
3. **Semantic Understanding**: Questions require understanding context, not just keyword matching
4. **Scale**: Hundreds of documents across topics - impossible to write rules for all
5. **Maintenance**: Rule-based systems require constant updates as docs change

---

## A2. System Architecture

See README.md for diagram.

### Components:
- **API Layer (FastAPI)**: REST endpoints for document ingestion and Q&A
- **LLM Usage**: GPT-3.5/4 for answer generation (stubbed for demo)
- **Prompt Layer**: System + user prompts with JSON output format
- **PostgreSQL**: Tenants, documents, AI requests/results, audit logs
- **Qdrant (Vector DB)**: Document embeddings, tenant-scoped collections
- **Redis**: Query caching, rate limiting, idempotency keys

---

## A3. Data Model

### Tenant Isolation Strategy
Every table with tenant data includes `tenant_id` foreign key:
```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    tenant_id INTEGER NOT NULL REFERENCES tenants(id),
    -- ...
);
```

### Key Tables:
1. **tenants**: B2B customers (id, name, slug)
2. **documents**: Source documents (tenant_id, title, content, content_hash)
3. **document_chunks**: RAG chunks (tenant_id, document_id, content, vector_id)
4. **ai_requests**: Audit trail (tenant_id, request_id, question, context_chunks)
5. **ai_results**: Answers (tenant_id, answer, sources, confidence, tokens)

### TenantId Enforcement:
- All queries include `WHERE tenant_id = ?`
- Vector collections are named `tenant_{id}` for physical isolation
- Additional filter in vector search for defense in depth

---

## A4. Prompt Design

### System Prompt
```
You are an internal knowledge assistant for {tenant_name}. Your role is to answer employee questions based ONLY on the provided context documents.

Rules:
1. Only use information from the provided context
2. If the context does not contain relevant information, say "I cannot answer this based on available documents"
3. Always cite which document(s) you used
4. Be concise and direct
5. Never make up information

Output format: JSON with fields: answer, sources, confidence
```

### User Prompt
```
Context documents:
{context}

Question: {question}

Respond in JSON format:
{
  "answer": "your answer here",
  "sources": ["document title 1"],
  "confidence": "high|medium|low|none"
}
```

### Why This Structure:
1. **Explicit tenant name**: Prevents confusion in multi-tenant context
2. **Clear rules**: Reduces hallucination risk
3. **Refusal instruction**: System admits when it doesn't know
4. **JSON output**: Programmatically parseable
5. **Confidence levels**: Helps users gauge reliability
6. **Source citation**: Builds trust and enables verification
