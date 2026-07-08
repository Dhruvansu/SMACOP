# SMACOP Project Plan

**Team:** Dhruv & Quang
**Start:** Tuesday, July 8, 2026
**Due:** Friday, July 24, 2026 (16 days)
**Goal:** Ship a Secure Microservice API & Cloud Observability Platform — a FastAPI service with JWT auth, containerized, deployed behind a private Azure network boundary, and observable through Grafana/Azure Monitor dashboards — entirely within Azure free-tier limits.

---

## 0. Architecture Recap

Per the README's flow diagram, the request path is:

1. Client requests a JWT from the FastAPI service (running in Docker).
2. FastAPI returns the JWT.
3. Client calls a protected route; traffic must traverse the Azure VNet boundary (NSG → Private Endpoint → Web App).
4. The Web App emits metrics and custom middleware logs to Azure Monitor.
5. Azure Monitor ingests telemetry into a Log Analytics Workspace.
6. Grafana queries Log Analytics via KQL to render live dashboards.

Every phase below builds one segment of this pipeline. Order matters: auth/middleware must exist before there's anything meaningful to containerize, network-isolate, or observe.

---

## 1. Team & Repository Setup
**Target: Jul 8 – Jul 9 (Days 1–2)**

- Create the shared GitHub repo (already done — SMACOP).
- Agree on a branching strategy: `main` protected, feature branches per task (e.g. `feature/jwt-auth`, `feature/dockerfile`, `feature/vnet`), PRs required before merge.
- Set up issue/task tracking (GitHub Issues or a shared board) mapped to the sections in this plan.
- Both partners clone the repo, confirm independent commit access, and agree on a commit-message convention.
- Install local toolchain: Python 3.11+, Docker Desktop with WSL2 backend, Azure CLI, `az` login test.
- Divide ownership for Phase 1 vs Phase 2 features so both partners have independent, parallel-committable work (e.g. Dhruv leads API/auth, Quang leads infra/networking, both contribute to observability — swap for later phases to keep contribution even).

**Deliverable:** Repo scaffold with `app/` (FastAPI), `infra/` (Dockerfile, Azure/Bicep or Terraform scripts), `docs/`, branching rules documented in `CONTRIBUTING.md`.

---

## 2. Secure FastAPI Core — Auth & Middleware
**Target: Jul 10 – Jul 13 (Days 3–6)**

Implements diagram steps 1–2 (token issuance).

- Scaffold FastAPI app with a health-check route (`/healthz`).
- Build user registration/login endpoints; issue short-lived JWTs (e.g. `python-jose` or `pyjwt`), with expiry and refresh strategy decided up front.
- Add a dependency-injected auth guard for protected routes (`Depends(get_current_user)`), returning 401 on invalid/expired tokens.
- Write custom middleware that:
  - Intercepts unhandled exceptions and logs them uniformly (structured JSON logs — needed later for Log Analytics ingestion).
  - Captures request/response timing (latency) and status codes for SLI tracking.
- Unit + integration tests for auth flows (valid login, invalid credentials, expired token, protected route access).
- Local run via `uvicorn`; manual verification with Postman/curl per the diagram's "Client / Postman" actor.

**Deliverable:** Working local API with `/register`, `/token`, and at least one protected route, plus middleware emitting structured logs to stdout.

---

## 3. Containerization & Local Integration Testing
**Target: Jul 14 – Jul 15 (Days 7–8)**

Implements diagram's "FastAPI inside Docker" and the shift-left testing guideline.

- Write an optimized multi-stage Dockerfile (slim base image, non-root user, minimal layer count).
- Add `docker-compose.yml` for local dev (API + any local dependencies).
- Confirm the containerized app behaves identically to the local run inside WSL2 — this is the "runs the same locally and in the cloud" user story.
- Add a smoke-test script that spins up the container and exercises `/healthz`, `/token`, and a protected route.
- Document image build/run commands in `README.md` or `docs/`.

**Deliverable:** `docker build && docker run` reproduces the full auth flow locally, verified before any cloud push.

---

## 4. Azure Deployment & Private Networking
**Target: Jul 16 – Jul 19 (Days 9–12)**

Implements diagram's VNet boundary (NSG → Private Endpoint → Web App).

- Provision an Azure Web App on the **F1 (Free)** App Service Plan.
- Push the container image (Azure Container Registry or GitHub Container Registry) and configure the Web App to pull it.
- Create a Virtual Network (VNet) and subnet(s) for the app tier.
- Configure a Network Security Group (NSG) with restrictive inbound rules (deny public access except intended paths).
- Set up a Private Endpoint so the Web App is reachable only within the VNet boundary, per the "security engineer" user story.
- Validate end-to-end: client can still obtain a token and reach the protected route only through the intended, restricted path — test both the "should work" and "should be blocked" cases.
- **Immediately set the Azure Budget alert to $0.01** as soon as any resource is provisioned (see Section 6) — do this before deploying anything else to the cloud.

