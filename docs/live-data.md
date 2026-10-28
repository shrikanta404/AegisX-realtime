# AegisX live data collection

The dashboard is intentionally database/API driven. It does not ship with a hardcoded asset dataset.

## Collection sources

For each active authorized scope, an inventory cycle queries:

- DNS: A, AAAA, CNAME, MX, NS and TXT through the configured DNS resolver.
- TLS: a live TLS handshake on port 443 and certificate metadata extraction, including expiry and SHA-256 fingerprint. Certificate verification is disabled for the observation handshake so expired certificates can still be inspected.
- Services: TCP connectivity for the ports explicitly allowed by the scope.

Each cycle is stored as an `inventory_snapshot` and the UI reads the resulting database state through the API.

## Live mode

The Command Center has **Run live collection**. This calls the scope-guarded monitoring endpoint and returns the current inventory plus any newly detected changes/findings.

The backend scheduler runs an immediate cycle when the application starts and repeats at `SCHEDULER_INTERVAL_SECONDS` (minimum 30 seconds). The browser refreshes monitoring views every few seconds, so new database state becomes visible without manually reloading the page.

## Authorization

Live collection is rejected unless the hostname is inside an active `AuthorizedScope`. Keep the project limited to organizer-approved targets and configured ports/checks.
