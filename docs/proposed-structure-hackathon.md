# AegisX Proposed Project Structure

## Product

AegisX — Authorized Attack-Surface Intelligence & Change Monitor

## Architecture

```text
Authorized Scope
  -> Scope Guard
  -> Inventory Collectors (DNS / TLS / Services)
  -> Inventory Snapshot
  -> Change Detection
  -> Finding Engine
  -> Evidence
  -> Threat Intelligence / Gemini AI
  -> Dashboard / Reports / Audit Log
```

## Backend

- FastAPI API layer
- SQLAlchemy ORM and PostgreSQL
- Alembic migrations
- Scope Guard authorization boundary
- Inventory collectors
- Snapshot and change detection
- Deterministic security issue detection
- Findings and evidence
- False-positive review
- Audit logging
- APScheduler
- Gemini, VirusTotal and AbuseIPDB integrations

## Frontend

- React + TypeScript + Vite
- API-backed Command Center
- Attack Surface view with Three.js visualization
- Assets, Changes, Findings, Reports and Settings views
- Authorized scope management
- Scheduler control
- Evidence and AI analysis panels

## Safety boundaries

- Monitoring is restricted to active authorized scopes.
- Port selection is configurable per authorized scope.
- No exploitation functionality is included.
- Potential dangling DNS is a review signal, not an exploitability claim.
- AI receives collected evidence and must not invent vulnerabilities or expand targets.
