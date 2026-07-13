# crew/tasks.py
from __future__ import annotations

from crewai import Task

from .agents import (
    requirements_analyst, terraform_generator,
    policy_reviewer, cost_estimator,
)
from .models import (
    InfraRequest, HclBundle, PolicyReport,
    CostEstimate,
)

intake_task = Task(
    description=(
        "Read this infra request:\n{brief}\n\n"
        "Produce a precise InfraRequest: region, "
        "vpc_cidr, az_count, instance_type, "
        "instance_count, db_engine, "
        "db_instance_class, db_storage_gb, tags. "
        "Do not invent sizing the brief did not "
        "imply - use small, safe defaults for a "
        "staging environment when it's silent."
    ),
    expected_output=(
        "An InfraRequest with every field filled."
    ),
    agent=requirements_analyst,
    output_pydantic=InfraRequest,
)

generate_task = Task(
    description=(
        "From the InfraRequest, write complete "
        "Terraform HCL: a VPC with one subnet per "
        "az_count, a security group, the requested "
        "EC2 instances, and one database instance. "
        "Tag every resource with environment, "
        "owner, and cost-center. Encrypt every "
        "storage resource. Call Validate HCL before "
        "you finish and fix any syntax error it "
        "reports."
    ),
    expected_output=(
        "An HclBundle: filename, hcl, and the "
        "resource_count you wrote."
    ),
    agent=terraform_generator,
    context=[intake_task],
    output_pydantic=HclBundle,
)

policy_task = Task(
    description=(
        "Parse the generated HCL with HCL Resource "
        "Parser, then run Deterministic Policy "
        "Check on the result. Treat every "
        "deterministic finding as final - you may "
        "not overrule one. Then use your own "
        "judgment only on anything the rules did "
        "not catch (unusual resource combinations, "
        "an instance type that doesn't match the "
        "declared environment). Approve, or list "
        "specific violations."
    ),
    expected_output=(
        "A PolicyReport: approved, "
        "checked_deterministic count, violations, "
        "reviewer_notes."
    ),
    agent=policy_reviewer,
    context=[generate_task],
    output_pydantic=PolicyReport,
)

cost_task = Task(
    description=(
        "Parse the approved HCL and run Cost Table "
        "Lookup on the resulting resources. Sum the "
        "monthly total and flag it clearly if it "
        "exceeds the environment's expected range "
        "for a staging deployment."
    ),
    expected_output=(
        "A CostEstimate: lines and "
        "total_monthly_usd."
    ),
    agent=cost_estimator,
    context=[generate_task, policy_task],
    output_pydantic=CostEstimate,
)
