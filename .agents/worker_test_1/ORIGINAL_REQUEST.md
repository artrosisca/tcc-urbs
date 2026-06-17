## 2026-06-16T19:46:04Z
You are a worker agent. Your task is to implement the E2E test suite in `tests/test_dashboard_e2e.py` at c:\GIT\tcc-urbs.
The test suite should be built using `pytest` and follow the plan in `TEST_INFRA.md`. It must run using the local virtualenv python and check both the static frontend files and the FastAPI backend server endpoints (using `fastapi.testclient.TestClient`).
Specifically, implement tests for the following:
1. **Tier 1 (Feature Coverage, >=25 tests)**:
   - Check emoji removal in `index.html` headers and tab navigation (verify no 🗺️, 🧭, 🔍, ⚡, 🚫, ⚠️ are present in buttons/headers; keep 🚌 in logo).
   - Check CartoDB Positron maps URL in `app.js` (verify light maps are set).
   - Check styles.css has clean light theme colors (background, panels, text main, text muted).
   - Check folder structure paths (data paths are updated to point to `data/`).
   - Check backend endpoint `/api/lines` lists the expected lines for Regime A, Regime B, and fallback.
2. **Tier 2 (Boundary & Corner cases, >=25 tests)**:
   - Check behavior of endpoints with empty/invalid inputs (e.g. regime parameters, date ranges, query params).
   - Check CSS styling boundary values (e.g., proper font sizing, borders, specific hex color variations).
   - Check file-checking fallbacks in `dashboard.py` if no files are found.
3. **Tier 3 (Cross-Feature combinations, >=5 tests)**:
   - Check interplay between regime selection, date range filtering, and bus line dropdown.
4. **Tier 4 (Real-World application scenarios, >=5 tests)**:
   - Run end-to-end verification sequences simulating user actions (selecting regime, changing date, listing lines, checking trips, loading maps).

Make sure the tests use `from fastapi.testclient import TestClient` and import `app` from `src.visualization.dashboard` to test backend behavior directly without needing a separate running server process.
Wait! Since we are doing this before refactoring, some tests (like path reorganization or light theme checks) might fail when run on the original codebase. That is expected! Let's ensure the tests are clean and clear.
Remember the Integrity warning:
MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Please write the test suite in `tests/test_dashboard_e2e.py` and run it on the current codebase. Document the results in `handoff.md` under your working directory `c:\GIT\tcc-urbs\.agents\worker_test_1\`.
Always update your `progress.md` before and after steps.
