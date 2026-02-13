# AI Prompts Documentation

## Prompts Used During Development

### Prompt 1: Initial Architecture Design
**Input**: "Help me design a RAG-based internal knowledge assistant with PostgreSQL, Redis, and Qdrant"

**Accepted Output**: Architecture diagram with clear separation of concerns
**Rejected Output**: Over-complicated microservices design (too complex for 90 min)

**Human Judgment**: Simplified to monolithic FastAPI service for time constraints

### Prompt 2: Data Model Design
**Input**: "Design PostgreSQL schema for multi-tenant document storage with audit trail"

**Accepted Output**: Core tables (tenants, documents, ai_requests, ai_results)
**Rejected Output**: Suggested adding 10+ tables for analytics (out of scope)

**Human Judgment**: Kept minimal schema, deferred analytics tables

### Prompt 3: Prompt Engineering for QA
**Input**: "Create a prompt for answering questions from document context that cites sources"

**Iteration 1**: Too verbose, included unnecessary instructions
**Iteration 2**: Missing structured output format
**Iteration 3 (Final)**: Concise with JSON output format

**Human Judgment**: Added explicit refusal instruction for missing context

---

## Production Prompts

### System Prompt (Knowledge Assistant)

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

**Rationale**:
- Explicit tenant name prevents cross-tenant confusion
- Clear refusal instruction reduces hallucination
- JSON output enables programmatic parsing
- Confidence field helps users gauge reliability

### User Prompt Template

```
Context documents:
{context}

Question: {question}

Respond in JSON format:
{
  "answer": "your answer here",
  "sources": ["document title 1", "document title 2"],
  "confidence": "high|medium|low|none"
}
```

**Rationale**:
- Context first (helps with attention in long contexts)
- Explicit JSON structure ensures parseable output
- Confidence levels help users decide when to verify

### Refusal Prompt (When No Context Found)

```
No relevant documents were found for this question.

Question: {question}

Respond with:
{
  "answer": "I cannot answer this question based on the available internal documents.",
  "sources": [],
  "confidence": "none"
}
```

**Rationale**:
- Explicit refusal is better than hallucinated answer
- Users know to seek information elsewhere
- Audit trail shows system behaved correctly

---

## Prompt Design Decisions

### Why Structured JSON Output?
1. **Parseability**: Backend can extract fields reliably
2. **Consistency**: Same format for all responses
3. **Auditability**: Easy to log and analyze

### Why Confidence Levels?
1. **User Trust**: Users know when to double-check
2. **Metrics**: Can track answer quality over time
3. **Escalation**: Low confidence can trigger human review

### Why Explicit Refusal Instructions?
1. **Safety**: Prevents hallucinated answers
2. **Trust**: Users learn system is honest about limitations
3. **Compliance**: Important for regulated industries

---

## Iterations Log

| Version | Change | Reason |
|---------|--------|--------|
| v1 | Initial prompt | Basic QA functionality |
| v2 | Added JSON output | Enable programmatic parsing |
| v3 | Added confidence field | Help users gauge reliability |
| v4 | Added explicit refusal | Reduce hallucinations |
| v5 | Added tenant name | Multi-tenant clarity |
