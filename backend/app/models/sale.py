from sqlalchemy import (
    Column, Integer, String, Numeric,
    DateTime, ForeignKey, func
)
from sqlalchemy.orm import relationship
from app.db.session import Base


class Sale(Base):
    __tablename__ = "sales"

    id = Column(Integer, primary_key=True, index=True)
    invoice_no = Column(String(50), nullable=False, unique=True, index=True)
    patient_name = Column(String(200), nullable=False)
    payment_mode = Column(String(50), nullable=False)
    sale_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id = Column(Integer, primary_key=True, index=True)
    sale_id = Column(Integer, ForeignKey("sales.id"), nullable=False)
    medicine_id = Column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity_sold = Column(Integer, nullable=False)
    price_at_sale = Column(Numeric(10, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    medicine = relationship("Medicine", back_populates="sale_items")
