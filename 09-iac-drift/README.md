# Project 09 — IaC Generation & Drift-Detection Crew

**Tier:** Intermediate  ·  **Frameworks:** CrewAI · Terraform

Generates HCL, policy-checks it, estimates cost, detects drift — plan-only, never applies.

Full walkthrough, architecture diagrams, and design rationale are in
**Project 09** of _Building AI Agents_. This folder is the complete code.

## Run it

```bash
uv venv --python 3.12
uv pip install -e ".[dev]"
cp .env.example .env    # add your keys
uv run uvicorn crew.app:app --reload
```

This crew only ever **generates HCL and runs `terraform plan`** against it —
`/generate` writes `main.tf` to a workdir, `/plan` runs a read-only
`terraform init` + `terraform plan` preview, and `/drift-check` diffs the
declared plan against a live-state JSON snapshot. The subprocess wrapper in
`crew/tools.py` (`_run_terraform`) allow-lists only `init`, `validate`,
`fmt`, and `plan` — it raises before ever shelling out if any code path asks
for `apply` or `destroy`. Nothing in this project ever applies or destroys
real infrastructure; running `terraform apply` yourself, in your own
terminal, after reading the plan, is a deliberate manual step outside this
crew.

## Files

- `.env.example`
- `.python-version`
- `Dockerfile`
- `crew/__init__.py`
- `crew/agents.py`
- `crew/app.py`
- `crew/crew.py`
- `crew/models.py`
- `crew/policies.py`
- `crew/tasks.py`
- `crew/tools.py`
- `evals/run_evals.py`
- `main.tf`
- `pyproject.toml`
- `requirements.txt`
- `tests/__init__.py`
- `tests/test_cost.py`
- `tests/test_drift.py`
- `tests/test_policies.py`
- `tests/test_safety.py`
- `uv.lock`

## Safety

If this project touches a regulated or irreversible action, its human-approval
gate is structural, not a prompt instruction. Do not remove it.
