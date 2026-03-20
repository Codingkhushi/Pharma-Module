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
    LowStockOut, LowStockItemOut, PurchaseOrderSummaryOut,
    ReorderSuggestionsOut, ReorderSuggestionItem, ReorderSuggestionGroup
)
from app.schemas.sale import RecentSaleOut

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/sales-summary", response_model=SalesSummaryOut)
def get_sales_summary(db: Session = Depends(get_db)):
    """Today's revenue vs yesterday with percent change."""
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
    """Total quantity of medicines sold today."""
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
    """Count and list of medicines needing attention."""
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
    """Count of pending and completed purchase orders."""
    pending = db.query(PurchaseOrder).filter(PurchaseOrder.status == "Pending").count()
    completed = db.query(PurchaseOrder).filter(PurchaseOrder.status == "Completed").count()
    return PurchaseOrderSummaryOut(pending_count=pending, completed_count=completed)


@router.get("/recent-sales", response_model=list[RecentSaleOut])
def get_recent_sales(db: Session = Depends(get_db)):
    """Last 10 sales with computed total."""
    sales = (
        db.query(Sale)
        .order_by(Sale.sale_date.desc())
        .limit(10)
        .all()
    )
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


@router.get("/reorder-suggestions", response_model=ReorderSuggestionsOut)
def get_reorder_suggestions(db: Session = Depends(get_db)):
    """
    Automatically surfaces medicines that need reordering, grouped by supplier.
    A medicine is flagged if ANY of these conditions are true:
      1. Out of Stock (quantity = 0)
      2. Low Stock (quantity < threshold, above zero)
      3. Expiring within 30 days AND still has stock (order replacement now)

    Also checks if a Pending PO already exists for each supplier,
    so the user knows whether to create a new one or top up an existing one.
    """
    today = date.today()
    expiry_window = today + timedelta(days=30)

    medicines = (
        db.query(Medicine)
        .filter(
            (Medicine.status == "Out of Stock") |
            (Medicine.status == "Low Stock")    |
            (
                (Medicine.expiry_date <= expiry_window) &
                (Medicine.expiry_date >= today) &
                (Medicine.quantity > 0)
            )
        )
        .order_by(Medicine.supplier, Medicine.name)
        .all()
    )

    # Find which suppliers already have a Pending PO
    from app.models.purchase_order import PurchaseOrder
    pending_suppliers = {
        po.supplier_name
        for po in db.query(PurchaseOrder)
        .filter(PurchaseOrder.status == "Pending")
        .all()
    }

    # Build reasons per medicine
    items_by_supplier: dict[str, list] = {}
    for med in medicines:
        reasons = []

        if med.status == "Out of Stock":
            reasons.append({"type": "out_of_stock", "detail": "No stock remaining"})

        if med.status == "Low Stock":
            reasons.append({
                "type": "low_stock",
                "detail": f"Only {med.quantity} units left (threshold: 20)"
            })

        days_to_expiry = (med.expiry_date - today).days
        if med.expiry_date <= expiry_window and med.expiry_date >= today and med.quantity > 0:
            reasons.append({
                "type": "expiring_soon",
                "detail": f"Expires in {days_to_expiry} day{'s' if days_to_expiry != 1 else ''} — order replacement stock"
            })

        if not reasons:
            continue

        supplier = med.supplier or "Unknown Supplier"
        if supplier not in items_by_supplier:
            items_by_supplier[supplier] = []

        items_by_supplier[supplier].append(ReorderSuggestionItem(
            id=med.id,
            name=med.name,
            supplier=supplier,
            quantity=med.quantity,
            status=med.status,
            expiry_date=str(med.expiry_date),
            reasons=reasons,
        ))

    groups = [
        ReorderSuggestionGroup(
            supplier=supplier,
            items=items,
            po_exists=supplier in pending_suppliers,
        )
        for supplier, items in items_by_supplier.items()
    ]

    return ReorderSuggestionsOut(
        total_items=sum(len(g.items) for g in groups),
        groups=groups,
    )