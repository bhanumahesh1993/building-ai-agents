# crew/models.py
from __future__ import annotations

from pydantic import BaseModel


class InfraRequest(BaseModel):
    environment: str
    region: str
    vpc_cidr: str
    az_count: int
    instance_type: str
    instance_count: int
    db_engine: str
    db_instance_class: str
    db_storage_gb: int
    tags: dict[str, str]


class HclBundle(BaseModel):
    filename: str
    hcl: str
    resource_count: int


class Violation(BaseModel):
    rule: str
    resource: str
    severity: str
    message: str


class PolicyReport(BaseModel):
    approved: bool
    checked_deterministic: int
    violations: list[Violation]
    reviewer_notes: str


class CostLine(BaseModel):
    resource: str
    monthly_usd: float


class CostEstimate(BaseModel):
    lines: list[CostLine]
    total_monthly_usd: float


class DriftEntry(BaseModel):
    resource: str
    field: str
    declared: str
    actual: str
    severity: str
    remediation: str


class DriftReport(BaseModel):
    drifted: bool
    entries: list[DriftEntry]


class IacPlan(BaseModel):
    request: InfraRequest
    hcl: HclBundle
    policy: PolicyReport
    cost: CostEstimate
    revisions_used: int
