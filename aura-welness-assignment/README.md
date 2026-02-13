# Internal Knowledge Assistant - AI Engineer Assessment

## Approach

This is an Internal Knowledge Assistant (Option C) that allows employees to ask questions about internal documents. The system uses RAG (Retrieval Augmented Generation) to provide accurate answers with source citations.

### User & Decision Context
- **User**: Internal employees (HR, Operations, Marketing, Support)
- **Decision**: Get quick, accurate answers from company knowledge base
- **Why not rule-based**: Natural language queries require semantic understanding; documents are unstructured and varied

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer (FastAPI)                      │
├─────────────────────────────────────────────────────────────────┤
│  POST /documents     - Ingest documents                         │
│  POST /ask           - Ask questions                            │
│  GET  /health        - Health check                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  DocumentService  - Chunk, embed, store documents               │
│  QueryService     - Retrieve context, generate answers          │
│  PromptService    - Build prompts with tenant context           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  PostgreSQL   │   │   Qdrant        │   │     Redis       │
│  (System of   │   │   (Vector DB)   │   │   (Cache)       │
│   Record)     │   │                 │   │                 │
├───────────────┤   ├─────────────────┤   ├─────────────────┤
│ - Tenants     │   │ - Document      │   │ - Query cache   │
│ - Documents   │   │   embeddings    │   │ - Rate limiting │
│ - AI Requests │   │ - Tenant-scoped │   │ - Idempotency   │
│ - AI Results  │   │   collections   │   │                 │
│ - Audit logs  │   │                 │   │                 │
└───────────────┘   └─────────────────┘   └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   LLM Provider  │
                    │   (Stubbed)     │
                    └─────────────────┘
```

## Trade-offs Made

1. **Stub LLM**: Real data flow but stubbed LLM responses for demo
2. **Simple chunking**: Fixed-size chunks (good enough for v1)
3. **Single collection per tenant**: Clear isolation, slight overhead
4. **No async workers**: Synchronous processing for simplicity

## Assumptions

- Documents are markdown/text format
- Each tenant has reasonable document volume (<10k docs)
- Questions are in English
- LLM API would be OpenAI-compatible in production

## What I Would Improve

- Add async document processing with Celery
- Implement streaming responses
- Add document versioning
- Implement feedback loop for answer quality
- Add semantic caching based on query similarity

---

## Runbook

### Prerequisites

- Docker Desktop installed
- Docker Compose v2+
- 4GB RAM available

### Quick Start

```bash
# Clone and start
git clone <repo-url>
cd aura

# Start all services
docker compose up --build

# Wait for health checks (about 30 seconds)
```

### Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Key variables:
- `DATABASE_URL`: PostgreSQL connection
- `REDIS_URL`: Redis connection
- `QDRANT_URL`: Qdrant vector DB
- `LLM_API_KEY`: OpenAI API key (optional for stub mode)
- `LLM_STUB_MODE`: Set to "true" for stubbed responses

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","postgres":true,"redis":true,"qdrant":true}
```

### Example API Calls

#### 1. Create a Tenant

```bash
curl -X POST http://localhost:8000/tenants \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "slug": "acme"}'
```

#### 2. Ingest a Document

```bash
curl -X POST http://localhost:8000/documents \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "title": "Employee Handbook",
    "content": "# Vacation Policy\n\nEmployees receive 20 days PTO per year. Unused days roll over up to 5 days maximum.\n\n# Sick Leave\n\nUnlimited sick leave with manager approval.",
    "source": "hr/handbook.md"
  }'
```

#### 3. Ask a Question

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "question": "How many vacation days do employees get?"
  }'
```

Expected response:
```json
{
  "answer": "Employees receive 20 days PTO per year.",
  "sources": [
    {"document": "Employee Handbook", "chunk": "Employees receive 20 days PTO..."}
  ],
  "confidence": "high",
  "request_id": "uuid-here"
}
```

#### 4. Query with No Context (Refusal)

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -H "X-Tenant-ID: 1" \
  -d '{
    "question": "What is the meaning of life?"
  }'
```

Expected response:
```json
{
  "answer": "I cannot answer this question based on the available internal documents.",
  "sources": [],
  "confidence": "none",
  "request_id": "uuid-here"
}
```

### Stopping Services

```bash
docker compose down

# To also remove volumes:
docker compose down -v
```
