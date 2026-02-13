from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Tenant
from app.schemas import TenantCreate, TenantResponse

router = APIRouter()


@router.post("", response_model=TenantResponse)
def create_tenant(tenant: TenantCreate, db: Session = Depends(get_db)):
    """Create a new tenant"""
    # Check if slug already exists
    existing = db.query(Tenant).filter(Tenant.slug == tenant.slug).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tenant slug already exists")
    
    db_tenant = Tenant(name=tenant.name, slug=tenant.slug)
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)
    return db_tenant


@router.get("", response_model=List[TenantResponse])
def list_tenants(db: Session = Depends(get_db)):
    """List all tenants"""
    return db.query(Tenant).filter(Tenant.is_active == True).all()


@router.get("/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: int, db: Session = Depends(get_db)):
    """Get tenant by ID"""
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant
