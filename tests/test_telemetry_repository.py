"""
Unit tests for the deep TelemetryRepository and Storage Adapters module.
Tests data retrieval, line discovery by operational regime, and in-memory test fakes.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import pytest
import pandas as pd
from src.etl.repository import (
    TelemetryRepository,
    InMemoryTelemetryAdapter,
    FilesystemTelemetryAdapter,
    _parse_coord,
    _fix_encoding
)


def test_parse_coord_and_fix_encoding():
    """Verify coordinate parser and encoding repair utility functions."""
    assert _parse_coord("-25,5350") == -25.5350
    assert _parse_coord("-49.2710") == -49.2710
    assert _parse_coord(None) is None
    assert _parse_coord("invalid") is None
    
    # Latin-1 corrupted string repair
    text_latin1 = "Praca do Japao"
    assert _fix_encoding(text_latin1) == "Praca do Japao"


def test_in_memory_telemetry_adapter():
    """Verify repository operations using the InMemory test adapter."""
    stops_df = pd.DataFrame([{"SEQ": 1, "NOME": "Terminal Sítio Cercado"}])
    realtime_df = pd.DataFrame([
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.53, "LON": -49.27},
        {"COD": "VEH02", "CODIGOLINHA": "010", "LAT": -25.43, "LON": -49.27}
    ])
    processed_df = pd.DataFrame([{"case:concept:name": "C1", "time:timestamp": "2025-10-24 08:00:00"}])

    adapter = InMemoryTelemetryAdapter(
        static_data={'pontos': stops_df, 'tabela': pd.DataFrame(), 'shape': pd.DataFrame()},
        realtime_data=realtime_df,
        processed_logs={"541_2025-10-24_2025-10-24": processed_df},
        lines_by_regime={"A": ["541", "010"], "B": ["541", "542"]}
    )
    repo = TelemetryRepository(adapter=adapter)

    # 1. Static data
    static = repo.get_static_data("2025-10-24", "541")
    assert len(static['pontos']) == 1

    # 2. Line discovery
    lines_a = repo.list_available_lines(regime="A")
    lines_b = repo.list_available_lines(regime="B")
    assert "010" in lines_a and "542" not in lines_a
    assert "542" in lines_b and "010" not in lines_b

    # 3. Realtime filtering
    realtime_541 = repo.get_realtime_telemetry("541", "2025-10-24", "2025-10-24")
    assert len(realtime_541) == 1
    assert realtime_541["CODIGOLINHA"].iloc[0] == "541"

    # 4. Processed event log retrieval
    log = repo.get_processed_event_log("541", "2025-10-24", "2025-10-24")
    assert log is not None
    assert len(log) == 1

    # 5. Telemetry status check
    status_processed = repo.check_telemetry_status("541", "2025-10-24", "2025-10-24")
    assert status_processed["status"] == "processed"
    assert status_processed["count"] == 1

    status_raw = repo.check_telemetry_status("010", "2025-10-24", "2025-10-24")
    assert status_raw["status"] == "raw"


def test_filesystem_telemetry_adapter_graceful_fallbacks(tmp_path):
    """Verify filesystem adapter handles non-existent paths gracefully without crashing."""
    adapter = FilesystemTelemetryAdapter(base_data_dir=str(tmp_path))
    repo = TelemetryRepository(adapter=adapter)

    # Non-existent static data returns empty DataFrames
    static = repo.get_static_data("2025-10-24", "999")
    assert static['pontos'].empty
    assert static['tabela'].empty
    assert static['shape'].empty

    # Non-existent realtime data returns empty DataFrame
    realtime = repo.get_realtime_telemetry("999", "2025-10-24", "2025-10-24")
    assert realtime.empty

    # Non-existent processed log returns None
    processed = repo.get_processed_event_log("999", "2025-10-24", "2025-10-24")
    assert processed is None

    # Line listing returns empty list
    lines = repo.list_available_lines()
    assert isinstance(lines, list)
    assert len(lines) == 0