**Deliverable:** Live Azure Web App reachable only via the configured private network path, running the same image validated locally.

**Risk flag:** Private Endpoints + NSGs are the most likely source of "it works locally but not in Azure" debugging time — budget slack here.

---

## 5. Monitoring & Telemetry Dashboards
**Target: Jul 20 – Jul 22 (Days 13–15)**

Implements diagram steps 4–6 (Web App → Azure Monitor → Log Analytics → Grafana).

- Wire the app's custom middleware logs and metrics into Azure Monitor (Application Insights SDK or diagnostic settings forwarding to Log Analytics).
- Confirm telemetry ingestion in the Log Analytics Workspace; watch ingestion volume against the 5 GB/month free-tier cap.
- Write KQL queries for the core SLIs called out in the README:
  - HTTP error rate (target SLO: 5xx < 0.1%)
  - Latency percentiles (p50/p95/p99)
  - Request volume / auth failure rate
- Connect Grafana (or Azure Monitor dashboards) to Log Analytics and build a live dashboard visualizing the above KQL queries.
- Validate the "SRE" user story: someone unfamiliar with the code can look at the dashboard and assess platform health.

**Deliverable:** Live dashboard showing real request telemetry from the deployed Azure Web App, backed by documented KQL queries and explicit SLIs/SLOs.

---

## 6. Zero-Cost Compliance Guardrails
**Target: Ongoing, finalized by Jul 22 (Day 15)**

Not a separate phase — a checklist enforced throughout Sections 4–5:

- [ ] App Service Plan is F1 (Free) — verify in Azure Portal, not just at creation time (redeploys can silently change tier).
- [ ] Log Analytics Workspace ingestion tracked against the 5 GB/month cap; set a daily cap if needed.
- [ ] Azure Budget alert configured at a **$0.01** hard ceiling, set up **before** any paid-tier-capable resource is created.
- [ ] All integration testing happens locally in Docker/WSL2 before any cloud push (no "test in prod").
- [ ] Periodic cost review in Azure Cost Management by both partners, not just whoever provisioned resources.

---

## 7. Integration, Hardening & Demo Prep
**Target: Jul 23 – Jul 24 (Days 16–17)**

- Full end-to-end walkthrough of the diagram: token request → protected route → private network path → telemetry → dashboard, run by both partners independently.
- Confirm even git contribution history (both partners have meaningful, independent commits — not just one partner committing both people's work).
- Clean up docs: architecture diagram, setup/run instructions, KQL query reference, known limitations.
- Rehearse a short demo/walkthrough for submission.
- Final buffer for any NSG/Private Endpoint or ingestion-quota issues surfaced late.

**Deliverable:** Submission-ready repo + live (or last-verified) Azure deployment + dashboard screenshots/recording as a fallback if free-tier resources are torn down before grading.

---

## 8. Extension Features (Stretch — only after Sections 1–7 are solid)
**Target: only if time remains before Jul 24**

Pick based on remaining time and interest; these are explicitly optional per the README.

- **Automated CI/CD:** GitHub Actions pipeline — build image, vulnerability scan (e.g. Trivy), push to registry, deploy to Azure Web App on merge to `main`.
- **Decentralized Secret Management:** Move JWT signing keys/DB credentials into Azure Key Vault, pulled at app startup instead of baked into the container or `.env`.
- **Automated Alerting:** Azure Monitor alert rule that fires email/webhook if 5xx rate exceeds the SLO for >3 minutes.

Suggested priority order if only one is attempted: CI/CD first (compounds testing effort already done), then Key Vault, then alerting.

---

## Suggested Timeline Summary

| Days | Dates | Phase |
|---|---|---|
| 1–2 | Jul 8–9 | Repo & environment setup |
| 3–6 | Jul 10–13 | FastAPI auth & middleware |
| 7–8 | Jul 14–15 | Containerization & local testing |
| 9–12 | Jul 16–19 | Azure deployment & private networking |
| 13–15 | Jul 20–22 | Monitoring & dashboards |
| 16–17 | Jul 23–24 | Integration, hardening, demo prep |
| — | if time remains | Extension features |

This leaves no dedicated stretch-feature block by default — the core three required features plus free-tier compliance are the priority. Only pull from Section 8 once Sections 1–7 are demo-ready.
