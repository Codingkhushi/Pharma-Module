from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.medicine import Medicine
from app.schemas.medicine import (
    MedicineCreate, MedicineUpdate, MedicineOut,
    MedicineListOut, MedicineStatusUpdate, InventorySummaryOut
)
from app.services.medicine_service import apply_status

router = APIRouter(prefix="/api/medicines", tags=["medicines"])


@router.get("/summary", response_model=InventorySummaryOut)
def get_inventory_summary(db: Session = Depends(get_db)):
    medicines = db.query(Medicine).all()
    total_value = sum(Decimal(str(m.quantity)) * m.mrp for m in medicines)
    return InventorySummaryOut(
        total_items=len(medicines),
        active_stock=sum(1 for m in medicines if m.status == "Active"),
        low_stock=sum(1 for m in medicines if m.status == "Low Stock"),
        out_of_stock=sum(1 for m in medicines if m.status == "Out of Stock"),
        expired=sum(1 for m in medicines if m.status == "Expired"),
        total_value=total_value,
    )


@router.get("", response_model=MedicineListOut)
def list_medicines(
    search: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Medicine)
    if search:
        like = f"%{search}%"
        query = query.filter(
            Medicine.name.ilike(like) | Medicine.generic_name.ilike(like)
        )
    if category_id:
        query = query.filter(Medicine.category_id == category_id)
    if status:
        query = query.filter(Medicine.status == status)

    total = query.count()
    medicines = query.offset((page - 1) * limit).limit(limit).all()
    return MedicineListOut(total=total, page=page, limit=limit, medicines=medicines)


@router.get("/{medicine_id}", response_model=MedicineOut)
def get_medicine(medicine_id: int, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    return medicine


@router.post("", response_model=MedicineOut, status_code=status.HTTP_201_CREATED)
def create_medicine(payload: MedicineCreate, db: Session = Depends(get_db)):
    medicine = Medicine(**payload.model_dump())
    apply_status(medicine)
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.put("/{medicine_id}", response_model=MedicineOut)
def update_medicine(medicine_id: int, payload: MedicineUpdate, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    for field, value in payload.model_dump().items():
        setattr(medicine, field, value)
    apply_status(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine


@router.patch("/{medicine_id}/status", response_model=MedicineOut)
def update_medicine_status(medicine_id: int, payload: MedicineStatusUpdate, db: Session = Depends(get_db)):
    medicine = db.query(Medicine).filter(Medicine.id == medicine_id).first()
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found")
    medicine.status = payload.status
    db.commit()
    db.refresh(medicine)
    return medicine
