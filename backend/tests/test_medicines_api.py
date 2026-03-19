"""
Integration tests for /api/medicines endpoints.
Uses the test client + in-memory SQLite DB.
"""
import pytest
from datetime import date, timedelta


VALID_MEDICINE = {
    "name": "Metformin 500mg",
    "generic_name": "Metformin HCl",
    "batch_no": "MET-2024-001",
    "expiry_date": str(date.today() + timedelta(days=400)),
    "quantity": 100,
    "cost_price": 18.0,
    "mrp": 35.0,
    "supplier": "PharmaCo",
}


class TestCreateMedicine:

    def test_create_returns_201(self, client):
        res = client.post("/api/medicines", json=VALID_MEDICINE)
        assert res.status_code == 201

    def test_create_returns_medicine_object(self, client):
        res = client.post("/api/medicines", json=VALID_MEDICINE)
        data = res.json()
        assert data["name"] == "Metformin 500mg"
        assert data["batch_no"] == "MET-2024-001"

    def test_create_auto_derives_active_status(self, client):
        """Backend must set status automatically — client never sends status."""
        res = client.post("/api/medicines", json=VALID_MEDICINE)
        assert res.json()["status"] == "Active"

    def test_create_derives_low_stock_status(self, client):
        payload = {**VALID_MEDICINE, "quantity": 5, "batch_no": "LOW-001"}
        res = client.post("/api/medicines", json=payload)
        assert res.json()["status"] == "Low Stock"

    def test_create_derives_out_of_stock_status(self, client):
        payload = {**VALID_MEDICINE, "quantity": 0, "batch_no": "OOS-001"}
        res = client.post("/api/medicines", json=payload)
        assert res.json()["status"] == "Out of Stock"

    def test_create_derives_expired_status(self, client):
        payload = {
            **VALID_MEDICINE,
            "expiry_date": str(date.today() - timedelta(days=1)),
            "batch_no": "EXP-001",
        }
        res = client.post("/api/medicines", json=payload)
        assert res.json()["status"] == "Expired"

    def test_negative_quantity_rejected(self, client):
        payload = {**VALID_MEDICINE, "quantity": -1}
        res = client.post("/api/medicines", json=payload)
        assert res.status_code == 422

    def test_zero_mrp_rejected(self, client):
        payload = {**VALID_MEDICINE, "mrp": 0}
        res = client.post("/api/medicines", json=payload)
        assert res.status_code == 422


class TestListMedicines:

    def test_list_returns_paginated(self, seeded_client):
        res = seeded_client.get("/api/medicines")
        assert res.status_code == 200
        data = res.json()
        assert "medicines" in data
        assert "total" in data
        assert data["total"] == 3

    def test_filter_by_status_active(self, seeded_client):
        res = seeded_client.get("/api/medicines?status=Active")
        data = res.json()
        assert all(m["status"] == "Active" for m in data["medicines"])

    def test_filter_by_status_expired(self, seeded_client):
        res = seeded_client.get("/api/medicines?status=Expired")
        data = res.json()
        assert all(m["status"] == "Expired" for m in data["medicines"])

    def test_search_by_name(self, seeded_client):
        res = seeded_client.get("/api/medicines?search=Paracetamol")
        data = res.json()
        assert data["total"] == 1
        assert data["medicines"][0]["name"] == "Paracetamol 500mg"

    def test_search_case_insensitive(self, seeded_client):
        res = seeded_client.get("/api/medicines?search=paracetamol")
        assert res.json()["total"] == 1

    def test_pagination(self, seeded_client):
        res = seeded_client.get("/api/medicines?page=1&limit=2")
        data = res.json()
        assert len(data["medicines"]) == 2
        assert data["total"] == 3


class TestUpdateMedicine:

    def test_update_recalculates_status(self, seeded_client):
        """Updating quantity to 0 must flip status to Out of Stock."""
        list_res = seeded_client.get("/api/medicines?search=Paracetamol")
        med = list_res.json()["medicines"][0]
        med_id = med["id"]

        payload = {
            "name": med["name"],
            "generic_name": med["generic_name"],
            "batch_no": med["batch_no"],
            "expiry_date": med["expiry_date"],
            "quantity": 0,  # depleted
            "cost_price": float(med["cost_price"]),
            "mrp": float(med["mrp"]),
            "supplier": med["supplier"],
        }
        res = seeded_client.put(f"/api/medicines/{med_id}", json=payload)
        assert res.status_code == 200
        assert res.json()["status"] == "Out of Stock"

    def test_update_nonexistent_returns_404(self, client):
        payload = {**VALID_MEDICINE}
        res = client.put("/api/medicines/9999", json=payload)
        assert res.status_code == 404


class TestMedicineStatusPatch:

    def test_manual_status_override(self, seeded_client):
        list_res = seeded_client.get("/api/medicines?search=Paracetamol")
        med_id = list_res.json()["medicines"][0]["id"]
        res = seeded_client.patch(f"/api/medicines/{med_id}/status", json={"status": "Expired"})
        assert res.status_code == 200
        assert res.json()["status"] == "Expired"

    def test_invalid_status_rejected(self, seeded_client):
        list_res = seeded_client.get("/api/medicines?search=Paracetamol")
        med_id = list_res.json()["medicines"][0]["id"]
        res = seeded_client.patch(f"/api/medicines/{med_id}/status", json={"status": "Broken"})
        assert res.status_code == 422