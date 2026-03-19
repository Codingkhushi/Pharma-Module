from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, field_validator


class MedicineBase(BaseModel):
    name: str
    generic_name: Optional[str] = None
    category_id: Optional[int] = None
    batch_no: str
    expiry_date: date
    quantity: int
    cost_price: Decimal
    mrp: Decimal
    supplier: Optional[str] = None

    @field_validator("quantity")
    @classmethod
    def quantity_non_negative(cls, v):
        if v < 0:
            raise ValueError("quantity cannot be negative")
        return v

    @field_validator("mrp", "cost_price")
    @classmethod
    def price_positive(cls, v):
        if v <= 0:
            raise ValueError("price must be positive")
        return v


class MedicineCreate(MedicineBase):
    pass


class MedicineUpdate(MedicineBase):
    pass


class MedicineStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v):
        allowed = {"Active", "Low Stock", "Expired", "Out of Stock"}
        if v not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v


class CategoryOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}


class MedicineOut(BaseModel):
    id: int
    name: str
    generic_name: Optional[str]
    category: Optional[CategoryOut]
    batch_no: str
    expiry_date: date
    quantity: int
    cost_price: Decimal
    mrp: Decimal
    supplier: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class MedicineListOut(BaseModel):
    total: int
    page: int
    limit: int
    medicines: list[MedicineOut]


class InventorySummaryOut(BaseModel):
    total_items: int
    active_stock: int
    low_stock: int
    out_of_stock: int
    expired: int
    total_value: Decimal
