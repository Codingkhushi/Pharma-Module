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


# ── Purchase Orders ──────────────────────────────────────────────────────────

class PurchaseOrderCreate(BaseModel):
    supplier_name: str


class PurchaseOrderStatusUpdate(BaseModel):
    status: str

    def validate_status(cls, v):
        if v not in {"Pending", "Completed"}:
            raise ValueError("status must be Pending or Completed")
        return v


class PurchaseOrderOut(BaseModel):
    id: int
    supplier_name: str
    status: str
    order_date: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Categories ───────────────────────────────────────────────────────────────

class CategoryCreate(BaseModel):
    name: str


class CategoryOut(BaseModel):
    id: int
    name: str

    model_config = {"from_attributes": True}


# ── Reorder Suggestions ──────────────────────────────────────────────────────

class ReorderReason(BaseModel):
    type: str          # "out_of_stock" | "low_stock" | "expiring_soon"
    detail: str        # human-readable shown in UI


class ReorderSuggestionItem(BaseModel):
    id: int
    name: str
    supplier: str
    quantity: int
    status: str
    expiry_date: str
    reasons: list[ReorderReason]

    model_config = {"from_attributes": True}


class ReorderSuggestionGroup(BaseModel):
    supplier: str
    items: list[ReorderSuggestionItem]
    po_exists: bool    # True if a Pending PO for this supplier already exists


class ReorderSuggestionsOut(BaseModel):
    total_items: int
    groups: list[ReorderSuggestionGroup]