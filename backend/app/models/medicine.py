from sqlalchemy import (
    Column, Integer, String, Numeric, Date,
    DateTime, ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Medicine(Base):
    __tablename__ = "medicines"
    __table_args__ = (
        CheckConstraint(
            "status IN ('Active', 'Low Stock', 'Expired', 'Out of Stock')",
            name="ck_medicine_status"
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    generic_name = Column(String(200), nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    batch_no = Column(String(100), nullable=False)
    expiry_date = Column(Date, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    cost_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    supplier = Column(String(200), nullable=True)
    status = Column(String(20), nullable=False, default="Active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    category = relationship("Category", backref="medicines")
    sale_items = relationship("SaleItem", back_populates="medicine")
