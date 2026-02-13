# Section B - RAG Design (B1)

## Document Chunking Strategy

### Approach: Sentence-Aware Fixed-Size Chunking

```python
CHUNK_SIZE = 500 characters
CHUNK_OVERLAP = 50 words
```

### How Documents are Chunked:
1. Split content by sentence boundaries (`. `)
2. Accumulate sentences until `CHUNK_SIZE` is reached
3. Create chunk and keep `CHUNK_OVERLAP` words for context continuity
4. Repeat until document is fully processed

### Why This Approach:
- **Sentence boundaries**: Avoids cutting mid-thought
- **Fixed size**: Predictable token usage for LLM
- **Overlap**: Maintains context across chunk boundaries
- **Simple**: Easy to debug and understand

### Trade-offs:
- Not semantic chunking (would be better for v2)
- Fixed size may split related paragraphs
- Overlap adds some redundancy

---

## Embedding Storage

### Vector Database: Qdrant

**Collection Strategy**: One collection per tenant (`tenant_{id}`)

**Embedding Model**: `all-MiniLM-L6-v2`
- Dimension: 384
- Fast inference
- Good quality for semantic search
- Runs locally (no API costs)

**Point Structure**:
```json
{
  "id": "uuid",
  "vector": [0.1, 0.2, ...],
  "payload": {
    "tenant_id": 1,
    "document_id": 123,
    "chunk_index": 0,
    "content": "chunk text...",
    "document_title": "Employee Handbook"
  }
}
```

---

## Tenant-Scoped Retrieval

### Multi-Layer Isolation:

**Layer 1: Physical Collection Separation**
```python
collection_name = f"tenant_{tenant_id}"
```
Each tenant has their own Qdrant collection - no data mixing possible.

**Layer 2: Filter in Search (Defense in Depth)**
```python
results = client.search(
    collection_name=collection_name,
    query_vector=embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="tenant_id",
                match=MatchValue(value=tenant_id)
            )
        ]
    )
)
```

### Why Defense in Depth:
- If collection naming has a bug, filter prevents cross-tenant leakage
- Explicit tenant check in every query
- Audit trail shows which tenant accessed what

---

## Retrieval Flow

1. User submits question with `X-Tenant-ID` header
2. Generate query embedding using same model as indexing
3. Search tenant's collection with top-k=5, score_threshold=0.3
4. Return chunks with metadata (title, content, score)
5. Pass to LLM for answer generation

### Score Threshold Rationale:
- 0.3 is conservative - only reasonably relevant chunks
- Prevents hallucination from marginally related content
- If no chunks pass threshold, system refuses to answer
