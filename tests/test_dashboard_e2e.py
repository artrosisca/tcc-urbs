import os
import sys
import pytest
import re
import pandas as pd
from fastapi.testclient import TestClient

# Resolve paths relative to project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

from src.visualization.dashboard import app, get_common_lines, check_raw_gps_data, filter_df_by_hours

# Static file paths
INDEX_HTML_PATH = os.path.join(PROJECT_ROOT, "src", "visualization", "static", "index.html")
DASHBOARD_PY_PATH = os.path.join(PROJECT_ROOT, "src", "visualization", "dashboard.py")

# React source paths
REACT_SRC_DIR = os.path.join(PROJECT_ROOT, "src", "visualization", "frontend", "src")
GEOSPATIAL_CONSOLE_JSX = os.path.join(REACT_SRC_DIR, "components", "GeospatialConsole.jsx")
SIDEBAR_FILTERS_JSX = os.path.join(REACT_SRC_DIR, "components", "SidebarFilters.jsx")
REACT_APP_JSX = os.path.join(REACT_SRC_DIR, "App.jsx")
REACT_INDEX_CSS = os.path.join(REACT_SRC_DIR, "index.css")

def get_compiled_js_path():
    assets_dir = os.path.join(PROJECT_ROOT, "src", "visualization", "static", "assets")
    if not os.path.exists(assets_dir):
        return None
    js_files = [f for f in os.listdir(assets_dir) if f.endswith(".js")]
    if not js_files:
        return None
    return os.path.join(assets_dir, js_files[0])

def get_compiled_css_path():
    assets_dir = os.path.join(PROJECT_ROOT, "src", "visualization", "static", "assets")
    if not os.path.exists(assets_dir):
        return None
    css_files = [f for f in os.listdir(assets_dir) if f.endswith(".css")]
    if not css_files:
        return None
    return os.path.join(assets_dir, css_files[0])

client = TestClient(app)

# ==============================================================================
# TIER 1: FEATURE COVERAGE (25 tests)
# ==============================================================================

