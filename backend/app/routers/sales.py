from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.sale import Sale
from app.schemas.sale import SaleCreate, SaleOut, SaleItemOut
from app.services.sale_service import create_sale

router = APIRouter(prefix="/api/sales", tags=["sales"])


def _build_sale_out(sale: Sale) -> SaleOut:
    items = []
    total = Decimal("0")
    for item in sale.items:
        subtotal = item.quantity_sold * item.price_at_sale
        total += subtotal
        items.append(SaleItemOut(
            id=item.id,
            medicine_id=item.medicine_id,
            medicine_name=item.medicine.name,
            quantity_sold=item.quantity_sold,
            price_at_sale=item.price_at_sale,
            subtotal=subtotal,
        ))
    return SaleOut(
        id=sale.id,
        invoice_no=sale.invoice_no,
        patient_name=sale.patient_name,
        payment_mode=sale.payment_mode,
        sale_date=sale.sale_date,
        total=total,
        items=items,
    )


@router.post("", response_model=SaleOut, status_code=201)
def record_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    sale = create_sale(db, payload)
    return _build_sale_out(sale)


@router.get("/{sale_id}", response_model=SaleOut)
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = db.query(Sale).filter(Sale.id == sale_id).first()
    if not sale:
        raise HTTPException(status_code=404, detail="Sale not found")
    return _build_sale_out(sale)
