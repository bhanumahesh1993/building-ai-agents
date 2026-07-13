# skills/scaffold-conventions/SKILL.md
---
name: scaffold-conventions
description: Naming and layout rules for generated
  FastAPI + static-frontend apps. Use when writing
  any file inside an app-builder workspace.
---

Endpoints live in backend/app/api.py, one function
per route, named after the HTTP verb and resource
(get_poll, post_vote). Entities live in
backend/app/models.py as SQLModel classes. Never
invent a new top-level folder - if your task needs
one, say so in your output instead of creating it.
