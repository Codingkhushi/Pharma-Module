"""
Integration tests for dashboard and purchase order endpoints.
"""
import pytest


class TestDashboardEndpoints:

    def test_sales_summary_returns_correct_shape(self, client):
        res = client.get("/api/dashboard/sales-summary")
        assert res.status_code == 200
        data = res.json()
        assert "today_total" in data
        assert "yesterday_total" in data
        assert "percent_change" in data

    def test_sales_summary_zero_when_no_sales(self, client):
        res = client.get("/api/dashboard/sales-summary")
        data = res.json()
        assert float(data["today_total"]) == 0.0

    def test_items_sold_returns_correct_shape(self, client):
        res = client.get("/api/dashboard/items-sold")
        assert res.status_code == 200
        assert "items_sold_today" in res.json()

    def test_low_stock_returns_correct_shape(self, client):
        res = client.get("/api/dashboard/low-stock")
        assert res.status_code == 200
        data = res.json()
        assert "low_stock_count" in data
        assert "items" in data

    def test_low_stock_reflects_seeded_data(self, seeded_client):
        """Omeprazole (qty=10) should appear as Low Stock."""
        res = seeded_client.get("/api/dashboard/low-stock")
        data = res.json()
        names = [i["name"] for i in data["items"]]
        assert any("Omeprazole" in n for n in names)

    def test_purchase_orders_summary(self, seeded_client):
        res = seeded_client.get("/api/dashboard/purchase-orders")
        assert res.status_code == 200
        data = res.json()
        assert data["pending_count"] == 1
        assert data["completed_count"] == 1

    def test_recent_sales_returns_list(self, client):
        res = client.get("/api/dashboard/recent-sales")
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_inventory_summary_totals(self, seeded_client):
        res = seeded_client.get("/api/medicines/summary")
        assert res.status_code == 200
        data = res.json()
        assert data["total_items"] == 3
        assert "total_value" in data


class TestPurchaseOrders:

    def test_create_purchase_order(self, client):
        res = client.post("/api/purchase-orders", json={"supplier_name": "TestSupplier"})
        assert res.status_code == 201
        data = res.json()
        assert data["supplier_name"] == "TestSupplier"
        assert data["status"] == "Pending"

    def test_list_purchase_orders(self, seeded_client):
        res = seeded_client.get("/api/purchase-orders")
        assert res.status_code == 200
        assert len(res.json()) == 2

    def test_filter_by_status_pending(self, seeded_client):
        res = seeded_client.get("/api/purchase-orders?status=Pending")
        data = res.json()
        assert all(o["status"] == "Pending" for o in data)

    def test_update_status_to_completed(self, client):
        create = client.post("/api/purchase-orders", json={"supplier_name": "Supplier X"})
        po_id = create.json()["id"]

        res = client.patch(f"/api/purchase-orders/{po_id}/status", json={"status": "Completed"})
        assert res.status_code == 200
        assert res.json()["status"] == "Completed"

    def test_invalid_status_rejected(self, client):
        create = client.post("/api/purchase-orders", json={"supplier_name": "Supplier Y"})
        po_id = create.json()["id"]

        res = client.patch(f"/api/purchase-orders/{po_id}/status", json={"status": "Shipped"})
        assert res.status_code == 400

    def test_nonexistent_po_returns_404(self, client):
        res = client.patch("/api/purchase-orders/9999/status", json={"status": "Completed"})
        assert res.status_code == 404


class TestCategories:

    def test_list_categories_empty(self, client):
        res = client.get("/api/categories")
        assert res.status_code == 200
        assert res.json() == []

    def test_create_category(self, client):
        res = client.post("/api/categories", json={"name": "Analgesic"})
        assert res.status_code == 201
        assert res.json()["name"] == "Analgesic"

    def test_duplicate_category_rejected(self, client):
        client.post("/api/categories", json={"name": "Analgesic"})
        res = client.post("/api/categories", json={"name": "Analgesic"})
        assert res.status_code == 400

    def test_list_categories_after_create(self, client):
        client.post("/api/categories", json={"name": "Gastric"})
        client.post("/api/categories", json={"name": "Analgesic"})
        res = client.get("/api/categories")
        names = [c["name"] for c in res.json()]
        assert "Gastric" in names
        assert "Analgesic" in names