# Building AI Agents — Companion Code

Complete, runnable source for all 25 projects from **_Building AI Agents_** by
Bhanu Mahesh. The book teaches the architecture, the load-bearing code, the
safety logic, and how to run each system; this repository holds the full source,
dependency locks, Docker configs, tests, and evaluation fixtures.

> **Matching editions.** Each book edition points at a git tag — for the first
> edition, check out `v1.0-book`. `main` tracks framework updates and may run
> ahead of the printed listings.

## The 25 projects

| # | Project | Tier | Frameworks |
|---|---------|------|------------|
| [01](./01-personalized-tutor/) | Personalized Tutor Agent | Starter | Pydantic AI · Langfuse |
| [02](./02-data-analyst/) | Autonomous Data Analyst | Starter | Pydantic AI · DuckDB |
| [03](./03-marketing-crew/) | Marketing Content Pipeline Crew | Starter | CrewAI · Langfuse |
| [04](./04-support-deflection/) | Tier-1 Support Deflection System | Starter | LangGraph · MCP |
| [05](./05-automated-grading/) | Automated Grading & Feedback | Starter | LangGraph |
| [06](./06-agentic-rag/) | Agentic RAG Knowledge Assistant | Intermediate | LlamaIndex · pgvector |
| [07](./07-deep-research/) | Deep Research Report Generator | Intermediate | LangGraph · Langfuse |
| [08](./08-code-review/) | Multi-Agent Code Review & Security Audit | Intermediate | LangGraph |
| [09](./09-iac-drift/) | IaC Generation & Drift-Detection Crew | Intermediate | CrewAI · Terraform |
| [10](./10-voice-support/) | Voice-Enabled Support Agent | Intermediate | Whisper · FastAPI WS |
| [11](./11-competitive-intel/) | Competitive-Intelligence Monitor | Intermediate | LangGraph · pgvector |
| [12](./12-literature-review/) | Scientific Literature Review Agent | Intermediate | Google ADK |
| [13](./13-legal-research/) | Legal Research Deep-Dive Agent | Intermediate | Claude Agent SDK |
| [14](./14-clinical-docs/) | Ambient Clinical Documentation Assistant | Intermediate | Pydantic AI |
| [15](./15-shopping-agent/) | E-commerce Shopping Agent | Intermediate | OpenAI Agents SDK · MCP |
| [16](./16-soc-triage/) | Autonomous SOC Alert-Triage System | Advanced | LangGraph · MCP |
| [17](./17-threat-intel/) | Threat-Intel Briefing & Vuln Prioritization | Advanced | CrewAI |
| [18](./18-diagnostic-debate/) | Clinical Diagnostic Debate Panel | Advanced | LangGraph |
| [19](./19-trading-firm/) | Multi-Agent Trading Research Firm | Advanced | LangGraph |
| [20](./20-aml-investigation/) | Financial-Crime & AML Investigation | Advanced | OpenAI Agents SDK |
| [21](./21-contract-diligence/) | Contract Due-Diligence & Redlining | Advanced | LlamaIndex · LangGraph |
| [22](./22-coding-agent/) | Autonomous Coding & PR Agent | Advanced | Claude Agent SDK · Docker |
| [23](./23-incident-response/) | DevOps Incident-Response Copilot | Advanced | LangGraph · MCP |
| [24](./24-app-builder/) | Full-Stack App Builder Agent | Advanced | Claude Agent SDK |
| [25](./25-supply-chain/) | Cross-Enterprise A2A Supply-Chain Orchestrator | Advanced | Google ADK · A2A |

## Quickstart

```bash
git clone https://github.com/bhanumahesh1993/building-ai-agents
cd building-ai-agents/07-deep-research
uv sync                     # install pinned dependencies
cp .env.example .env        # add your API keys
uv run python -m research.app
```

Every project folder has its own layout: `src/` (or a package dir), `tests/`,
`evals/`, a `Dockerfile`, `requirements.txt`, and an `.env.example`. See
**Appendix A** of the book for full environment setup (`uv`, keys, Docker,
Postgres/pgvector).

## Status

This repository is seeded from the book's listings — the same code you read on
the page, organized into runnable project trees. Projects are being hardened for
end-to-end reproducibility on an ongoing basis; open an issue if a project does
not run as-is against the pinned versions.

## License

MIT — see [LICENSE](./LICENSE). Build on it, ship it, make it yours.

## Safety note

Several projects operate in regulated or high-stakes domains (healthcare,
finance, legal, security). Every irreversible action in those projects is gated
behind an explicit human step, by design. They are educational and research
reproductions, **not** professional advice or approved tools. Keep the gates.
