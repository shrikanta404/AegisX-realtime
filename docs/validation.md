# Validation Notes

## Checks completed in the packaged source tree

- Python compile check: `python -m compileall -q app migrations tests`
- Offline core tests: `PYTHONPATH=. python tests/test_offline.py`
- Frontend TypeScript project check: `node node_modules/typescript/bin/tsc -b`

The source tree is packaged without `backend/.env`, Python virtual environments, `frontend/node_modules`, caches or generated build output. Install dependencies locally before running the application.
