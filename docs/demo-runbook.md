# AegisX Demo Runbook

Use only targets that are explicitly organizer-approved and present in the active AegisX authorized scope.

## 1. Start

- PostgreSQL: database `aegisx_dev`
- Backend: `scripts/start_backend.ps1`
- Frontend: `scripts/start_frontend.ps1`
- Swagger: `http://localhost:8000/docs`

## 2. Establish scope

From Settings or `POST /api/v1/scopes`, create the lab scope with the organizer-approved domain(s), ports and checks.

## 3. Establish baseline

Run `POST /api/v1/scheduler/run/{domain}` once. The first snapshot becomes the comparison baseline.

## 4. Demonstrate change detection

Make one controlled change inside the approved lab, run monitoring again, then show:

`Changes -> Finding -> Evidence`

## 5. Demonstrate seeded issues

Use the controlled lab state to demonstrate an expired TLS certificate, an unexpected service, and a potential dangling DNS review condition. The dangling-DNS result is intentionally presented as a review signal and does not claim exploitability.

## 6. Demonstrate AI

Open the finding, request AI analysis, and show the supplied finding/evidence plus available VirusTotal or AbuseIPDB context. The AI layer explains supplied facts; it does not expand scope or run attacks.

## 7. Demonstrate review and reporting

- Mark a finding as a false positive with a reason.
- Show the audit log.
- Open Reports and export/print the security report.