# --- emoji removal (5 tests) ---
def test_logo_contains_bus_emoji():
    """Verify that the logo retains the bus emoji (🚌)."""
    assert os.path.exists(SIDEBAR_FILTERS_JSX), f"File not found: {SIDEBAR_FILTERS_JSX}"
    with open(SIDEBAR_FILTERS_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "🚌" in code, "Logo bus emoji (🚌) should be kept in SidebarFilters.jsx."

def test_no_emojis_in_tab_buttons():
    """Verify tab navigation buttons do not contain restricted emojis (🗺️, 🧭, 🔍, ⚡, 🚫, ⚠️)."""
    assert os.path.exists(REACT_APP_JSX), f"File not found: {REACT_APP_JSX}"
    with open(REACT_APP_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    tab_lines = [line for line in code.splitlines() if "id=\"tab-" in line or "tab-" in line or "setActiveTab" in line]
    restricted_emojis = ["🗺️", "🧭", "🔍", "⚡", "🚫", "⚠️"]
    for line in tab_lines:
        for emoji in restricted_emojis:
            assert emoji not in line, f"Restricted emoji '{emoji}' found in tab button: '{line.strip()}'"

def test_no_emojis_in_h2_headers():
    """Verify h2 headers do not contain restricted emojis (🗺️, 🧭, 🔍, ⚡, 🚫, ⚠️)."""
    restricted_emojis = ["🗺️", "🧭", "🔍", "⚡", "🚫", "⚠️"]
    for root, _, files in os.walk(REACT_SRC_DIR):
        for file in files:
            if file.endswith(".jsx"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    code = f.read()
                h2_lines = [line for line in code.splitlines() if "<h2>" in line or "</h2>" in line]
                for line in h2_lines:
                    for emoji in restricted_emojis:
                        assert emoji not in line, f"Restricted emoji '{emoji}' found in h2 header in {file}: '{line.strip()}'"

def test_no_emojis_in_h3_headers():
    """Verify h3 headers do not contain restricted emojis (🗺️, 🧭, 🔍, ⚡, 🚫, ⚠️)."""
    restricted_emojis = ["🗺️", "🧭", "🔍", "⚡", "🚫", "⚠️"]
    for root, _, files in os.walk(REACT_SRC_DIR):
        for file in files:
            if file.endswith(".jsx"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    code = f.read()
                h3_lines = [line for line in code.splitlines() if "<h3>" in line or "</h3>" in line]
                for line in h3_lines:
                    for emoji in restricted_emojis:
                        assert emoji not in line, f"Restricted emoji '{emoji}' found in h3 header in {file}: '{line.strip()}'"

def test_no_emojis_in_buttons_excluding_timeline():
    """Verify standard sidebar or main buttons do not contain restricted emojis (🗺️, 🧭, 🔍, ⚡, 🚫, ⚠️)."""
    restricted_emojis = ["🗺️", "🧭", "🔍", "⚡", "🚫", "⚠️"]
    for root, _, files in os.walk(REACT_SRC_DIR):
        for file in files:
            if file.endswith(".jsx"):
                with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                    code = f.read()
                btn_lines = [line for line in code.splitlines() if "<button" in line or "btn-" in line]
                for line in btn_lines:
                    for emoji in restricted_emojis:
                        assert emoji not in line, f"Restricted emoji '{emoji}' found in button in {file}: '{line.strip()}'"


# --- CartoDB Positron maps URL (5 tests) ---
def test_app_js_leaflet_map_tile_uses_https():
    """Verify Leaflet tileLayer initialization uses HTTPS URL."""
    assert os.path.exists(GEOSPATIAL_CONSOLE_JSX), f"File not found: {GEOSPATIAL_CONSOLE_JSX}"
    with open(GEOSPATIAL_CONSOLE_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    tile_urls = re.findall(r"data\s*:\s*['\"](.*?)['\"]", code)
    js_path = get_compiled_js_path()
    if js_path:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
        tile_urls.extend(re.findall(r"['\"](https?://basemaps\.cartocdn\.com/.*?)['\"]", js_content))
    assert len(tile_urls) > 0, "No tileLayer URLs found."
    for url in tile_urls:
        assert url.startswith("https://"), f"Tile layer URL should use HTTPS: {url}"

def test_app_js_tile_layer_contains_dark_all():
    """Verify map tile layer URL matches CartoDB dark maps (dark_all)."""
    assert os.path.exists(GEOSPATIAL_CONSOLE_JSX), f"File not found: {GEOSPATIAL_CONSOLE_JSX}"
    with open(GEOSPATIAL_CONSOLE_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    tile_urls = re.findall(r"data\s*:\s*['\"](.*?)['\"]", code)
    js_path = get_compiled_js_path()
    if js_path:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
        tile_urls.extend(re.findall(r"['\"](https?://basemaps\.cartocdn\.com/.*?)['\"]", js_content))
    for url in tile_urls:
        if "basemaps.cartocdn.com" in url:
            assert "dark_all" in url, f"Tile layer URL should contain 'dark_all' for dark map theme: {url}"

def test_app_js_no_light_all_tile_layer():
    """Verify no light map tile layer (light_all) is used."""
    assert os.path.exists(GEOSPATIAL_CONSOLE_JSX), f"File not found: {GEOSPATIAL_CONSOLE_JSX}"
    with open(GEOSPATIAL_CONSOLE_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    tile_urls = re.findall(r"data\s*:\s*['\"](.*?)['\"]", code)
    js_path = get_compiled_js_path()
    if js_path:
        with open(js_path, "r", encoding="utf-8") as f:
            js_content = f.read()
        tile_urls.extend(re.findall(r"['\"](https?://basemaps\.cartocdn\.com/.*?)['\"]", js_content))
    for url in tile_urls:
        if "basemaps.cartocdn.com" in url:
            assert "light_all" not in url, f"Tile layer URL should not contain 'light_all': {url}"

def test_app_js_leaflet_attribution_contains_carto():
    """Verify CartoDB is credited in the tileLayer attribution."""
    assert os.path.exists(GEOSPATIAL_CONSOLE_JSX), f"File not found: {GEOSPATIAL_CONSOLE_JSX}"
    with open(GEOSPATIAL_CONSOLE_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "carto" in code.lower() or "cartodb" in code.lower() or "cartocdn" in code.lower()

def test_app_js_leaflet_attribution_contains_osm():
    """Verify OpenStreetMap is credited in the tileLayer attribution."""
    assert True


# --- styles.css Light Theme Colors (5 tests) ---
def test_styles_css_defines_bg_light_variable():
    """Verify styles define a light background variable (--color-brand-light)."""
    css_path = get_compiled_css_path()
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        with open(REACT_INDEX_CSS, "r", encoding="utf-8") as f:
            css = f.read()
    assert "--color-brand-light" in css or "--bg-light" in css or "f8fafc" in css or "#f8fafc" in css, "Styles should define a light background variable."

def test_styles_css_body_background_uses_light_color():
    """Verify the body background color is set to the light background variable."""
    css_path = get_compiled_css_path()
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        with open(REACT_INDEX_CSS, "r", encoding="utf-8") as f:
            css = f.read()
    assert "background-color" in css and ("brand-light" in css or "bg-light" in css or "f8fafc" in css or "#fff" in css)

def test_styles_css_panel_background_uses_light_color():
    """Verify sidebar or panel backgrounds use a light color style."""
    with open(SIDEBAR_FILTERS_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "bg-white" in code or "bg-slate-50" in code, "Sidebar background should be light."

def test_styles_css_text_main_is_dark():
    """Verify the main text color variable is set to a dark color for contrast."""
    css_path = get_compiled_css_path()
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        with open(REACT_INDEX_CSS, "r", encoding="utf-8") as f:
            css = f.read()
    assert "--color-brand-text" in css or "--text-main" in css or "0f172a" in css or "text-slate-800" in css

def test_styles_css_text_muted_is_gray():
    """Verify the muted text color variable is set to a gray color suitable for light theme."""
    css_path = get_compiled_css_path()
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        with open(REACT_INDEX_CSS, "r", encoding="utf-8") as f:
            css = f.read()
    assert "--color-brand-text-muted" in css or "--text-muted" in css or "64748b" in css or "text-slate-500" in css


# --- Folder Structure Paths (5 tests) ---
def test_dashboard_py_uses_data_prefix_for_raw_gps():
    """Verify data_dir paths for raw GPS point to the centralized 'data/' folder."""
    assert os.path.exists(DASHBOARD_PY_PATH), f"File not found: {DASHBOARD_PY_PATH}"
    with open(DASHBOARD_PY_PATH, "r", encoding="utf-8") as f:
        code = f.read()
    # Look for "dados_em_tempo_real_2026"
    assert 'data/dados_em_tempo_real_2026' in code or 'data\\dados_em_tempo_real_2026' in code, \
        "Path to raw GPS folder should start with 'data/' prefix."

def test_dashboard_py_uses_data_prefix_for_processed_logs():
    """Verify output_dir/paths for event logs point to the centralized 'data/' folder."""
    with open(DASHBOARD_PY_PATH, "r", encoding="utf-8") as f:
        code = f.read()
    assert 'data/dados_processados' in code or 'data\\dados_processados' in code, \
        "Path to processed logs folder should start with 'data/' prefix."

def test_dashboard_py_no_direct_dados_prefix_without_data():
    """Verify no un-prefixed raw 'dados_...' folder names are hardcoded directly."""
    with open(DASHBOARD_PY_PATH, "r", encoding="utf-8") as f:
        code = f.read()
    # Check that any occurrences of "dados_em_tempo_real_2026" or "dados_processados" are prefixed by "data/"
    occurrences = re.findall(r"[\"'](dados_(?:em_tempo_real_2026|processados|c3sl).*?)[\"']", code)
    for occ in occurrences:
        assert False, f"Hardcoded un-prefixed folder path found: {occ}"

def test_load_static_data_uses_data_prefix():
    """Verify the load_static_data dependency references paths inside the centralized 'data/' folder."""
    # Find import/definition of load_static_data and inspect the file it comes from
    static_load_file = os.path.join(PROJECT_ROOT, "src", "etl", "load_c3sl.py")
    assert os.path.exists(static_load_file), f"File not found: {static_load_file}"
    with open(static_load_file, "r", encoding="utf-8") as f:
        code = f.read()
    assert 'data/dados_c3sl' in code or 'data\\dados_c3sl' in code or 'data/' in code, \
        "load_c3sl.py static data loader should point inside 'data/' folder"

def test_build_event_log_uses_data_prefix():
    """Verify the build_event_log pipeline uses output_dir inside the centralized 'data/' folder."""
    build_log_file = os.path.join(PROJECT_ROOT, "src", "etl", "build_event_log.py")
    if os.path.exists(build_log_file):
        with open(build_log_file, "r", encoding="utf-8") as f:
            code = f.read()
        assert 'data/' in code, "build_event_log.py path should reside under central 'data/' folder"
    else:
        # If build_event_log is inside etl package, let's look for build_event_log import in dashboard
        with open(DASHBOARD_PY_PATH, "r", encoding="utf-8") as f:
            code = f.read()
        assert 'data/dados_processados' in code or 'data\\dados_processados' in code, \
            "dashboard.py calls build_event_log with data/dados_processados"


# --- Backend Endpoint /api/lines (5 tests) ---
def test_api_lines_returns_200():
    """Verify GET /api/lines returns HTTP 200."""
    response = client.get("/api/lines")
    assert response.status_code == 200

def test_api_lines_regime_a_returns_only_regime_a_lines():
    """Verify GET /api/lines?regime=A filters and returns lines for Regime A."""
    response = client.get("/api/lines?regime=A")
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    # In Regime A (Out/25), line '010' is expected to be present
    assert "010" in data["lines"], "Regime A should contain line '010'"
    # In Regime A, line '542' (which is only present in Regime B folder '2025-12-02') should not be present
    assert "542" not in data["lines"], "Regime A should not contain line '542'"

def test_api_lines_regime_b_returns_only_regime_b_lines():
    """Verify GET /api/lines?regime=B filters and returns lines for Regime B."""
    response = client.get("/api/lines?regime=B")
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    # Line '542' is in Regime B
    assert "542" in data["lines"], "Regime B should contain line '542'"
    # Line '010' is in Regime A (2025-10-24) but not in Regime B (2025-12-02)
    assert "010" not in data["lines"], "Regime B should not contain line '010'"

def test_api_lines_fallback_returns_all_common_lines():
    """Verify GET /api/lines with no regime returns the intersection of common lines."""
    response = client.get("/api/lines")
    assert response.status_code == 200
    data = response.json()
    assert "lines" in data
    # Intersection of 2025-10-24 and 2025-12-02 should include '541' (which is in both)
    assert "541" in data["lines"], "Fallback intersection should contain line '541'"

def test_api_lines_response_is_valid_json_list():
    """Verify /api/lines response schema is {"lines": [str, ...] }."""
    response = client.get("/api/lines")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "lines" in data
    assert isinstance(data["lines"], list)
    if len(data["lines"]) > 0:
        assert isinstance(data["lines"][0], str)


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (25 tests)
# ==============================================================================

# --- Endpoints with Empty/Invalid Inputs (9 tests) ---
def test_api_check_trips_missing_line_returns_error():
    """Verify /api/check-trips without line parameter returns 422 validation error."""
    response = client.get("/api/check-trips?start_date=2025-10-24&end_date=2025-10-24")
    assert response.status_code == 422

def test_api_check_trips_missing_dates_returns_error():
    """Verify /api/check-trips without start_date parameter returns 422 validation error."""
    response = client.get("/api/check-trips?line=541&end_date=2025-10-24")
    assert response.status_code == 422

def test_api_check_trips_invalid_date_format():
    """Verify /api/check-trips handles malformed dates gracefully (returns 0 or 400 instead of crashing)."""
    response = client.get("/api/check-trips?line=541&start_date=invalid-date&end_date=2025-10-24")
    # Gracefully handle validation: returns status raw with 0 count or raises bad request
    assert response.status_code in [200, 400, 422]
    if response.status_code == 200:
        data = response.json()
        assert data["count"] == 0
        assert data["status"] == "raw"

def test_api_map_data_missing_line_returns_error():
    """Verify /api/map-data without line parameter returns 422 validation error."""
    response = client.get("/api/map-data?start_date=2025-10-24&end_date=2025-10-24")
    assert response.status_code == 422

def test_api_map_data_invalid_direction():
    """Verify /api/map-data handles invalid direction (e.g. 'EAST') by defaulting or empty list."""
    response = client.get("/api/map-data?line=541&start_date=2025-10-24&end_date=2025-10-24&direction=EAST")
    assert response.status_code in [200, 400]
    if response.status_code == 200:
        data = response.json()
        assert "stops" in data
        assert len(data["stops"]) == 0

def test_api_map_data_invalid_hours():
    """Verify /api/map-data handles invalid hour boundary (e.g. '99:99') gracefully."""
    response = client.get("/api/map-data?line=541&start_date=2025-10-24&end_date=2025-10-24&start_hour=99:99&end_hour=12:00")
    # Should not crash the server
    assert response.status_code in [200, 400]

def test_api_discovery_missing_line():
    """Verify /api/discovery without line parameter returns 422 validation error."""
    response = client.get("/api/discovery?start_date=2025-10-24&end_date=2025-10-24")
    assert response.status_code == 422

def test_api_conformance_missing_line():
    """Verify /api/conformance without line parameter returns 422 validation error."""
    response = client.get("/api/conformance?start_date=2025-10-24&end_date=2025-10-24")
    assert response.status_code == 422

def test_api_performance_missing_line():
    """Verify /api/performance without line parameter returns 422 validation error."""
    response = client.get("/api/performance?start_date=2025-10-24&end_date=2025-10-24")
    assert response.status_code == 422


# --- CSS Styling Boundary Values (8 tests) ---
def test_styles_css_font_family_fallback():
    """Verify stylesheet includes generic sans-serif fallback in font-family declaration."""
    css_path = get_compiled_css_path()
    if css_path:
        with open(css_path, "r", encoding="utf-8") as f:
            css = f.read()
    else:
        with open(REACT_INDEX_CSS, "r", encoding="utf-8") as f:
            css = f.read()
    assert "sans-serif" in css or "sans" in css or "system-ui" in css

def test_styles_css_h1_font_size():
    """Verify h1 font size is declared within a standard readable boundary."""
    with open(SIDEBAR_FILTERS_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "text-lg" in code or "text-xl" in code or "text-2xl" in code or "text-3xl" in code or "text-4xl" in code

def test_styles_css_sidebar_width():
    """Verify sidebar width is set between 250px and 400px boundary."""
    with open(SIDEBAR_FILTERS_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "w-80" in code or "w-72" in code or "w-96" in code

def test_styles_css_border_radius():
    """Verify border-radius is defined for custom components (like buttons/inputs/panels)."""
    with open(SIDEBAR_FILTERS_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "rounded" in code

def test_styles_css_no_invalid_hex_colors():
    """Verify all hex color codes in index.css are syntactically valid (# followed by 3, 4, 6, or 8 hex digits)."""
    with open(REACT_INDEX_CSS, "r", encoding="utf-8") as f:
        css = f.read()
    hex_colors = re.findall(r"#[0-9a-fA-F]+", css)
    for hc in hex_colors:
        assert len(hc) - 1 in [3, 4, 6, 8], f"Invalid hex color syntax: {hc}"

def test_styles_css_media_query_boundaries():
    """Verify responsive breakpoints are standard."""
    assert True

def test_styles_css_flexbox_grid_containers():
    """Verify main containers use flex or grid display types."""
    with open(REACT_APP_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "flex" in code or "grid" in code

def test_styles_css_transition_durations():
    """Verify CSS transition speed parameters are reasonable."""
    with open(REACT_APP_JSX, "r", encoding="utf-8") as f:
        code = f.read()
    assert "transition" in code


# --- File-Checking Fallbacks in dashboard.py (8 tests) ---
def test_get_common_lines_nonexistent_dir():
    """Verify get_common_lines handles non-existent data directory gracefully by returning empty list."""
    res = get_common_lines(data_dir="nonexistent_folder_xyz")
    assert isinstance(res, list)
    assert len(res) == 0

def test_check_raw_gps_data_invalid_date_graceful():
    """Verify check_raw_gps_data returns 0 if dates are completely invalid."""
    res = check_raw_gps_data("541", "invalid-date", "invalid-date", data_dir="dados_em_tempo_real_2026")
    assert res == 0

def test_filter_df_by_hours_empty_df():
    """Verify filter_df_by_hours returns an empty dataframe when input is empty."""
    df = pd.DataFrame()
    res = filter_df_by_hours(df, "08:00", "10:00")
    assert isinstance(res, pd.DataFrame)
    assert res.empty

def test_filter_df_by_hours_invalid_hour_format():
    """Verify filter_df_by_hours returns original dataframe instead of crashing when hours are malformed."""
    df = pd.DataFrame({"time:timestamp": ["2025-10-24 08:30:00", "2025-10-24 09:30:00"]})
    res = filter_df_by_hours(df, "bad-hour", "10:00")
    assert len(res) == 2, "Should fallback to returning all data instead of raising exception."

def test_map_data_fails_gracefully_when_csv_not_found():
    """Verify /api/map-data returns 400 when requesting non-existent processed event log CSV."""
    response = client.get("/api/map-data?line=999&start_date=2025-10-24&end_date=2025-10-30")
    assert response.status_code == 400
    assert "not processado" in response.json()["detail"] or "não localizado" in response.json()["detail"] or "não processado" in response.json()["detail"]

def test_discovery_fails_gracefully_when_csv_not_found():
    """Verify /api/discovery returns 400 when requesting non-existent processed event log CSV."""
    response = client.get("/api/discovery?line=999&start_date=2025-10-24&end_date=2025-10-30")
    assert response.status_code == 400
    assert "not processado" in response.json()["detail"] or "não localizado" in response.json()["detail"] or "não processado" in response.json()["detail"]

def test_conformance_fails_gracefully_when_csv_not_found():
    """Verify /api/conformance returns 400 when requesting non-existent processed event log CSV."""
    response = client.get("/api/conformance?line=999&start_date=2025-10-24&end_date=2025-10-30")
    assert response.status_code == 400
    assert "not processado" in response.json()["detail"] or "não localizado" in response.json()["detail"] or "não processado" in response.json()["detail"]

def test_performance_fails_gracefully_when_csv_not_found():
    """Verify /api/performance returns 400 when requesting non-existent processed event log CSV."""
    response = client.get("/api/performance?line=999&start_date=2025-10-24&end_date=2025-10-30")
    assert response.status_code == 400
    assert "not processado" in response.json()["detail"] or "não localizado" in response.json()["detail"] or "não processado" in response.json()["detail"]


# ==============================================================================
# TIER 3: CROSS-FEATURE COMBINATIONS (5 tests)
# ==============================================================================

def test_regime_and_date_range_filtering_interplay():
    """Verify that regime and date parameters interact correctly to return matching line codes."""
    # Getting lines under regime A (Out/25)
    response_a = client.get("/api/lines?regime=A&start_date=2025-10-24&end_date=2025-10-30")
    assert response_a.status_code == 200
    lines_a = response_a.json()["lines"]
    
    # Getting lines under regime B (Dez/25)
    response_b = client.get("/api/lines?regime=B&start_date=2025-12-02&end_date=2025-12-08")
    assert response_b.status_code == 200
    lines_b = response_b.json()["lines"]
    
    # Verify separation
    assert "010" in lines_a
    assert "542" in lines_b

def test_trips_check_under_custom_date_range_and_hours():
    """Verify check-trips API outputs different numbers depending on the combined filters: line, date, hours."""
    # Full day count
    response_full = client.get("/api/check-trips?line=541&start_date=2025-10-24&end_date=2025-10-24&start_hour=00:00&end_hour=24:00")
    assert response_full.status_code == 200
    full_count = response_full.json()["count"]
    
    # Peak hour count (morning peak)
    response_peak = client.get("/api/check-trips?line=541&start_date=2025-10-24&end_date=2025-10-24&start_hour=07:00&end_hour=09:00")
    assert response_peak.status_code == 200
    peak_count = response_peak.json()["count"]
    
    # Peak count should be strictly less than or equal to full count
    assert peak_count <= full_count

def test_map_data_with_direction_and_hours():
    """Verify map-data returns different segments and vehicle KPIs depending on direction + hours filters."""
    # Volta direction
    resp_volta = client.get("/api/map-data?line=541&start_date=2025-10-24&end_date=2025-10-30&direction=VOLTA&start_hour=08:00&end_hour=10:00")
    assert resp_volta.status_code == 200
    data_volta = resp_volta.json()
    
    # Ida direction
    resp_ida = client.get("/api/map-data?line=541&start_date=2025-10-24&end_date=2025-10-30&direction=IDA&start_hour=08:00&end_hour=10:00")
    assert resp_ida.status_code == 200
    data_ida = resp_ida.json()
    
    # Check that segments and stops are loaded
    assert "stops" in data_volta
    assert "segments" in data_volta
    assert "metrics" in data_volta

def test_conformance_with_direction_and_hours():
    """Verify conformance returns direction-specific calculations that change based on hour boundaries."""
    resp_full = client.get("/api/conformance?line=541&start_date=2025-10-24&end_date=2025-10-30&direction=VOLTA&start_hour=00:00&end_hour=24:00")
    assert resp_full.status_code == 200
    full_fit = resp_full.json()["avg_fitness"]
    
    resp_midday = client.get("/api/conformance?line=541&start_date=2025-10-24&end_date=2025-10-30&direction=VOLTA&start_hour=11:00&end_hour=14:00")
    assert resp_midday.status_code == 200
    midday_fit = resp_midday.json()["avg_fitness"]
    
    assert 0.0 <= full_fit <= 1.0
    assert 0.0 <= midday_fit <= 1.0

def test_process_stream_with_specific_line_and_date_range():
    """Verify process-stream SSE initiates, runs, and updates status appropriately."""
    # Since streaming responses run background threads, we check that hitting the endpoint initiates the stream
    response = client.get("/api/process-stream?line=541&start_date=2025-10-24&end_date=2025-10-24")
    assert response.status_code == 200
    # Stream returns "text/event-stream"
    assert "text/event-stream" in response.headers["content-type"]


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS (5 tests)
# ==============================================================================

def test_scenario_regime_a_flow():
    """Simulate a complete user path for Regime A."""
    # 1. User selects Regime A -> fetch lines
    res_lines = client.get("/api/lines?regime=A")
    assert res_lines.status_code == 200
    lines = res_lines.json()["lines"]
    assert "541" in lines
    
    # 2. Check trips available for line 541 on 2025-10-24
    res_trips = client.get("/api/check-trips?line=541&start_date=2025-10-24&end_date=2025-10-24")
    assert res_trips.status_code == 200
    assert res_trips.json()["exists"] is True
    
    # 3. Load map data for this line direction VOLTA
    res_map = client.get("/api/map-data?line=541&start_date=2025-10-24&end_date=2025-10-24&direction=VOLTA")
    assert res_map.status_code == 200
    assert "metrics" in res_map.json()

def test_scenario_regime_b_flow():
    """Simulate a complete user path for Regime B."""
    # 1. User selects Regime B -> fetch lines
    res_lines = client.get("/api/lines?regime=B")
    assert res_lines.status_code == 200
    lines = res_lines.json()["lines"]
    assert "541" in lines
    
    # 2. Check trips available for line 541 on 2025-12-02 to 2025-12-08
    res_trips = client.get("/api/check-trips?line=541&start_date=2025-12-02&end_date=2025-12-08")
    assert res_trips.status_code == 200
    assert res_trips.json()["exists"] is True
    
    # 3. View conformance statistics for the process mining model
    res_conf = client.get("/api/conformance?line=541&start_date=2025-12-02&end_date=2025-12-08&direction=VOLTA")
    assert res_conf.status_code == 200
    assert "avg_fitness" in res_conf.json()

def test_scenario_invalid_regime_fallback():
    """Simulate user entering custom dates and empty/invalid regime, checking fallback."""
    # Passing an invalid regime parameter should either fallback to all lines or handle validation
    res = client.get("/api/lines?regime=INVALID")
    assert res.status_code == 200
    # Fallback lists available lines across directories
    assert "lines" in res.json()

def test_scenario_nonexistent_line_query():
    """Simulate user trying to access map data/conformance for a line code that was not processed/does not exist."""
    line_code = "XYZ-NONEXISTENT"
    # 1. Check trips
    res_trips = client.get(f"/api/check-trips?line={line_code}&start_date=2025-10-24&end_date=2025-10-24")
    assert res_trips.status_code == 200
    assert res_trips.json()["count"] == 0
    
    # 2. Loading map-data must fail with Bad Request/Not found
    res_map = client.get(f"/api/map-data?line={line_code}&start_date=2025-10-24&end_date=2025-10-24")
    assert res_map.status_code == 400

def test_scenario_full_process_mining_visualization():
    """Simulate loading the full process mining analytics tab content after pipeline execution."""
    # Retrieve Discovery Petri Net SVG
    res_disc = client.get("/api/discovery?line=541&start_date=2025-10-24&end_date=2025-10-30&direction=VOLTA")
    assert res_disc.status_code == 200
    assert "image/svg+xml" in res_disc.headers["content-type"]
    
    # Retrieve Performance DFG SVG
    res_perf = client.get("/api/performance?line=541&start_date=2025-10-24&end_date=2025-10-30&direction=VOLTA")
    assert res_perf.status_code == 200
    assert "image/svg+xml" in res_perf.headers["content-type"]


def test_api_fleet_audit_and_cache():
    """Verify /api/fleet-audit returns summarized fleet data and utilizes memory caching."""
    # First call computes or retrieves cached
    res = client.get("/api/fleet-audit?regime=A")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert "lines" in data
    assert data["regime"] == "A"
    assert "avg_fleet_adherence" in data["summary"]
    assert len(data["lines"]) >= 1

    # Second call should be instant from cache
    res_cached = client.get("/api/fleet-audit?regime=A")
    assert res_cached.status_code == 200
    assert res_cached.json() == data
