"""
Integration tests for POST /api/sales — ACID transaction behavior.
These are the most important tests in the suite.
"""
import pytest
from datetime import date, timedelta
from app.models.category import Category
from app.models.medicine import Medicine
from app.services.medicine_service import apply_status


@pytest.fixture()
def sale_client(client, db):
    """Client seeded specifically for sale tests."""
    today = date.today()

    cat = Category(name="Analgesic")
    db.add(cat)
    db.flush()

    medicines = [
        Medicine(name="Paracetamol 500mg", batch_no="PCM-001",
                 category_id=cat.id, generic_name="Acetaminophen",
                 expiry_date=today + timedelta(days=365),
                 quantity=50, cost_price=12, mrp=25, supplier="MedCo"),
        Medicine(name="Omeprazole 20mg", batch_no="OMP-001",
                 category_id=cat.id, generic_name="Omeprazole",
                 expiry_date=today + timedelta(days=180),
                 quantity=5, cost_price=55, mrp=95, supplier="HealthCo"),
        Medicine(name="Aspirin 75mg", batch_no="ASP-001",
                 category_id=cat.id, generic_name="Aspirin",
                 expiry_date=today - timedelta(days=10),  # Expired
                 quantity=300, cost_price=20, mrp=45, supplier="GreenMed"),
    ]
    for m in medicines:
        apply_status(m)
        db.add(m)
    db.commit()

    return client, db


class TestRecordSale:

    def test_sale_returns_201(self, sale_client):
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        res = client.post("/api/sales", json={
            "patient_name": "Test Patient",
            "payment_mode": "Cash",
            "items": [{"medicine_id": med.id, "quantity_sold": 5}],
        })
        assert res.status_code == 201

    def test_sale_decrements_quantity(self, sale_client):
        """Core ACID check — quantity must drop by exactly quantity_sold."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        original_qty = med.quantity  # 50

        client.post("/api/sales", json={
            "patient_name": "Test Patient",
            "payment_mode": "Cash",
            "items": [{"medicine_id": med.id, "quantity_sold": 10}],
        })

        db.refresh(med)
        assert med.quantity == original_qty - 10  # must be 40

    def test_sale_snapshots_price_at_sale(self, sale_client):
        """price_at_sale must equal mrp at time of sale, not whatever mrp is later."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        original_mrp = float(med.mrp)  # 25.0

        res = client.post("/api/sales", json={
            "patient_name": "Price Test",
            "payment_mode": "UPI",
            "items": [{"medicine_id": med.id, "quantity_sold": 2}],
        })
        sale_data = res.json()
        assert float(sale_data["items"][0]["price_at_sale"]) == original_mrp

    def test_sale_generates_invoice_number(self, sale_client):
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        res = client.post("/api/sales", json={
            "patient_name": "Invoice Test",
            "payment_mode": "Card",
            "items": [{"medicine_id": med.id, "quantity_sold": 1}],
        })
        invoice_no = res.json()["invoice_no"]
        assert invoice_no.startswith("INV-")

    def test_sale_updates_status_after_depletion(self, sale_client):
        """After selling all stock, medicine status must flip to Out of Stock."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="OMP-001").first()
        assert med.quantity == 5  # confirm starting qty

        client.post("/api/sales", json={
            "patient_name": "Deplete Test",
            "payment_mode": "Cash",
            "items": [{"medicine_id": med.id, "quantity_sold": 5}],  # sell all 5
        })

        db.refresh(med)
        assert med.quantity == 0
        assert med.status == "Out of Stock"

    def test_sale_updates_status_to_low_stock(self, sale_client):
        """Selling down to below threshold must flip status to Low Stock."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        assert med.quantity == 50  # Active

        client.post("/api/sales", json={
            "patient_name": "Low Stock Test",
            "payment_mode": "Cash",
            "items": [{"medicine_id": med.id, "quantity_sold": 35}],  # leaves 15
        })

        db.refresh(med)
        assert med.quantity == 15
        assert med.status == "Low Stock"

    def test_sale_total_computed_correctly(self, sale_client):
        """total = SUM(quantity_sold × price_at_sale)."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        qty = 3
        expected_total = float(med.mrp) * qty  # 25 × 3 = 75

        res = client.post("/api/sales", json={
            "patient_name": "Total Test",
            "payment_mode": "UPI",
            "items": [{"medicine_id": med.id, "quantity_sold": qty}],
        })
        assert float(res.json()["total"]) == expected_total


class TestSaleValidation:

    def test_insufficient_stock_rejected(self, sale_client):
        """Selling more than available quantity must return 400."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()

        res = client.post("/api/sales", json={
            "patient_name": "Over Stock",
            "payment_mode": "Cash",
            "items": [{"medicine_id": med.id, "quantity_sold": 9999}],
        })
        assert res.status_code == 400

    def test_expired_medicine_cannot_be_sold(self, sale_client):
        """Selling an expired medicine must return 400."""
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="ASP-001").first()
        assert med.status == "Expired"

        res = client.post("/api/sales", json={
            "patient_name": "Expired Test",
            "payment_mode": "Cash",
            "items": [{"medicine_id": med.id, "quantity_sold": 1}],
        })
        assert res.status_code == 400

    def test_nonexistent_medicine_rejected(self, sale_client):
        client, _ = sale_client
        res = client.post("/api/sales", json={
            "patient_name": "Ghost",
            "payment_mode": "Cash",
            "items": [{"medicine_id": 99999, "quantity_sold": 1}],
        })
        assert res.status_code == 404

    def test_empty_items_rejected(self, sale_client):
        client, _ = sale_client
        res = client.post("/api/sales", json={
            "patient_name": "Empty",
            "payment_mode": "Cash",
            "items": [],
        })
        assert res.status_code == 422

    def test_invalid_payment_mode_rejected(self, sale_client):
        client, db = sale_client
        med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        res = client.post("/api/sales", json={
            "patient_name": "Bad Payment",
            "payment_mode": "Bitcoin",
            "items": [{"medicine_id": med.id, "quantity_sold": 1}],
        })
        assert res.status_code == 422

    def test_rollback_on_failure_leaves_stock_intact(self, sale_client):
        """
        If one item in a multi-item sale fails,
        the whole transaction must roll back — no stock decremented.
        """
        client, db = sale_client
        good_med = db.query(Medicine).filter_by(batch_no="PCM-001").first()
        original_qty = good_med.quantity

        # Second item references a non-existent medicine — will fail mid-transaction
        res = client.post("/api/sales", json={
            "patient_name": "Rollback Test",
            "payment_mode": "Cash",
            "items": [
                {"medicine_id": good_med.id,  "quantity_sold": 5},
                {"medicine_id": 99999,         "quantity_sold": 1},  # will 404
            ],
        })
        assert res.status_code == 404

        # Good medicine's quantity must be UNCHANGED — transaction rolled back
        db.refresh(good_med)
        assert good_med.quantity == original_qty