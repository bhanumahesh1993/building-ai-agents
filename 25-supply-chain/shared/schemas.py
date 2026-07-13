# shared/schemas.py
from __future__ import annotations

from pydantic import BaseModel


class ReorderRequest(BaseModel):
    """What Northwind sends across the boundary."""
    sku: str
    quantity: int
    spend_cap: float
    buyer_org: str


class SupplierQuote(BaseModel):
    """One candidate quote, internal to ProcureIQ."""
    supplier: str
    unit_price: float
    lead_time_days: int
    moq: int


class PurchaseOrder(BaseModel):
    """What crosses back as the completed artifact."""
    po_number: str
    supplier: str
    sku: str
    quantity: int
    unit_price: float
    total: float
    lead_time_days: int
