## 2026-06-16T20:00:10Z
You are a worker agent. Your task is to execute the folder moves and run the verification tests for the repository reorganization (R4).
Please:
1. Run the Python automation script:
   `.venv\Scripts\python.exe -m src.etl.reorganize`
2. Once the moves are completed, run the E2E test suite to verify the changes:
   `.venv\Scripts\python.exe -m pytest tests/test_dashboard_e2e.py -v`
3. Document the command outputs and test results (specifically how many tests pass and fail now). Verify that the path reorganization tests (like `test_dashboard_py_uses_data_prefix_for_raw_gps`, etc.) now pass.
4. Write your handoff report to `handoff.md` under your working directory `c:\GIT\tcc-urbs\.agents\worker_reorg_exec_1\`.
Always update your `progress.md` before and after steps.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.
