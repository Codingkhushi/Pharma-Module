"""
Run once to create tables and seed initial data.
  python -m app.db.init_db
"""
from datetime import date, timedelta
from app.db.session import engine, SessionLocal, Base

# Import all models so Base knows about them before create_all
from app.models.category import Category
from app.models.medicine import Medicine
from app.models.sale import Sale, SaleItem
from app.models.purchase_order import PurchaseOrder


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")


def seed_categories(db) -> dict:
    names = [
        "Analgesic", "Antibiotic", "Antiviral", "Cardiovascular",
        "Gastric", "Anticoagulant", "Dermatology", "Respiratory",
        "Diabetes", "Vitamins & Supplements"
    ]
    cat_map = {}
    for name in names:
        existing = db.query(Category).filter(Category.name == name).first()
        if not existing:
            cat = Category(name=name)
            db.add(cat)
            db.flush()
            cat_map[name] = cat
        else:
            cat_map[name] = existing
    db.commit()
    print(f"✓ Seeded {len(names)} categories")
    return cat_map


def seed_medicines(db, cat_map: dict):
    today = date.today()
    medicines_data = [
        {
            "name": "Paracetamol 500mg",
            "generic_name": "Acetaminophen",
            "category_id": cat_map["Analgesic"].id,
            "batch_no": "PCM-2024-0892",
            "expiry_date": today + timedelta(days=365),
            "quantity": 500,
            "cost_price": 12.00,
            "mrp": 25.00,
            "supplier": "MedSupply Co.",
        },
        {
            "name": "Omeprazole 20mg Capsule",
            "generic_name": "Omeprazole",
            "category_id": cat_map["Gastric"].id,
            "batch_no": "OMP-2024-5873",
            "expiry_date": today + timedelta(days=180),
            "quantity": 15,  # Low Stock
            "cost_price": 55.00,
            "mrp": 95.75,
            "supplier": "HealthCare Ltd.",
        },
        {
            "name": "Aspirin 75mg",
            "generic_name": "Aspirin",
            "category_id": cat_map["Anticoagulant"].id,
            "batch_no": "ASP-2023-3421",
            "expiry_date": today - timedelta(days=30),  # Expired
            "quantity": 300,
            "cost_price": 20.00,
            "mrp": 45.00,
            "supplier": "GreenMed",
        },
        {
            "name": "Atorvastatin 10mg",
            "generic_name": "Atorvastatin Besylate",
            "category_id": cat_map["Cardiovascular"].id,
            "batch_no": "AME-2024-0945",
            "expiry_date": today + timedelta(days=300),
            "quantity": 0,  # Out of Stock
            "cost_price": 100.00,
            "mrp": 195.00,
            "supplier": "PharmaCorp",
        },
        {
            "name": "Amoxicillin 500mg",
            "generic_name": "Amoxicillin",
            "category_id": cat_map["Antibiotic"].id,
            "batch_no": "AMX-2024-1122",
            "expiry_date": today + timedelta(days=400),
            "quantity": 250,
            "cost_price": 45.00,
            "mrp": 85.00,
            "supplier": "MedSupply Co.",
        },
        {
            "name": "Metformin 500mg",
            "generic_name": "Metformin HCl",
            "category_id": cat_map["Diabetes"].id,
            "batch_no": "MET-2024-3310",
            "expiry_date": today + timedelta(days=500),
            "quantity": 120,
            "cost_price": 18.00,
            "mrp": 35.00,
            "supplier": "HealthCare Ltd.",
        },
    ]

    from app.services.medicine_service import apply_status
    for data in medicines_data:
        existing = db.query(Medicine).filter(Medicine.batch_no == data["batch_no"]).first()
        if not existing:
            med = Medicine(**data)
            apply_status(med)  # derive correct status before insert
            db.add(med)

    db.commit()
    print(f"✓ Seeded {len(medicines_data)} medicines")


def seed_purchase_orders(db):
    orders = [
        {"supplier_name": "MedSupply Co.", "status": "Pending"},
        {"supplier_name": "HealthCare Ltd.", "status": "Pending"},
        {"supplier_name": "GreenMed", "status": "Completed"},
        {"supplier_name": "PharmaCorp", "status": "Pending"},
        {"supplier_name": "MedSupply Co.", "status": "Pending"},
    ]
    if db.query(PurchaseOrder).count() == 0:
        for o in orders:
            db.add(PurchaseOrder(**o))
        db.commit()
        print(f"✓ Seeded {len(orders)} purchase orders")


def seed_sales(db):
    """Seed a few sample sales so the dashboard shows data immediately."""
    if db.query(Sale).count() > 0:
        return

    from decimal import Decimal
    meds = db.query(Medicine).all()
    if not meds:
        return

    # Pick active medicines for the sample sales
    active = [m for m in meds if m.status == "Active" and m.quantity >= 5]
    if len(active) < 2:
        return

    sales_data = [
        {
            "invoice_no": "INV-2024-0001",
            "patient_name": "Rajesh Kumar",
            "payment_mode": "Card",
            "items": [(active[0], 3)],
        },
        {
            "invoice_no": "INV-2024-0002",
            "patient_name": "Sarah Smith",
            "payment_mode": "Cash",
            "items": [(active[1], 2)],
        },
        {
            "invoice_no": "INV-2024-0003",
            "patient_name": "Michael Johnson",
            "payment_mode": "UPI",
            "items": [(active[0], 2), (active[1], 3)],
        },
    ]

    for s in sales_data:
        sale = Sale(
            invoice_no=s["invoice_no"],
            patient_name=s["patient_name"],
            payment_mode=s["payment_mode"],
        )
        db.add(sale)
        db.flush()
        for med, qty in s["items"]:
            db.add(SaleItem(
                sale_id=sale.id,
                medicine_id=med.id,
                quantity_sold=qty,
                price_at_sale=med.mrp,
            ))
            med.quantity -= qty
        db.commit()

    print("✓ Seeded 3 sample sales")


def init_db():
    create_tables()
    db = SessionLocal()
    try:
        cat_map = seed_categories(db)
        seed_medicines(db, cat_map)
        seed_purchase_orders(db)
        seed_sales(db)
        print("\n✅ Database initialized successfully")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
