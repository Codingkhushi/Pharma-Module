
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator


class SaleItemCreate(BaseModel):
    medicine_id: int
    quantity_sold: int

    @field_validator("quantity_sold")
    @classmethod
    def qty_positive(cls, v):
        if v <= 0:
            raise ValueError("quantity_sold must be at least 1")
        return v


class SaleCreate(BaseModel):
    patient_name: str
    payment_mode: str
    items: list[SaleItemCreate]

    @field_validator("payment_mode")
    @classmethod
    def valid_payment(cls, v):
        allowed = {"Cash", "Card", "UPI"}
        if v not in allowed:
            raise ValueError(f"payment_mode must be one of {allowed}")
        return v

    @field_validator("items")
    @classmethod
    def items_non_empty(cls, v):
        if not v:
            raise ValueError("sale must have at least one item")
        return v


class SaleItemOut(BaseModel):
    id: int
    medicine_id: int
    medicine_name: str
    quantity_sold: int
    price_at_sale: Decimal
    subtotal: Decimal
    model_config = {"from_attributes": True}


class SaleOut(BaseModel):
    id: int
    invoice_no: str
    patient_name: str
    payment_mode: str
    sale_date: datetime
    total: Decimal
    items: list[SaleItemOut]
    model_config = {"from_attributes": True}


class RecentSaleOut(BaseModel):
    id: int
    invoice_no: str
    patient_name: str
    item_count: int
    total: Decimal
    payment_mode: str
    sale_date: datetime
    model_config = {"from_attributes": True}
