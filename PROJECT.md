# Project: URBS Process Mining Dashboard Refactoring

## Architecture
- **Backend (Python FastAPI)**: Serves static frontend assets and exposes REST API endpoints for process mining, data retrieval, and dashboard stats (e.g. conformance, discovery, performance).
- **Frontend (HTML/CSS/JS)**: Renders a dashboard with a sidebar, Leaflet map, interactive filters (regime/period, bus lines), and tabs for process mining analysis.
- **Data (CSV/JSON)**: Stored in data folders (`dados_c3sl`, `dados_em_tempo_real_2026`, `dados_processados`) containing bus GPS data and processed event logs.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | E2E Testing Suite (Dual Track) | Design E2E test infra and write test cases for Tiers 1-4. | None | DONE |
| 2 | Codebase Exploration | Explore paths, emojis, theme, and python route files. | None | DONE |
| 3 | Repository Reorganization | Move data directories to central `data/`, move script, update paths. | M2 | PLANNED |
| 4 | Backend Route & Data Filtering | Update routes to dynamically list and filter bus lines by processed files. | M3 | PLANNED |
| 5 | Frontend Visual Redesign | Remove emojis, apply clean light theme, update Leaflet tiles. | M3 | PLANNED |
| 6 | Integration & Verification | Run all tests (Tiers 1-5), perform adversarial hardening. | M1, M4, M5 | PLANNED |

## Code Layout
- `data/` — Central data directory (to be created)
- `data/dados_c3sl/` — Raw GPS data from C3SL (to be moved)
- `data/dados_em_tempo_real_2026/` — Real-time GPS data (to be moved)
- `data/dados_processados/` — Processed CSV event logs for process mining (to be moved)
- `src/etl/` — Extraction, Transformation, and Load scripts
- `src/etl/download_c3sl.py` — Raw data download script (to be moved)
- `src/mining/` — Process mining logic (conformance, discovery, performance)
- `src/visualization/` — FastAPI backend & frontend dashboard
- `src/visualization/dashboard.py` — FastAPI application server
- `src/visualization/static/` — Frontend HTML, JS, CSS files

## Interface Contracts
### Frontend ↔ Backend REST API
- `GET /api/lines` — Returns list of available bus lines. Needs to support regime/period query params.
- `GET /api/trips` / `/api/data` — Custom routes for getting process mining data.
