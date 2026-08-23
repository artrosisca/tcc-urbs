"""
Unit tests for the deep TrajectoryReconstructor module.
Tests data cleaning, HMM Viterbi shape projection, PCHIP spline interpolation,
and event log synthesis with in-memory telemetry fixtures.
"""

import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.etl.trajectory import TrajectoryReconstructor, haversine_vectorized


@pytest.fixture
def sample_static_data():
    """Generates static stops and shape coordinate fixture."""
    stops_df = pd.DataFrame([
        {"SEQ": 1, "NUM": "101", "NOME": "Terminal Sítio Cercado", "SENTIDO": "VOLTA", "LAT": -25.5350, "LON": -49.2710},
        {"SEQ": 2, "NUM": "102", "NOME": "Praça do Japão", "SENTIDO": "VOLTA", "LAT": -25.4420, "LON": -49.2880},
        {"SEQ": 3, "NUM": "103", "NOME": "Praça Rui Barbosa", "SENTIDO": "VOLTA", "LAT": -25.4350, "LON": -49.2730},
    ])
    shape_df = pd.DataFrame([
        {"SHP": "SHP_1", "LAT": -25.5350, "LON": -49.2710},
        {"SHP": "SHP_1", "LAT": -25.4900, "LON": -49.2800},
        {"SHP": "SHP_1", "LAT": -25.4420, "LON": -49.2880},
        {"SHP": "SHP_1", "LAT": -25.4380, "LON": -49.2800},
        {"SHP": "SHP_1", "LAT": -25.4350, "LON": -49.2730},
    ])
    return {"pontos": stops_df, "shape": shape_df, "tabela": pd.DataFrame()}


