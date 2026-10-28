# AegisX

**Authorized Attack-Surface Intelligence & Change Monitor**

AegisX is a PS-011 prototype for **live, authorized** attack-surface monitoring. The UI does not use a fixed dashboard dataset: it reads PostgreSQL through FastAPI, while the backend performs fresh DNS, TLS and selected TCP-service observations against active authorized scopes.

## What is live

When an authorized scope is monitored, AegisX collects current:

- DNS records for the supplied hostname (A, AAAA, CNAME, MX, NS, TXT where available)
- TLS certificate metadata, including expiry, issuer, subject, serial and SHA-256 fingerprint
- Selected TCP service states on the ports configured for that authorized scope
- Current IP address and inventory timestamp
- Snapshot-to-snapshot changes
- Deterministic security findings and evidence

The browser refreshes API-backed views every few seconds. The backend scheduler performs an immediate authorized collection at startup and repeats at the configured interval. Manual **Run live collection** triggers a fresh collection immediately.

## Architecture

```text
Authorized Scope
      |
  Scope Guard
      |
 Live Inventory
  /     |      \
 DNS   TLS   Services
  \      |      /
    Inventory Snapshot
           |
     Change Detection
           |
    Finding + Evidence
       /          \
 Threat Intel     Gemini
       \          /
       Dashboard / Reports
```

## Important scope rule

AegisX only monitors domains covered by an active authorized scope. Do not enter a target unless you have written authorization to monitor it. The service collector only checks the ports listed in the scope configuration, and the dangling-DNS result is a review signal rather than a claim of exploitability.

## Repository layout

```text
AegisX/
├── backend/          FastAPI + SQLAlchemy + Alembic
├── frontend/         React + TypeScript + Vite + Three.js
├── database/         database notes
├── docs/             architecture, security and demo documentation
└── scripts/          Windows setup / start / verify helpers
```

## Backend setup (Windows PowerShell)

Python 3.13 and PostgreSQL are recommended.

```powershell
cd backend
py -3.13 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `backend/.env` with your PostgreSQL password and any optional API keys. API keys are never displayed by the frontend.

Create the PostgreSQL database and migrate it:

```powershell
python -m alembic upgrade head
```

Start the backend:

```powershell
python -m uvicorn app.main:app --reload
```

Swagger: `http://localhost:8000/docs`

Health: `http://localhost:8000/health`

## Frontend setup

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

Set `VITE_API_BASE_URL` in `frontend/.env` when the backend is not on the default address.

## Live collection workflow

1. Open **Settings → Authorized scope**.
2. Enter a domain/host that is explicitly approved for monitoring.
3. Configure the permitted ports and checks.
4. Click **Add scope**.
5. Open the Command Center and select the authorized domain.
6. Click **Run live collection**.
7. Watch Assets, Changes, Findings and the 3D Attack Surface refresh from PostgreSQL.
8. Keep the scheduler running for continuous monitoring.

The scheduler default is one collection every 60 seconds. Adjust `SCHEDULER_INTERVAL_SECONDS` in `.env` for your lab, subject to the organizer's allowed operating conditions.

## Verification

From the repository root after installing dependencies:

```powershell
.\scripts\verify.ps1
```

The verification script uses the virtual-environment Python interpreter and `python -m alembic` conventions so a global Alembic installation is not required.

## Optional integrations

- Gemini for defensive explanation, correlation and summaries
- VirusTotal domain reputation
- AbuseIPDB IP reputation

If keys are absent, the core collection and monitoring pipeline still works.

## Demo flow

1. Create an authorized lab scope.
2. Run the first live collection to establish a baseline.
3. Introduce a controlled, authorized lab change.
4. Run or wait for the next collection.
5. Review the change timeline.
6. Review the generated finding and evidence.
7. Run AI analysis.
8. Review false-positive handling and the audit trail.
9. Export the security report.
