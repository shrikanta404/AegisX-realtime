# Monitoring Pseudocode

```text
for each active authorized scope:
    validate target with ScopeGuard
    inventory = collect DNS + TLS + selected services
    save snapshot

    compare current snapshot with previous snapshot
    for each detected change:
        create finding
        create change evidence

    inspect current inventory for seeded conditions
    for each issue:
        create finding
        create issue evidence

    optionally enrich finding with threat intelligence
    optionally request Gemini explanation

    write audit event
```
