# tests/test_remote_output_validation.py -- remote-output
# validation.
#
# ProcureIQ is a separate, independently-owned agent. Its
# completed-task artifact crosses a trust boundary exactly like
# any other third-party API response: extract_purchase_order()
# must reject anything malformed or malicious rather than let it
# flow downstream untouched. This gives real teeth to
# evals/run_evals.py's eval_boundary_integrity(), which expects a
# validator that actually rejects a poisoned artifact.
from __future__ import annotations

import pytest

from a2a_client import (
    UntrustedRemoteOutputError, extract_purchase_order,
)
from shared.schemas import PurchaseOrder


def _task_with(data: dict) -> dict:
    return {
        "id": "task-1",
        "status": {"state": "completed"},
        "artifacts": [{"parts": [{"kind": "data", "data": data}]}],
    }


VALID_PO = {
    "po_number": "PO-ABC123", "supplier": "Fastenal Direct",
    "sku": "GASKET-9", "quantity": 500, "unit_price": 13.10,
    "total": 6550.0, "lead_time_days": 5,
}


def test_well_formed_artifact_is_accepted():
    po = extract_purchase_order(_task_with(VALID_PO))
    assert isinstance(po, PurchaseOrder)
    assert po.po_number == "PO-ABC123"
    assert po.total == pytest.approx(6550.0)


def test_missing_artifacts_key_is_rejected():
    with pytest.raises(UntrustedRemoteOutputError):
        extract_purchase_order({"id": "t", "status": {}})


def test_empty_artifacts_list_is_rejected():
    with pytest.raises(UntrustedRemoteOutputError):
        extract_purchase_order({"artifacts": []})


def test_missing_required_field_is_rejected():
    poisoned = {k: v for k, v in VALID_PO.items()
                if k != "po_number"}
    with pytest.raises(UntrustedRemoteOutputError):
        extract_purchase_order(_task_with(poisoned))


def test_wrong_type_for_quantity_is_rejected():
    poisoned = dict(VALID_PO)
    poisoned["quantity"] = "five hundred units"
    with pytest.raises(UntrustedRemoteOutputError):
        extract_purchase_order(_task_with(poisoned))


def test_wrong_type_for_total_is_rejected():
    poisoned = dict(VALID_PO)
    poisoned["total"] = {"$ne": None}  # NoSQL-injection-flavored junk
    with pytest.raises(UntrustedRemoteOutputError):
        extract_purchase_order(_task_with(poisoned))


def test_completely_malformed_artifact_shape_is_rejected():
    """The remote agent returns something that isn't even
    artifact-shaped -- e.g. a string where a dict was expected."""
    task = {"artifacts": ["not-a-dict"]}
    with pytest.raises(UntrustedRemoteOutputError):
        extract_purchase_order(task)
