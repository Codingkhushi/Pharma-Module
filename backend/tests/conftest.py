"""
Shared pytest fixtures.
Uses a file-based SQLite DB (not in-memory) so the same connection is shared
between the test session, the FastAPI dependency override, and the db fixture.
Every test gets a fresh database via create_all/drop_all.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base, get_db
from app.main import app

# File-based SQLite — avoids the "different connection = different in-memory DB" problem
TEST_DATABASE_URL = "sqlite:///./test_pharmacy.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Keep a module-level session reference so db fixture and override share the same session
_test_db = None


def override_get_db():
    """FastAPI dependency override — yields the shared test session."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client():
    """FastAPI test client with fresh tables per test."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db(client):
    """DB session sharing the same engine as the client override."""
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture()
def seeded_client(client, db):
    """Client with a category + 3 medicines + 2 purchase orders pre-loaded."""
    from app.models.category import Category
    from app.models.medicine import Medicine
    from app.models.purchase_order import PurchaseOrder
    from app.services.medicine_service import apply_status
    from datetime import date, timedelta

    today = date.today()

    cat = Category(name="Analgesic")
    db.add(cat)
    db.flush()

    medicines = [
        Medicine(name="Paracetamol 500mg", generic_name="Acetaminophen",
                 category_id=cat.id, batch_no="PCM-001",
                 expiry_date=today + timedelta(days=365),
                 quantity=500, cost_price=12, mrp=25, supplier="MedCo"),
        Medicine(name="Omeprazole 20mg", generic_name="Omeprazole",
                 category_id=cat.id, batch_no="OMP-001",
                 expiry_date=today + timedelta(days=180),
                 quantity=10, cost_price=55, mrp=95, supplier="HealthCo"),
        Medicine(name="Aspirin 75mg", generic_name="Aspirin",
                 category_id=cat.id, batch_no="ASP-001",
                 expiry_date=today - timedelta(days=10),  # Expired
                 quantity=300, cost_price=20, mrp=45, supplier="GreenMed"),
    ]
    for m in medicines:
        apply_status(m)
        db.add(m)

    db.add(PurchaseOrder(supplier_name="MedCo", status="Pending"))
    db.add(PurchaseOrder(supplier_name="HealthCo", status="Completed"))
    db.commit()

    return client