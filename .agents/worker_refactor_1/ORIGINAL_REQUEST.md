## 2026-06-16T20:05:00Z
You are a worker agent. Your task is to implement the dashboard refactoring changes for URBS dashboard (removing emojis, filtering bus lines by processed data, applying light clean theme, and updating map tile layers) at c:\GIT\tcc-urbs.

Specifically, implement the following changes:

1. **Backend Route & Data Filtering in `src/visualization/dashboard.py`**:
   - In endpoint `/api/lines` (`read_lines(regime: str = None)`):
     - Scan `data/dados_processados/` for files starting with `event_log_` and ending with `.csv`.
     - Extract unique line codes from these files.
     - If `regime == "A"`, only include line codes from files with start date `2025-10-24`.
     - If `regime == "B"`, only include line codes from files with start date `2025-12-02`.
     - If `regime` is empty/None, return all unique processed line codes found.
     - If no processed line codes are found, fall back to scanning the raw GPS directories under `data/dados_em_tempo_real_2026/` (intersection of common lines for fallback/empty regime, or folder-specific for regime A/B) and listing those lines.
     - Exclude line `'REC'` and lines starting with `'X'`.
     - Return sorted lines list inside a dict `{"lines": [...]}`.
   - In endpoint `/api/map-data` (`get_map_data(...)`):
     - If `direction` is not in `["IDA", "VOLTA"]`, immediately return an empty map dictionary:
       `{"stops": [], "shape": [], "segments": [], "replay_trips": [], "metrics": {}}`

2. **Emoji Removal in `src/visualization/static/index.html`**:
   - Remove restricted emojis (`🗺️`, `🧭`, `🔍`, `⚡`, `🚫`, `⚠️`) from tab navigation buttons (lines 151-154) and headers/subheaders (lines 163, 178, 195, 226, 248, 271, 292, 319).
   - In zoom buttons (lines 233, 234, 326, 327), replace `🔍 +` and `🔍 -` with `Zoom +` and `Zoom -`.
   - Make sure to keep the logo emoji (`🚌` on line 19) and active bus markers (`🚌` in app.js).

3. **Frontend JS updates in `src/visualization/static/app.js`**:
   - In `loadCommonLines()`, append the selected regime as a query parameter (e.g. `/api/lines?regime=A` or `/api/lines?regime=B` depending on `activeFilters.regime`).
   - In `renderMaps()` and tileLayer definitions (lines 474 and 482), change the Leaflet map tile URL:
     `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
     to the CartoDB Positron light theme:
     `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`

4. **Light Theme Visual Redesign in `src/visualization/static/styles.css`**:
   - Declare the following variables in `:root`:
     ```css
     --bg-light: #fafafa;
     --panel-light: #ffffff;
     --border-light: #e5e7eb;
     --text-main: #111827;
     --text-muted: #6b7280;
     --accent-red: #ef4444;
     --accent-blue: #111827;
     --accent-green: #10b981;
     --accent-orange: #111827;
     --bg-dark: var(--bg-light);
     --panel-dark: var(--panel-light);
     --border-dark: var(--border-light);
     ```
   - Ensure the body has `background-color: var(--bg-light);` and sidebar has `background-color: var(--panel-light);`.
   - Modify primary buttons (`.btn-primary` and `.btn-timeline`) text color to be white (`color: #ffffff;`) and hover background color to be `#374151;`.
   - Update `.highlight-group` to have light background `#fffbeb` and border `1px solid #f59e0b`.
   - Update `.console-wrapper` to have light background `#f3f4f6` and border `1px solid var(--border-light)`, and `#log-console` to have readable dark text `color: #1f2937;`.
   - In `.data-table th` and `.data-table tbody tr:hover`, update background transparent colors to look clean on white backgrounds (e.g., `background-color: rgba(0,0,0,0.02);`).
   - In `.tab-btn:hover`, change `color: white;` to `color: var(--text-main);`.

5. **Verification**:
   - Run the E2E verification test suite:
     `.venv\Scripts\python.exe -m pytest tests/test_dashboard_e2e.py -v`
   - Ensure that 100% of the 60 test cases pass.

MANDATORY INTEGRITY WARNING:
DO NOT CHEAT. All implementations must be genuine. DO NOT hardcode test results, create dummy/facade implementations, or circumvent the intended task. A Forensic Auditor will independently verify your work. Integrity violations WILL be detected and your work WILL be rejected.

Write your changes and handoff report to `handoff.md` under your working directory `c:\GIT\tcc-urbs\.agents\worker_refactor_1\`.
Always update your `progress.md` before and after steps.