@pytest.fixture
def sample_raw_telemetry():
    """Generates noisy raw telemetry DataFrame."""
    base_time = datetime(2025, 10, 24, 8, 0, 0)
    records = [
        # Near Stop 1 (-25.5350, -49.2710)
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5348, "LON": -49.2712, "request_timestamp": (base_time + timedelta(minutes=0)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5330, "LON": -49.2715, "request_timestamp": (base_time + timedelta(minutes=4)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # Near Stop 2 (-25.4420, -49.2880)
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.4418, "LON": -49.2878, "request_timestamp": (base_time + timedelta(minutes=8)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # Near Stop 3 (-25.4350, -49.2730)
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.4352, "LON": -49.2728, "request_timestamp": (base_time + timedelta(minutes=12)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # Stationary duplicate point (< 5m from previous)
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.4352001, "LON": -49.2728001, "request_timestamp": (base_time + timedelta(minutes=13)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # REC / garage point to filter
        {"COD": "VEH02", "CODIGOLINHA": "REC", "LAT": -25.5000, "LON": -49.3000, "request_timestamp": (base_time + timedelta(minutes=5)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
        # Null coordinates point to filter
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": np.nan, "LON": np.nan, "request_timestamp": (base_time + timedelta(minutes=15)).strftime("%Y-%m-%d %H:%M:%S"), "SENT": "VOLTA", "SITUACAO": "OP", "TABELA": "1"},
    ]
    return pd.DataFrame(records)


def test_haversine_vectorized():
    """Verify haversine distance calculation."""
    # Distance between ~1 degree of latitude is approx 111 km
    lat1 = np.array([-25.0])
    lon1 = np.array([-49.0])
    lat2 = np.array([-26.0])
    lon2 = np.array([-49.0])
    dist = haversine_vectorized(lat1, lon1, lat2, lon2)[0]
    assert 110000 < dist < 112000


def test_clean_telemetry(sample_raw_telemetry, sample_static_data):
    """Verify raw GPS data cleaning filters invalid, stationary, and garage points."""
    cleaned = TrajectoryReconstructor.clean_telemetry(sample_raw_telemetry, sample_static_data["pontos"])
    assert not cleaned.empty
    assert (cleaned["CODIGOLINHA"] != "REC").all()
    assert cleaned["LAT"].isna().sum() == 0
    assert cleaned["LON"].isna().sum() == 0
    # Stationary jitter filtered
    assert len(cleaned) == 4


def test_map_gps_to_shape_hmm(sample_static_data):
    """Verify HMM Viterbi projection onto shape geometry."""
    shape_df = sample_static_data["shape"]
    gps_lats = np.array([-25.5348, -25.4895, -25.4418, -25.4352])
    gps_lons = np.array([-49.2712, -49.2802, -49.2878, -49.2728])
    
    indices = TrajectoryReconstructor.map_gps_to_shape_hmm(
        gps_lats, gps_lons,
        shape_df["LAT"].values, shape_df["LON"].values
    )
    assert len(indices) == 4
    # Monotonic progression
    assert (np.diff(indices) >= 0).all()


def test_resolve_route_geometry(sample_static_data):
    """Verify dynamic route direction and shape resolution."""
    sentido_static, stops_filtered, shape_filtered = TrajectoryReconstructor.resolve_route_geometry(
        sample_static_data,
        direction="VOLTA"
    )
    assert sentido_static == "VOLTA"
    assert len(stops_filtered) == 3
    assert len(shape_filtered) == 5
    assert "shape_idx" in stops_filtered.columns


def test_match_trip(sample_raw_telemetry, sample_static_data):
    """Verify single trip stop passage matching and PCHIP spline interpolation."""
    cleaned = TrajectoryReconstructor.clean_telemetry(sample_raw_telemetry, sample_static_data["pontos"])
    events_df = TrajectoryReconstructor.match_trip(cleaned, sample_static_data, line_code="541")
    
    assert isinstance(events_df, pd.DataFrame)
    assert len(events_df) == 3  # Visited/interpolated all 3 stops
    assert "timestamp" in events_df.columns
    assert "stop_seq" in events_df.columns
    # Timestamps strictly increase
    timestamps = pd.to_datetime(events_df["timestamp"])
    assert (timestamps.diff().dropna().dt.total_seconds() > 0).all()


def test_reconstruct_event_log(sample_raw_telemetry, sample_static_data):
    """Verify full end-to-end event log synthesis."""
    df_log = TrajectoryReconstructor.reconstruct_event_log(
        sample_raw_telemetry,
        sample_static_data,
        line_code="541"
    )
    assert isinstance(df_log, pd.DataFrame)
    assert not df_log.empty
    assert "case:concept:name" in df_log.columns
    assert "concept:name" in df_log.columns
    assert "time:timestamp" in df_log.columns
    assert df_log["concept:name"].str.startswith("PASSAGEM_").all()


def test_calculate_segment_speeds(sample_raw_telemetry, sample_static_data):
    """Verify segment speed aggregation and color coding."""
    df_log = TrajectoryReconstructor.reconstruct_event_log(
        sample_raw_telemetry,
        sample_static_data,
        line_code="541"
    )
    sentido, stops_f, shape_f = TrajectoryReconstructor.resolve_route_geometry(sample_static_data, "VOLTA")
    segments = TrajectoryReconstructor.calculate_segment_speeds(df_log, shape_f, stops_f)
    
    assert isinstance(segments, list)
    assert len(segments) == 2  # 3 stops = 2 segments
    for seg in segments:
        assert "from_stop" in seg
        assert "to_stop" in seg
        assert "speed" in seg
        assert "color" in seg
        assert seg["color"] in ["#ff4b4b", "#f59e0b", "#ffffff"]


def test_build_replay_trips(sample_raw_telemetry, sample_static_data):
    """Verify multi-vehicle replay paths output."""
    df_log = TrajectoryReconstructor.reconstruct_event_log(
        sample_raw_telemetry,
        sample_static_data,
        line_code="541"
    )
    sentido, stops_f, shape_f = TrajectoryReconstructor.resolve_route_geometry(sample_static_data, "VOLTA")
    replays = TrajectoryReconstructor.build_replay_trips(df_log, stops_f)
    
    assert isinstance(replays, list)
    assert len(replays) == 1
    assert "case_id" in replays[0]
    assert "vehicle" in replays[0]
    assert len(replays[0]["path"]) == 3
