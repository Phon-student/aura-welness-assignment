# Section D - Tenant Isolation Strategy (D1)

## Prompt Isolation

### 1. Tenant Name in System Prompt
```
You are an internal knowledge assistant for {tenant_name}.
```
- LLM knows exactly which tenant's perspective to use
- Prevents confusion if model has seen other company data

### 2. Context Contains Only Tenant Documents
```python
context_chunks = vector_service.search(
    tenant_id=tenant_id,  # Explicit filter
    query=question
)
```
- Only documents from requesting tenant in context
- Impossible to reference other tenant's information

### 3. No Cross-Tenant Patterns in Prompts
- Never include "For all customers..." patterns
- No comparative analysis across tenants
- Each request is fully isolated

---

## Vector Search Scoping

### Physical Isolation (Primary)
```python
collection_name = f"tenant_{tenant_id}"
```
- Each tenant has dedicated Qdrant collection
- No shared vector space
- Complete data separation

### Logical Isolation (Secondary)
```python
query_filter=Filter(
    must=[
        FieldCondition(
            key="tenant_id",
            match=MatchValue(value=tenant_id)
        )
    ]
)
```
- Even within collection, filter by tenant_id
- Defense against misconfigured collection names
- Belt-and-suspenders approach

---

## Database Isolation

### All Queries Include tenant_id
```python
db.query(Document).filter(
    Document.tenant_id == tenant_id,
    Document.is_active == True
).all()
```

### Foreign Key Constraints
```sql
document_id INTEGER REFERENCES documents(id) ON DELETE CASCADE
tenant_id INTEGER NOT NULL REFERENCES tenants(id) ON DELETE CASCADE
```
- Cascade deletes prevent orphaned data
- Can't create records without valid tenant

---

## API-Level Enforcement

### Required Header
```python
def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> int:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
```
- Every request must specify tenant
- No default tenant (explicit > implicit)

### Validation
```python
tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
if not tenant:
    raise HTTPException(status_code=404, detail="Tenant not found")
```
- Verify tenant exists before any operation
- Invalid tenant = immediate rejection

---

## Audit Trail

Every action logged with tenant_id:
```sql
CREATE TABLE audit_logs (
    tenant_id INTEGER REFERENCES tenants(id),
    action VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100),
    details JSONB
);
```

Enables:
- Per-tenant usage analytics
- Security incident investigation
- Compliance reporting
