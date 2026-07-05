# Project Review (Quick Scan)

## Scan Scope
- Code scanned: `app/*`, `tests/test_app.py`, `requirements.txt`, `init.sh`, `init.ps1`
- History/context scanned: `templates/progress.md`, `templates/session-handoff.md`, `templates/feature_list.json`, `templates/context.md`, `templates/agents.md`
- Current baseline from scan: tests pass (`7 passed`), but multiple correctness/maintainability issues remain.

## History Notes (from `templates/`)
- Session 001 built the FastAPI + SQLite MVP and initial AI plumbing.
- Session 002 migrated model calls to Ollama (`qwen2.5:3b`) with heuristic fallback.
- Session 003 added pattern storage, recall evaluation persistence, and review scheduling/prioritization.
- Feature ledger reports all phases as `passing`, but the items below are still unresolved in current code.

## Issues Found

1. **Health endpoint reports database type incorrectly**
   - **Where:** `app/main.py` (`/health`)
   - **Issue:** `database` is hardcoded to `"sqlite"` even when `DATABASE_URL` can point elsewhere.
   - **Impact:** Operational/monitoring output can be misleading in non-SQLite deployments.

2. **Ollama availability is cached permanently**
   - **Where:** `app/services.py` (`_ollama_is_available`, `_use_ollama`)
   - **Issue:** `@lru_cache(maxsize=1)` locks availability result for the process lifetime.
   - **Impact:** If Ollama is down at startup and later recovers, app may keep using fallback logic until restart.

3. **Broad exception swallowing in AI paths**
   - **Where:** `app/services.py` (`detect_pattern`, `rephrase_question`)
   - **Issue:** Multiple `except Exception:` blocks silently fall back without surfacing cause.
   - **Impact:** Real integration errors are hidden, making production debugging and incident response harder.

4. **Two-phase write can leave partial question state**
   - **Where:** `app/main.py` (`create_question`)
   - **Issue:** `Question` is committed first, `QuestionInsight` committed separately.
   - **Impact:** A failure between commits can persist a question without the expected derived insight (inconsistent state).

5. **Recall attempt can become empty after trimming**
   - **Where:** `app/main.py` (`submit_recall`), `app/schemas.py` (`RecallAttemptCreate`)
   - **Issue:** Schema only checks `min_length=1`; whitespace-only payload passes, then `.strip()` stores `""`.
   - **Impact:** Empty recall submissions can be accepted/scored, degrading data quality and feedback value.

6. **Repo workflow contract in `templates/agents.md` is not fully satisfied**
   - **Where:** repository root vs. `templates/agents.md`
   - **Issue:** `agents.md` defines `progress.md` and `feature_list.json` as required artifacts, but root-level `progress.md` is missing and tracking is under `templates/`.
   - **Impact:** Handoff/startup workflow is ambiguous and can cause session-to-session drift.

7. **Minor cleanup issue in startup script**
   - **Where:** `init.ps1`
   - **Issue:** File ends with a stray `#is it` comment fragment.
   - **Impact:** Not a runtime bug, but indicates unclean checked-in script state.

8. **Test coverage gaps for risky paths**
   - **Where:** `tests/test_app.py`
   - **Issue:** No targeted tests for whitespace-only recall input, AI provider failure behavior visibility, or `/health` accuracy against configured DB backend.
   - **Impact:** Regressions in input validation and observability can slip through while suite still passes.

## Priority Fix Order
1. Input/data integrity: items **4** and **5**
2. Runtime correctness/observability: items **1**, **2**, **3**
3. Workflow consistency and hygiene: items **6**, **7**, **8**
