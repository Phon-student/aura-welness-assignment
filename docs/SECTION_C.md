# Section C - Cost Control Strategy (C1)

## Token Usage Limits

### 1. Context Truncation
- Max 5 chunks retrieved per query
- Each chunk max 500 chars (~125 tokens)
- Total context: ~625 tokens max

### 2. Caching Strategy
**Redis Cache Key**: `qa:{tenant_id}:{md5(question)}`
**TTL**: 1 hour

```python
def _make_key(self, tenant_id: int, question: str) -> str:
    normalized = question.lower().strip()
    question_hash = hashlib.md5(normalized.encode()).hexdigest()
    return f"qa:{tenant_id}:{question_hash}"
```

**Cache Hit Flow**:
1. Check Redis before vector search
2. If hit, return cached answer (0 LLM tokens)
3. Log as `was_cached=True` for analytics

**Expected Savings**:
- Common questions (PTO, benefits) hit cache ~70% of time
- Each cache hit saves ~1000 tokens

### 3. Rate Limiting
```python
RATE_LIMIT_PER_MINUTE = 60  # per tenant
```
- Prevents runaway costs from misbehaving clients
- Per-tenant to ensure fair usage

---

## When AI Should NOT Be Used

### 1. Exact Match Queries
If question matches document title exactly, return document directly without LLM.

### 2. Low Confidence Scenarios
If vector search returns no results above threshold (0.3), don't call LLM:
```python
if not context_chunks:
    return {
        "answer": "I cannot answer this based on available documents.",
        "confidence": "none"
    }
```
This saves ~1000 tokens per "I don't know" response.

### 3. Repeated Failures
Track questions that consistently get "none" confidence:
- After 3 failures, suggest user contact human support
- Don't waste tokens on questions outside knowledge base

---

## Cost Monitoring

### Token Tracking (stored in PostgreSQL):
```sql
CREATE TABLE ai_results (
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    was_cached BOOLEAN
);
```

### Metrics Available:
- Tokens per tenant per day
- Cache hit ratio
- Cost per answer
- Questions that bypass LLM

---

## v2 Improvements (Not Built Yet)

1. **Semantic Caching**: Cache by embedding similarity, not exact match
2. **Tiered Models**: Use cheaper model for simple questions
3. **Batch Processing**: Combine multiple questions for efficiency
4. **Token Budgets**: Per-tenant monthly limits
