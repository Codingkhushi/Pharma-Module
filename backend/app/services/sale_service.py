from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from app.models.sale import Sale, SaleItem
from app.models.medicine import Medicine
from app.schemas.sale import SaleCreate
from app.services.medicine_service import apply_status


def generate_invoice_no(db: Session) -> str:
    """Generate sequential invoice number — INV-YYYY-XXXX."""
    year = datetime.now().year
    count = db.query(Sale).count() + 1
    return f"INV-{year}-{count:04d}"


def create_sale(db: Session, payload: SaleCreate) -> Sale:
    """
    Record a sale atomically.

    Within a single transaction:
      1. Validate all medicines exist and have sufficient stock
      2. INSERT into sales
      3. INSERT into sale_items (with price_at_sale snapshot)
      4. UPDATE medicines.quantity (decrement)
      5. derive_status() → UPDATE medicines.status
      6. COMMIT

    If any step raises, the except block rolls back everything.
    No partial state ever lands in the DB.
    """
    try:
        # ── Step 1: Validate all items before touching the DB ──────────────
        medicines_map: dict[int, Medicine] = {}
        for item in payload.items:
            medicine = db.query(Medicine).filter(Medicine.id == item.medicine_id).first()

            if not medicine:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Medicine id={item.medicine_id} not found"
                )
            if medicine.status == "Expired":
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"'{medicine.name}' is expired and cannot be sold"
                )
            if medicine.quantity < item.quantity_sold:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for '{medicine.name}'. "
                           f"Available: {medicine.quantity}, requested: {item.quantity_sold}"
                )
            medicines_map[item.medicine_id] = medicine

        # ── Step 2: INSERT sale ─────────────────────────────────────────────
        sale = Sale(
            invoice_no=generate_invoice_no(db),
            patient_name=payload.patient_name,
            payment_mode=payload.payment_mode,
        )
        db.add(sale)
        db.flush()  # get sale.id without committing

        # ── Step 3 + 4 + 5: INSERT sale_items, decrement qty, derive status ─
        for item in payload.items:
            medicine = medicines_map[item.medicine_id]

            # Snapshot price at moment of sale
            sale_item = SaleItem(
                sale_id=sale.id,
                medicine_id=item.medicine_id,
                quantity_sold=item.quantity_sold,
                price_at_sale=medicine.mrp,  # frozen — future mrp changes won't affect this
            )
            db.add(sale_item)

            # Decrement stock
            medicine.quantity -= item.quantity_sold

            # Recalculate status in the same transaction
            apply_status(medicine)

        # ── Step 6: COMMIT ──────────────────────────────────────────────────
        db.commit()
        db.refresh(sale)
        return sale

    except HTTPException:
        db.rollback()
        raise  # re-raise validation errors as-is

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Transaction failed and was rolled back: {str(e)}"
        )
