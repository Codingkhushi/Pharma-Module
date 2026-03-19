from datetime import date
from sqlalchemy.orm import Session
from app.models.medicine import Medicine
from app.config import settings

LOW_STOCK_THRESHOLD = settings.LOW_STOCK_THRESHOLD


def derive_status(medicine: Medicine) -> str:
    """
    Derive the correct status for a medicine based on priority rules.

    Priority order (highest to lowest):
      1. Expired  — expiry_date is in the past, regardless of quantity
      2. Out of Stock — quantity is exactly 0
      3. Low Stock — quantity is above 0 but below LOW_STOCK_THRESHOLD
      4. Active   — quantity >= threshold and not expired

    This function is the ONLY place status logic lives.
    Called on every write (add, update) and by the daily scheduler.
    """
    today = date.today()

    if medicine.expiry_date < today:
        return "Expired"

    if medicine.quantity == 0:
        return "Out of Stock"

    if medicine.quantity < LOW_STOCK_THRESHOLD:
        return "Low Stock"

    return "Active"


def apply_status(medicine: Medicine) -> Medicine:
    """
    Derive and write status back onto the medicine object.
    Does NOT commit — caller is responsible for the transaction.
    """
    medicine.status = derive_status(medicine)
    return medicine


def run_daily_expiry_scan(db: Session) -> dict:
    """
    Called by APScheduler at 00:05 daily.
    Scans every medicine, recalculates status, updates only changed rows.
    Wraps everything in a single transaction — all or nothing.
    Returns a summary dict for logging.
    """
    updated = 0
    errors = 0

    try:
        medicines = db.query(Medicine).all()

        for medicine in medicines:
            new_status = derive_status(medicine)
            if new_status != medicine.status:
                medicine.status = new_status
                updated += 1

        db.commit()

    except Exception as e:
        db.rollback()
        errors += 1
        # In production you'd log to a proper logger
        print(f"[SCHEDULER ERROR] daily_expiry_scan failed: {e}")

    return {"scanned": len(medicines) if "medicines" in dir() else 0, "updated": updated, "errors": errors}
