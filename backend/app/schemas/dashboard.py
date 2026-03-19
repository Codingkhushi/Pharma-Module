from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


class SalesSummaryOut(BaseModel):
    today_total: Decimal
    yesterday_total: Decimal
    percent_change: float


class ItemsSoldOut(BaseModel):
    items_sold_today: int


class LowStockItemOut(BaseModel):
    id: int
    name: str
    quantity: int
    status: str
    model_config = {"from_attributes": True}


class LowStockOut(BaseModel):
    low_stock_count: int
    items: list[LowStockItemOut]


class PurchaseOrderSummaryOut(BaseModel):
    pending_count: int
    completed_count: int


class PurchaseOrderCreate(BaseModel):
    supplier_name: str


class PurchaseOrderStatusUpdate(BaseModel):
    status: str


class PurchaseOrderOut(BaseModel):
    id: int
    supplier_name: str
    status: str
    order_date: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str
    model_config = {"from_attributes": True}
