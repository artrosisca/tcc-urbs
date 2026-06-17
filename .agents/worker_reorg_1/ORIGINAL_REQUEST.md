## 2026-06-16T19:50:46Z
You are a worker agent. Your task is to perform the repository folder reorganization (R4) at c:\GIT\tcc-urbs.
Specifically, do the following:
1. Create a central `data` folder in the root directory if it doesn't exist.
2. Move the folders `dados_c3sl`, `dados_em_tempo_real_2026`, and `dados_processados` into this new `data/` folder.
3. Move the `download_c3sl.py` script from the root to `src/etl/download_c3sl.py`.
4. Update all Python imports, file reading/writing references, and config scripts to point to the new paths (e.g. `data/dados_processados`, `data/dados_c3sl`, `data/dados_em_tempo_real_2026`, and `src/etl/download_c3sl.py`). This includes:
   - `src/etl/load_c3sl.py`
   - `src/etl/load_realtime.py`
   - `src/etl/build_event_log.py`
   - `src/mining/conformance.py`
   - `src/mining/discovery.py`
   - `src/mining/performance.py`
   - `src/visualization/dashboard.py`
   - `.gitignore` (update gitignore paths as well)
   - Any other scripts where paths are referenced.
5. Make sure the python backend starts successfully and verify that python files can import each other without path/module errors.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes and handoff report to `handoff.md` under your working directory `c:\GIT\tcc-urbs\.agents\worker_reorg_1\`.
Always update your `progress.md` before and after steps.
