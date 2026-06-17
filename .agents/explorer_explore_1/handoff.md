# Explorer Handoff Report

## 1. Observation

Direct observations made in the repository files:

### Emojis in Headers and Tabs
- **File**: `src/visualization/static/index.html`
  - **Line 151**: `<button class="tab-btn active" data-tab="tab-mapa">🗺️ Aba 1: Mapas Geográficos de Operação</button>`
  - **Line 152**: `<button class="tab-btn" data-tab="tab-descoberta">🧭 Aba 2: Descoberta de Processos</button>`
  - **Line 153**: `<button class="tab-btn" data-tab="tab-conformidade">🔍 Aba 3: Auditoria & Conformidade</button>`
  - **Line 154**: `<button class="tab-btn" data-tab="tab-desempenho">⚡ Aba 4: Desempenho & Gargalos</button>`
  - **Line 163**: `<h2>🗺️ Visualização de Mapas CCO Integrados</h2>`
  - **Line 178**: `<h3>🗺️ Mapa A: Gargalos e Trechos (Velocidade Média)</h3>`
  - **Line 195**: `<h3>🚌 Mapa B: Replay da Frota (Simulador Histórico)</h3>`
  - **Line 226**: `<h2>🧭 Rede de Petri Descoberta (Inductive Miner)</h2>`
  - **Line 248**: `<h2>🔍 Auditoria de Fidelidade de Rota (Token-Based Replay)</h2>`
  - **Line 271**: `<h3>🚫 Pontos Mais Pulados/Ignorados</h3>`
  - **Line 292**: `<h3>⚠️ Detalhes de Viagens com Maior Desvio</h3>`
  - **Line 319**: `<h2>⚡ Directly-Follows Graph (DFG) de Tempos Operacionais</h2>`

### Theme & Styling
- **File**: `src/visualization/static/styles.css`
  - **Line 1**: `/* Estilo Global CCO Dark */`
  - **Lines 2–12**:
    ```css
    :root {
        --bg-dark: #1e1e24; /* Cinza Escuro de fundo */
        --panel-dark: #121214; /* Painel cinza muito escuro */
        --border-dark: #2d2d34; /* Borda cinza suave */
        --text-main: #f1f5f9;
        ...
    }
    ```

### Leaflet Configuration
- **File**: `src/visualization/static/app.js`
  - **Lines 473–474**:
    ```javascript
    mapCongestion = L.map('map-congestion').setView([-25.43, -49.27], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    ```
  - **Lines 481–482**:
    ```javascript
    mapReplay = L.map('map-replay').setView([-25.43, -49.27], 13);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
    ```

### Directory References
- **File**: `src/etl/load_c3sl.py` (Line 33) uses `"dados_c3sl"`.
- **File**: `src/etl/load_realtime.py` (Line 5) uses `"dados_em_tempo_real_2026"`.
- **File**: `src/etl/build_event_log.py` (Line 9) uses `"dados_processados"`.
- **File**: `PROJECT.md` (Line 24) references `src/etl/download_c3sl.py`.

### Endpoints and Frontend Fetching Logic
- **File**: `src/visualization/dashboard.py`
  - **Lines 113–120**: Exposes the `GET /api/lines` endpoint calling `get_common_lines()`.
  - **Lines 52–77**: `get_common_lines()` fetches lines from `dados_em_tempo_real_2026/2025-10-24` and `dados_em_tempo_real_2026/2025-12-02` and computes their intersection.
- **File**: `src/visualization/static/app.js`
  - **Line 172**: Fetches `/api/lines`.
  - **Lines 74–122**: Unlocks the filter sidebar upon regime selection.

---

## 2. Logic Chain

1. **Emojis**: Identifying header/tab emojis is straightforward by searching for literal strings (e.g. `🗺️`, `🧭`) within `index.html`. Line numbers are extracted directly from the HTML search results.
2. **Current Theme/CSS**: Inspecting `styles.css` confirms the project uses a Global CCO Dark theme with CSS variables (e.g., `--bg-dark`, `--panel-dark`).
3. **Leaflet tiles**: Checking `app.js` shows both `mapCongestion` and `mapReplay` are configured with view `[-25.43, -49.27]`, zoom `13`, and tiles from `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png` (CartoDB Dark Matter).
4. **Data Directories**: A global grep search for `dados_c3sl`, `dados_em_tempo_real_2026`, and `dados_processados` reveals they are referenced throughout the ETL process (`load_c3sl.py`, `load_realtime.py`, `build_event_log.py`) and various scratch scripts. A refactoring to move these directories under `data/` will require updating these variables/parameters.
5. **Endpoints**: Examining `dashboard.py` reveals that the endpoint `/api/lines` loads all bus lines present in both regimes by default. In `app.js`, regime selection radio buttons unlock the filters panel and call `loadCommonLines()`, which queries `/api/lines` without sending filters.

---

## 3. Caveats

- We assumed that only emojis in tabs, headers, panel headers, and table section headers are to be removed (per instructions). Emojis used in map tooltips, dropdown placeholders (e.g., `🚌`), or other sub-elements were kept if they did not constitute headers or tabs.
- No testing or code execution was performed due to local environment permission prompt timeouts. However, static code analysis is sufficient for this exploration phase.

---

## 4. Conclusion

- Emojis in headers/tabs exist only in `src/visualization/static/index.html`.
- The current dark CSS theme utilizes CSS variables; refactoring to a light theme requires altering these variables or style definitions.
- Leaflet maps currently use CartoDB Dark Matter tiles, which must be swapped for CartoDB Positron tiles for a light theme.
- Data folder paths are hardcoded as default parameters or constants in the backend python files and must be updated to reference `data/` subdirectory.
- The `GET /api/lines` endpoint must be rewritten to receive regime/date parameters and filter options from `data/dados_processados` instead of calculating intersection on raw files.

---

## 5. Verification Method

To independently verify the observations:
1. Open and inspect `src/visualization/static/index.html` to locate the emojis at the specified lines.
2. Open `src/visualization/static/styles.css` to review `:root` variable colors.
3. Open `src/visualization/static/app.js` and inspect lines 473–482 to confirm map configuration and CartoDB Dark Matter tile provider URL.
4. Run the FastAPI application locally:
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn src.visualization.dashboard:app --reload
   ```
   Open `http://localhost:8000/` and verify that the page loads correctly and is currently in Dark Mode.
