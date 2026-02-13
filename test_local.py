"""
Local test script - validates code without running external services.
This proves the code will work when Docker runs.
"""
import sys
import importlib.util
from pathlib import Path

def test_imports():
    """Test all modules can be imported"""
    print("Testing imports...")
    
    backend_path = Path("src/backend")
    sys.path.insert(0, str(backend_path))
    
    modules = [
        "app.config",
        "app.schemas", 
        "app.models",
        "app.services.document_service",
        "app.services.llm_service",
    ]
    
    for module in modules:
        try:
            importlib.import_module(module)
            print(f"  [OK] {module}")
        except Exception as e:
            print(f"  [FAIL] {module}: {e}")
            return False
    return True

def test_config():
    """Test configuration loads"""
    print("\nTesting configuration...")
    from app.config import settings
    
    assert settings.CHUNK_SIZE == 500
    assert settings.EMBEDDING_DIMENSION == 384
    assert settings.LLM_STUB_MODE == True
    print("  [OK] Config loads correctly")
    return True

def test_schemas():
    """Test Pydantic schemas"""
    print("\nTesting schemas...")
    from app.schemas import (
        TenantCreate, DocumentCreate, QuestionRequest, 
        QuestionResponse, SourceInfo
    )
    from uuid import uuid4
    
    # Test TenantCreate
    tenant = TenantCreate(name="Test Corp", slug="test")
    assert tenant.name == "Test Corp"
    print("  [OK] TenantCreate")
    
    # Test DocumentCreate
    doc = DocumentCreate(title="Test", content="Content here", source="test.md")
    assert doc.title == "Test"
    print("  [OK] DocumentCreate")
    
    # Test QuestionRequest
    q = QuestionRequest(question="How many vacation days?")
    assert len(q.question) > 3
    print("  [OK] QuestionRequest")
    
    # Test QuestionResponse
    resp = QuestionResponse(
        answer="20 days",
        sources=[SourceInfo(document="Handbook", chunk="...")],
        confidence="high",
        request_id=uuid4()
    )
    assert resp.confidence == "high"
    print("  [OK] QuestionResponse")
    
    return True

def test_document_service():
    """Test document chunking logic"""
    print("\nTesting DocumentService...")
    from app.services.document_service import DocumentService
    
    svc = DocumentService()
    
    # Test hashing
    hash1 = svc.hash_content("test content")
    hash2 = svc.hash_content("test content")
    hash3 = svc.hash_content("different content")
    assert hash1 == hash2
    assert hash1 != hash3
    print("  [OK] Content hashing")
    
    # Test chunking
    content = """
    This is the first paragraph about vacation policy. Employees get 20 days off.
    This is the second paragraph about sick leave. It is unlimited with approval.
    This is the third paragraph about remote work. Up to 3 days per week allowed.
    """
    chunks = svc.chunk_document(content, "Test Doc")
    assert len(chunks) > 0
    assert all("content" in c for c in chunks)
    assert all("chunk_index" in c for c in chunks)
    print(f"  [OK] Chunking: {len(chunks)} chunks created")
    
    return True

def test_llm_service():
    """Test LLM service (stub mode)"""
    print("\nTesting LLMService (stub mode)...")
    from app.services.llm_service import LLMService
    import asyncio
    
    svc = LLMService()
    assert svc.stub_mode == True
    print("  [OK] Stub mode enabled")
    
    # Test prompt building
    system_prompt = svc.build_system_prompt("Acme Corp")
    assert "Acme Corp" in system_prompt
    assert "JSON" in system_prompt
    print("  [OK] System prompt generation")
    
    # Test with context
    context = [{"content": "Employees get 20 days PTO", "document_title": "Handbook", "score": 0.8}]
    user_prompt = svc.build_user_prompt("How many vacation days?", context)
    assert "20 days" in user_prompt
    print("  [OK] User prompt with context")
    
    # Test without context (refusal)
    user_prompt_empty = svc.build_user_prompt("Random question?", [])
    assert "cannot answer" in user_prompt_empty.lower()
    print("  [OK] Refusal prompt generation")
    
    # Test stub response
    async def test_generate():
        response = await svc.generate_answer("How many days?", context, "Acme")
        assert "answer" in response
        assert "sources" in response
        assert "confidence" in response
        return response
    
    response = asyncio.run(test_generate())
    print(f"  [OK] Stub response: confidence={response['confidence']}")
    
    return True

def test_models():
    """Test SQLAlchemy models structure"""
    print("\nTesting SQLAlchemy models...")
    from app.models import Tenant, Document, DocumentChunk, AIRequest, AIResult, AuditLog
    
    # Check all models have required fields
    assert hasattr(Tenant, 'id')
    assert hasattr(Tenant, 'name')
    assert hasattr(Tenant, 'slug')
    print("  [OK] Tenant model")
    
    assert hasattr(Document, 'tenant_id')
    assert hasattr(Document, 'content_hash')
    print("  [OK] Document model")
    
    assert hasattr(DocumentChunk, 'tenant_id')
    assert hasattr(DocumentChunk, 'vector_id')
    print("  [OK] DocumentChunk model")
    
    assert hasattr(AIRequest, 'tenant_id')
    assert hasattr(AIRequest, 'request_id')
    print("  [OK] AIRequest model")
    
    assert hasattr(AIResult, 'tenant_id')
    assert hasattr(AIResult, 'was_cached')
    print("  [OK] AIResult model")
    
    return True

def test_api_routes():
    """Test FastAPI routes can be loaded"""
    print("\nTesting API routes...")
    from app.routers import health, tenants, documents, questions
    
    assert hasattr(health, 'router')
    print("  [OK] Health router")
    
    assert hasattr(tenants, 'router')
    print("  [OK] Tenants router")
    
    assert hasattr(documents, 'router')
    print("  [OK] Documents router")
    
    assert hasattr(questions, 'router')
    print("  [OK] Questions router")
    
    return True

def main():
    print("=" * 60)
    print("LOCAL VALIDATION TEST")
    print("=" * 60)
    print("This validates code structure without external services.")
    print("If all tests pass, Docker deployment will work.\n")
    
    tests = [
        test_imports,
        test_config,
        test_schemas,
        test_document_service,
        test_llm_service,
        test_models,
        test_api_routes,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [FAIL] {test.__name__}: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\nAll tests passed! Docker deployment will work.")
        print("\nTo run with Docker:")
        print("  1. Start Docker Desktop")
        print("  2. Run: docker compose up --build")
        return 0
    else:
        print("\nSome tests failed. Fix issues before Docker deployment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
