# Original User Request

## 2026-06-16T19:41:27Z

Refactor the URBS process mining dashboard website by removing emojis from tabs and headers, filtering the bus line selector to show only processed lines for the selected regime, applying a clean and light visual theme inspired by bootstack.vercel.app, and reorganizing the repository folders (moving data directories under a central data/ folder).

Working directory: c:\GIT\tcc-urbs
Integrity mode: development

## Requirements

### R1. Remove Emojis from Tabs and Map Headers
Remove emojis from the following UI locations:
- Tab navigation buttons (e.g. 🗺️, 🧭, 🔍, ⚡).
- Headers of the maps, tab panels, and table sections (e.g. 🗺️, 🚌, 🧭, 🔍, ⚡, 🚫, ⚠️).
*Note: Keep the bus emoji (🚌) in the sidebar logo header and in the active bus markers on the map replay simulation.*

### R2. Filter Bus Lines by Processed Data
Adjust the sidebar bus line selector to dynamically display only the options for which processed data is available under the selected regime/period.
- If Regime A (Oct/25) is selected, show only lines with processed data for that date range in `data/dados_processados` (e.g., 010, 226, 500, 541).
- If Regime B (Dec/25) is selected, show only lines with processed data for that date range in `data/dados_processados` (e.g., 541, 542, 549).
- If no dates or an arbitrary date range is selected, scan `data/dados_processados` and display all unique line codes found. If none are found, fall back to listing the raw GPS lines so the user can process them.

### R3. Light Clean Theme Redesign (Inspired by BootStack)
Redesign the theme and aesthetics of the website to be light and clean, inspired by the style of https://bootstack.vercel.app/:
- Use a light/off-white background (e.g., `#fafafa` or `#f9fafb`) and white panels (`#ffffff`).
- Main text should be dark gray/black (`#111827` or `#171717`) and muted text should be medium gray (`#6b7280` or `#737373`).
- Use thin, clean borders (e.g., `1px solid #e5e7eb` or similar).
- Active tabs and primary buttons should have high-contrast solid dark/neutral backgrounds with white text and rounded/fully rounded borders.
- Update the Leaflet maps in `app.js` to use a light clean tile provider (like CartoDB Positron: `https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png`) instead of the current dark base layer.
- Ensure all inputs, console logging outputs, tables, and KPIs are visually polished and readable under the light theme.

### R4. Reorganize Repository Folder Structure
Clean up the repository structure:
- Create a central `data` folder in the root directory.
- Move the folders `dados_c3sl`, `dados_em_tempo_real_2026`, and `dados_processados` into the new `data` folder.
- Move the `download_c3sl.py` script from the root to `src/etl/`.
- Update all Python imports, file reading/writing references, and shell/config scripts to point to the new paths (e.g. `data/dados_processados`, `src/etl/download_c3sl.py`) to ensure the application builds and runs successfully.

## Acceptance Criteria

### UI Visuals & Emojis
- [ ] Emojis are removed from tab buttons and section headers. Emojis remain in the sidebar logo and the bus markers on the map replay.
- [ ] The entire dashboard has a clean, off-white light theme with dark gray text, thin light gray borders, and high-contrast dark buttons.
- [ ] Leaflet maps use the CartoDB Positron light theme tiles.

### Data Filtering
- [ ] Changing the regime (A or B) correctly updates the bus line dropdown options to show only the lines that have corresponding processed CSV files in `data/dados_processados`.

### Reorganization & Execution
- [ ] Folder structure is organized: data directories are under `data/`, and `download_c3sl.py` is under `src/etl/`.
- [ ] The Python FastAPI backend and Javascript frontend run successfully without errors, and all features (loading lines, checking trips, loading maps, replay, discovery, conformance, and performance tabs) work correctly using the new folder paths.
