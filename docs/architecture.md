# AegisX Architecture

## Trust boundaries

The scope guard is the first security boundary. Every monitoring request resolves an active `AuthorizedScope` before inventory runs.

## Data pipeline

`Scope -> Inventory -> Snapshot -> Change Detector -> Finding Engine -> Evidence -> AI/TI -> UI/Report`

## Deterministic vs AI responsibilities

Deterministic services establish facts: DNS, TLS, service state, snapshot comparison and seeded issue detection. Gemini is used only for explanation, correlation and summaries over supplied evidence.
