from datetime import date, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import func, cast, Date
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.sale import Sale, SaleItem
from app.models.medicine import Medicine
from app.models.purchase_order import PurchaseOrder
from app.schemas.dashboard import (
    SalesSummaryOut, ItemsSoldOut,
    LowStockOut, LowStockItemOut, PurchaseOrderSummaryOut
)
from app.schemas.sale import RecentSaleOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/sales-summary", response_model=SalesSummaryOut)
def get_sales_summary(db: Session = Depends(get_db)):
    today = date.today()
    yesterday = today - timedelta(days=1)

    def day_total(d: date) -> Decimal:
        result = (
            db.query(func.coalesce(func.sum(SaleItem.quantity_sold * SaleItem.price_at_sale), 0))
            .join(Sale, Sale.id == SaleItem.sale_id)
            .filter(cast(Sale.sale_date, Date) == d)
            .scalar()
        )
        return Decimal(str(result))

    today_total = day_total(today)
    yesterday_total = day_total(yesterday)

    if yesterday_total == 0:
        percent_change = 100.0 if today_total > 0 else 0.0
    else:
        percent_change = float((today_total - yesterday_total) / yesterday_total * 100)

    return SalesSummaryOut(
        today_total=today_total,
        yesterday_total=yesterday_total,
        percent_change=round(percent_change, 1),
    )


@router.get("/items-sold", response_model=ItemsSoldOut)
def get_items_sold(db: Session = Depends(get_db)):
    today = date.today()
    result = (
        db.query(func.coalesce(func.sum(SaleItem.quantity_sold), 0))
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(cast(Sale.sale_date, Date) == today)
        .scalar()
    )
    return ItemsSoldOut(items_sold_today=int(result))


@router.get("/low-stock", response_model=LowStockOut)
def get_low_stock(db: Session = Depends(get_db)):
    items = (
        db.query(Medicine)
        .filter(Medicine.status.in_(["Low Stock", "Out of Stock"]))
        .order_by(Medicine.quantity.asc())
        .all()
    )
    return LowStockOut(
        low_stock_count=len(items),
        items=[LowStockItemOut(id=m.id, name=m.name, quantity=m.quantity, status=m.status) for m in items],
    )


@router.get("/purchase-orders", response_model=PurchaseOrderSummaryOut)
def get_purchase_order_summary(db: Session = Depends(get_db)):
    pending = db.query(PurchaseOrder).filter(PurchaseOrder.status == "Pending").count()
    completed = db.query(PurchaseOrder).filter(PurchaseOrder.status == "Completed").count()
    return PurchaseOrderSummaryOut(pending_count=pending, completed_count=completed)


@router.get("/recent-sales", response_model=list[RecentSaleOut])
def get_recent_sales(db: Session = Depends(get_db)):
    sales = db.query(Sale).order_by(Sale.sale_date.desc()).limit(10).all()
    result = []
    for sale in sales:
        total = sum(item.quantity_sold * item.price_at_sale for item in sale.items)
        result.append(RecentSaleOut(
            id=sale.id,
            invoice_no=sale.invoice_no,
            patient_name=sale.patient_name,
            item_count=len(sale.items),
            total=total,
            payment_mode=sale.payment_mode,
            sale_date=sale.sale_date,
        ))
    return result
