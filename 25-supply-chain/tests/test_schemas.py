# tests/test_schemas.py -- the cross-boundary task schema.
#
# shared/schemas.py is the contract the two independently-owned
# agents (inventory_agent @ Northwind, procurement_agent @
# ProcureIQ) exchange across the A2A trust boundary. These tests
# pin its shape: what's required, what's rejected, and that it
# round-trips through model_dump()/model_validate() the same way
# it does when serialized to JSON on the wire.
from __future__ import annotations

import pytest
from pydantic import ValidationError

from shared.schemas import (
    PurchaseOrder, ReorderRequest, SupplierQuote,
)


def test_reorder_request_round_trips():
    req = ReorderRequest(
        sku="GASKET-9", quantity=500,
        spend_cap=5000.0, buyer_org="northwind")
    dumped = req.model_dump()
    restored = ReorderRequest.model_validate(dumped)
    assert restored == req


@pytest.mark.parametrize("missing", [
    "sku", "quantity", "spend_cap", "buyer_org"])
def test_reorder_request_requires_every_field(missing):
    payload = {
        "sku": "GASKET-9", "quantity": 500,
        "spend_cap": 5000.0, "buyer_org": "northwind",
    }
    del payload[missing]
    with pytest.raises(ValidationError):
        ReorderRequest.model_validate(payload)


def test_reorder_request_rejects_wrong_types():
    with pytest.raises(ValidationError):
        ReorderRequest.model_validate({
            "sku": "GASKET-9", "quantity": "five hundred",
            "spend_cap": 5000.0, "buyer_org": "northwind",
        })


def test_supplier_quote_round_trips():
    quote = SupplierQuote(
        supplier="Anchor Fasteners Co.", unit_price=12.40,
        lead_time_days=9, moq=100)
    assert SupplierQuote.model_validate(
        quote.model_dump()) == quote


def test_purchase_order_round_trips():
    po = PurchaseOrder(
        po_number="PO-ABC123", supplier="Fastenal Direct",
        sku="GASKET-9", quantity=500, unit_price=13.10,
        total=6550.0, lead_time_days=5)
    dumped = po.model_dump()
    assert PurchaseOrder.model_validate(dumped) == po
    # These are the exact keys that cross the wire as the A2A
    # artifact's data part -- downstream code (extract_purchase_
    # order in a2a_client.py) depends on this shape.
    assert set(dumped) == {
        "po_number", "supplier", "sku", "quantity",
        "unit_price", "total", "lead_time_days",
    }


@pytest.mark.parametrize("missing", [
    "po_number", "supplier", "sku", "quantity",
    "unit_price", "total", "lead_time_days"])
def test_purchase_order_requires_every_field(missing):
    payload = {
        "po_number": "PO-ABC123", "supplier": "Fastenal Direct",
        "sku": "GASKET-9", "quantity": 500, "unit_price": 13.10,
        "total": 6550.0, "lead_time_days": 5,
    }
    del payload[missing]
    with pytest.raises(ValidationError):
        PurchaseOrder.model_validate(payload)
