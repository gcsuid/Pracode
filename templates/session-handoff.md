# Session Handoff

## Verified Now

- FastAPI backend boots and the test suite passes.
- SQLite-backed SQLAlchemy persistence is active by default.
- Question logging endpoints are implemented and covered by tests.
- `python -m pytest -q` passes with `3 passed`.

## Changed This Session

- Added `app/` backend package with DB setup, model, schemas, and API routes.
- Added `tests/test_app.py` for health and question API behavior.
- Added `requirements.txt`, `init.sh`, and `init.ps1`.
- Updated template feature ledger and progress artifacts for the newly completed work.

## Broken Or Unverified

- Practice engine and AI-backed features (phase-003 onward) are not implemented yet.

## Next Best Step

- Highest-priority unfinished feature: `phase-003` Practice Engine.
- Why it is next: the database and logging baseline is now complete and stable.
- What counts as passing: practice endpoint returns a previously logged question and records the attempt.
- What must not change during that step: existing question API contracts and SQLite compatibility.
