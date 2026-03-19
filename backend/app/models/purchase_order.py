from sqlalchemy import (
    Column, Integer, String, DateTime,
    CheckConstraint, func
)
from app.db.session import Base


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Pending', 'Completed')",
            name="ck_purchase_order_status"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    supplier_name = Column(String(200), nullable=False)
    status = Column(String(20), nullable=False, default="Pending")
    order_date = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
