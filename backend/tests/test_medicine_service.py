"""
Unit tests for derive_status().
These test pure logic — no DB, no HTTP, just the function.
"""
import pytest
from datetime import date, timedelta
from app.models.medicine import Medicine
from app.services.medicine_service import derive_status

today = date.today()
future = today + timedelta(days=100)
past   = today - timedelta(days=1)


class TestDeriveStatus:

    def test_expired_with_stock(self):
        """Expired beats everything — even if quantity is healthy."""
        m = Medicine(expiry_date=past, quantity=500)
        assert derive_status(m) == "Expired"

    def test_expired_with_low_stock(self):
        """Expired beats Low Stock."""
        m = Medicine(expiry_date=past, quantity=10)
        assert derive_status(m) == "Expired"

    def test_expired_with_zero_stock(self):
        """Expired beats Out of Stock."""
        m = Medicine(expiry_date=past, quantity=0)
        assert derive_status(m) == "Expired"

    def test_out_of_stock(self):
        """quantity=0, not expired → Out of Stock."""
        m = Medicine(expiry_date=future, quantity=0)
        assert derive_status(m) == "Out of Stock"

    def test_low_stock_boundary_lower(self):
        """quantity=1 → Low Stock."""
        m = Medicine(expiry_date=future, quantity=1)
        assert derive_status(m) == "Low Stock"

    def test_low_stock_boundary_upper(self):
        """quantity=19 → Low Stock (threshold is 20)."""
        m = Medicine(expiry_date=future, quantity=19)
        assert derive_status(m) == "Low Stock"

    def test_active_at_threshold(self):
        """quantity=20 exactly → Active (at or above threshold)."""
        m = Medicine(expiry_date=future, quantity=20)
        assert derive_status(m) == "Active"

    def test_active_healthy_stock(self):
        """quantity=500, valid expiry → Active."""
        m = Medicine(expiry_date=future, quantity=500)
        assert derive_status(m) == "Active"

    def test_expires_today_is_not_expired(self):
        """expiry_date = today is still valid (not strictly less than today)."""
        m = Medicine(expiry_date=today, quantity=100)
        assert derive_status(m) == "Active"

    def test_expires_tomorrow_is_active(self):
        """expiry_date = tomorrow → Active."""
        m = Medicine(expiry_date=today + timedelta(days=1), quantity=100)
        assert derive_status(m) == "Active"