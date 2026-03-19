from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.models.purchase_order import PurchaseOrder
from app.models.category import Category
from app.schemas.dashboard import (
    PurchaseOrderCreate, PurchaseOrderStatusUpdate,
    PurchaseOrderOut, CategoryCreate, CategoryOut
)

po_router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


@po_router.get("", response_model=list[PurchaseOrderOut])
def list_purchase_orders(status: Optional[str] = Query(None), db: Session = Depends(get_db)):
    query = db.query(PurchaseOrder)
    if status:
        query = query.filter(PurchaseOrder.status == status)
    return query.order_by(PurchaseOrder.order_date.desc()).all()


@po_router.post("", response_model=PurchaseOrderOut, status_code=201)
def create_purchase_order(payload: PurchaseOrderCreate, db: Session = Depends(get_db)):
    po = PurchaseOrder(supplier_name=payload.supplier_name)
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


@po_router.patch("/{po_id}/status", response_model=PurchaseOrderOut)
def update_po_status(po_id: int, payload: PurchaseOrderStatusUpdate, db: Session = Depends(get_db)):
    if payload.status not in {"Pending", "Completed"}:
        raise HTTPException(status_code=400, detail="status must be Pending or Completed")
    po = db.query(PurchaseOrder).filter(PurchaseOrder.id == po_id).first()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = payload.status
    db.commit()
    db.refresh(po)
    return po


cat_router = APIRouter(prefix="/api/categories", tags=["categories"])


@cat_router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return db.query(Category).order_by(Category.name).all()


@cat_router.post("", response_model=CategoryOut, status_code=201)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    existing = db.query(Category).filter(Category.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    cat = Category(name=payload.name)
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat
