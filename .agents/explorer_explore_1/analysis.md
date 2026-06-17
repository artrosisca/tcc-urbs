# Codebase Investigation Analysis

This report documents the findings from investigating the `tcc-urbs` codebase.

---

## 1. Emoji Usage in Headers and Tabs

Emojis are used exclusively within the frontend markup of the dashboard (`src/visualization/static/index.html`). Here is the complete list of files, lines, and contexts:

### `src/visualization/static/index.html`

- **Line 19**: `<span class="logo-icon">🚌</span>` (Sidebar Logo Icon - *Note: This is to be kept per requirements.*)
- **Line 151**: `<button class="tab-btn active" data-tab="tab-mapa">🗺️ Aba 1: Mapas Geográficos de Operação</button>` (Tab Button 1)
- **Line 152**: `<button class="tab-btn" data-tab="tab-descoberta">🧭 Aba 2: Descoberta de Processos</button>` (Tab Button 2)
- **Line 153**: `<button class="tab-btn" data-tab="tab-conformidade">🔍 Aba 3: Auditoria & Conformidade</button>` (Tab Button 3)
- **Line 154**: `<button class="tab-btn" data-tab="tab-desempenho">⚡ Aba 4: Desempenho & Gargalos</button>` (Tab Button 4)
- **Line 163**: `<h2>🗺️ Visualização de Mapas CCO Integrados</h2>` (Aba 1 - Panel Header)
- **Line 178**: `<h3>🗺️ Mapa A: Gargalos e Trechos (Velocidade Média)</h3>` (Aba 1 - Map A Box Header)
- **Line 195**: `<h3>🚌 Mapa B: Replay da Frota (Simulador Histórico)</h3>` (Aba 1 - Map B Box Header)
- **Line 226**: `<h2>🧭 Rede de Petri Descoberta (Inductive Miner)</h2>` (Aba 2 - Panel Header)
- **Line 233**: `<button id="btn-zoom-in-desc" class="btn-sm">🔍 +</button>` (Aba 2 - Zoom In Button)
- **Line 234**: `<button id="btn-zoom-out-desc" class="btn-sm">🔍 -</button>` (Aba 2 - Zoom Out Button)
- **Line 248**: `<h2>🔍 Auditoria de Fidelidade de Rota (Token-Based Replay)</h2>` (Aba 3 - Panel Header)
- **Line 271**: `<h3>🚫 Pontos Mais Pulados/Ignorados</h3>` (Aba 3 - Table Section Header)
- **Line 292**: `<h3>⚠️ Detalhes de Viagens com Maior Desvio</h3>` (Aba 3 - Table Section Header)
- **Line 319**: `<h2>⚡ Directly-Follows Graph (DFG) de Tempos Operacionais</h2>` (Aba 4 - Panel Header)
- **Line 326**: `<button id="btn-zoom-in-des" class="btn-sm">🔍 +</button>` (Aba 4 - Zoom In Button)
- **Line 327**: `<button id="btn-zoom-out-des" class="btn-sm">🔍 -</button>` (Aba 4 - Zoom Out Button)

*Note: In `src/visualization/static/app.js` (line 657), the bus emoji (`🚌`) is used inside HTML to define the divIcon for Leaflet markers on the replay simulation map: `html: '<div class="bus-animation-icon">🚌</div>'`. Per the requirements, this emoji should be kept.*

---

## 2. CSS Styling, Theme, and Leaflet Maps Configuration

### Current CSS Theme (`src/visualization/static/styles.css`)
- **Theme Archetype**: Global CCO Dark Theme.
- **Color Variables (`:root`)**:
  - `--bg-dark`: `#1e1e24` (background of the app)
  - `--panel-dark`: `#121214` (sidebar background, card panels, tables)
  - `--border-dark`: `#2d2d34` (thin borders between elements)
  - `--text-main`: `#f1f5f9` (bright text)
  - `--text-muted`: `#94a3b8` (secondary text)
  - `--accent-red`: `#ff4b4b` (deviant values/alerts)
  - `--accent-blue`: `#ffffff` (active tab bottom border color)
  - `--accent-green`: `#39e587` (conformance percentage/terminal output color)
  - `--accent-orange`: `#f59e0b` (primary buttons, active sliders, highlights)
- **Highlights**: The regime selection block (Passo 1) has a warm brownish-orange background (`#271a0c`) and a pulsing orange border to draw immediate attention.
- **Console styling**: The simulation console (`#log-console`) has a pitch black background (`#0c0c0e`) and uses a monospace font (`JetBrains Mono`) with bright green text.

### Leaflet Maps Configuration (`src/visualization/static/app.js`)
- **Initialization**: Inside function `renderMaps()`, maps are initialized only if they do not exist:
  - **Map A (Congestion Map)**: `mapCongestion = L.map('map-congestion').setView([-25.43, -49.27], 13);`
  - **Map B (Replay Map)**: `mapReplay = L.map('map-replay').setView([-25.43, -49.27], 13);`
- **Tile Layer**: Both maps use the CartoDB Dark Matter tile provider:
  - **URL**: `https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png`
  - **Attribution**: `&copy; OpenStreetMap &copy; CARTO`
- **Synchronization**: The panning and zooming of the two maps are synchronized:
  - `mapCongestion.on('drag', () => mapReplay.setView(mapCongestion.getCenter(), mapCongestion.getZoom(), {animate: false}));`
  - `mapCongestion.on('zoom', () => mapReplay.setZoom(mapCongestion.getZoom()));`

---

## 3. References to Data Directories and Scripts

The codebase references `dados_c3sl`, `dados_em_tempo_real_2026`, `dados_processados`, and the script `download_c3sl.py` in the following files and lines:

### A. `dados_c3sl`
- **`.gitignore` (Line 2)**: `dados_c3sl/`
- **`PROJECT.md` (Line 6)**: Mentioned in data folders description.
- **`PROJECT.md` (Line 20)**: `- data/dados_c3sl/ — Raw GPS data from C3SL (to be moved)`
- **`download_c3sl.py` (Line 9)**: `DEST_DIR = "dados_c3sl"`
- **`src/etl/load_c3sl.py` (Line 33)**: `def load_static_data(date_str, line_code, c3sl_dir="dados_c3sl"):`
- **`scratch/analyze_quality.py` (Lines 113, 132)**: Loading points/schedule data.
- **`scratch/explore_data.py` (Lines 13, 146)**: Unzipping JSON.xz files.
- **`scratch/explore_json.py` (Lines 5, 6, 7)**: File paths constants.
- **`scratch/explore_line541.py` (Lines 4, 5)**: File paths constants.
- **`scratch/explore_points_seq.py` (Line 5)**: Points JSON xz path.
- **`scratch/explore_shape.py` (Line 4)**: Shape JSON xz path.
- **`scratch/explore_shape_detail.py` (Line 5)**: Shape JSON xz path.
- **`scratch/explore_tabelalinha.py` (Line 5)**: Schedule JSON xz path.

### B. `dados_em_tempo_real_2026`
- **`.gitignore` (Line 1)**: `dados_em_tempo_real_2026/`
- **`PROJECT.md` (Line 6)**: Mentioned in data folders description.
- **`PROJECT.md` (Line 21)**: `- data/dados_em_tempo_real_2026/ — Real-time GPS data (to be moved)`
- **`download_c3sl.py` (Line 8)**: `DATA_DIR = "dados_em_tempo_real_2026"`
- **`download_c3sl.py` (Line 73)**: Print statements warning.
- **`src/etl/load_realtime.py` (Line 5)**: `def load_realtime_data(line_code, start_date, end_date, data_dir="dados_em_tempo_real_2026"):`
- **`src/visualization/dashboard.py` (Line 52)**: `def get_common_lines(data_dir="dados_em_tempo_real_2026"):`
- **`src/visualization/dashboard.py` (Line 164)**: `def check_raw_gps_data(..., data_dir="dados_em_tempo_real_2026"):`
- **`scratch/analyze_quality.py` (Line 16)**: Directory path.
- **`scratch/check_intervals.py` (Line 6)**: `DATA_DIR = 'dados_em_tempo_real_2026'`
- **`scratch/check_intervals_v2.py` (Line 5)**: `DATA_DIR = 'dados_em_tempo_real_2026'`
- **`scratch/explore_data.py` (Line 44)**: CSV directory path.
- **`scratch/find_intersection_lines.py` (Lines 5, 16)**: Directories for date folders.
- **`scratch/test_check.py` (Line 5)**: Parameter default value.

### C. `dados_processados`
- **`PROJECT.md` (Line 6)**: Mentioned in data folders description.
- **`PROJECT.md` (Line 22)**: `- data/dados_processados/ — Processed CSV event logs... (to be moved)`
- **`src/etl/build_event_log.py` (Line 9)**: `def build_event_log(..., output_dir="dados_processados"):`
- **`src/mining/conformance.py` (Line 159)**: `csv_path = "dados_processados/event_log_541_2025-10-24_2025-10-24.csv"`
- **`src/mining/discovery.py` (Lines 5, 81, 91)**: Directory and file references.
- **`src/mining/performance.py` (Line 206)**: `csv_path = "dados_processados/event_log_541_2025-10-24_2025-10-24.csv"`
- **`src/visualization/dashboard.py` (Lines 136, 258, 301, 530, 579, 640)**: Build output directory parameter and event log CSV file references.
- **`scratch/check_replay_keys.py` (Line 6)**: `df = pd.read_csv('dados_processados/event_log_541...')`
- **`scratch/run_evaluation.py` (Line 88)**: `output_path = "dados_processados/comparativo_tcc.md"`

### D. `download_c3sl.py`
- **`PROJECT.md` (Line 24)**: `- src/etl/download_c3sl.py — Raw data download script (to be moved)`

---

## 4. Endpoints & Frontend Logic for Bus Lines Retrieval and Display

### Backend Endpoints
The backend server is defined in `src/visualization/dashboard.py` using FastAPI.

1. **`GET /api/lines`** (Lines 113–120):
   - **Purpose**: Returns the list of bus lines that are common to both regimes/periods (Oct/25 and Dec/25).
   - **Implementation**: Calls `get_common_lines()`.
   - **`get_common_lines()`** (Lines 52–77):
     - Scans `dados_em_tempo_real_2026/2025-10-24` and `dados_em_tempo_real_2026/2025-12-02` (the dates for Regime A and Regime B).
     - Extracts the unique `CODIGOLINHA` values from all CSV files in those directories.
     - Computes the intersection between the two sets (common lines).
     - Excludes line `'REC'` and lines starting with `'X'`.
     - Returns the sorted list.

2. **`GET /api/check-trips`** (Lines 256–297):
   - **Purpose**: Verifies if there are processed journeys in `dados_processados` for the given line, date range, and hour range. If not, it falls back to scanning the raw GPS points in `dados_em_tempo_real_2026` to determine if raw data exists to be mined.

### Frontend Fetching & Regime Selection Logic (`src/visualization/static/app.js`)

1. **Regime Selection**:
   - The user selects a regime ("A" or "B") using the radio button inputs.
   - Selection triggers an event listener (Lines 74–122):
     - Visual overlay wrapper `#locked-filters-container` is unlocked (`.unlocked` class is added, and the `disabled` property is removed from all inner controls).
     - Sets default dates in `activeFilters`:
       - **Regime A**: `startDate = "2025-10-24"`, `endDate = "2025-10-30"`.
       - **Regime B**: `startDate = "2025-12-02"`, `endDate = "2025-12-08"`.
     - Triggers `loadCommonLines()`.

2. **Loading Lines (`loadCommonLines` function)** (Lines 170–205):
   - Performs a standard HTTP fetch to `/api/lines`.
   - Upon receiving the JSON array, it clears the `#select-linha` select element and appends an `<option>` element for each line.
   - Keeps the previously selected line selected if it is still available.
   - Automatically triggers `checkActiveLineData()`, which checks if the newly selected line has processed/raw data.

*Critical Assessment for Refactoring (R2)*: Currently, the `/api/lines` endpoint does not receive the selected regime/period as query parameters. It computes the intersection of lines available in both periods at startup. To filter lines by processed files for a specific regime, the frontend needs to pass the selected regime/date range to `/api/lines`, and the backend must scan `dados_processados` for matching files (e.g., matching the date patterns in the filenames).

---

## 5. How to Run/Start the Backend and Frontend

### Prerequisites
- Python 3.10+ (a `.venv` virtual environment is already present in the workspace).
- Dependencies installed from `requirements.txt`.

### Step 1: Activate Virtual Environment
On Windows (PowerShell):
```powershell
.\.venv\Scripts\Activate.ps1
```

### Step 2: Start the FastAPI Backend
Start the FastAPI server using `uvicorn`:
```bash
uvicorn src.visualization.dashboard:app --reload
```
Alternatively, run without explicit activation:
```powershell
.\.venv\Scripts\python.exe -m uvicorn src.visualization.dashboard:app --reload
```

### Step 3: Access the Frontend
FastAPI serves the static frontend assets automatically.
- The static folder is mounted at `/static` (mapped to `src/visualization/static`).
- The root route `/` returns `index.html`.
- Open your browser and navigate to:
  `http://localhost:8000/` or `http://127.0.0.1:8000/`
