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
    # Canonical key: PASSAGEM_{SEQ:02d}_{NOME} (F1.1)
    assert df_log["concept:name"].str.match(r"^PASSAGEM_\d{2}_").all()


def test_segmentation_fallback_progress_reversal(sample_static_data):
    """
    TDD Spec (F1.2):
    Without a reliable SENT column, trips must be segmented by reversal of
    curvilinear progress along the shape instead of failing with KeyError.
    """
    base_time = datetime(2025, 10, 24, 8, 0, 0)
    shape_pts = sample_static_data["shape"]
    # One stop at each shape point so no ping is dropped by the 500m outlier filter
    stops_df = pd.DataFrame([
        {"SEQ": i + 1, "NUM": f"20{i}", "NOME": f"Parada {i + 1}", "SENTIDO": "VOLTA",
         "LAT": shape_pts.iloc[i]["LAT"], "LON": shape_pts.iloc[i]["LON"]}
        for i in range(len(shape_pts))
    ])
    static_data = {"pontos": stops_df, "shape": shape_pts, "tabela": pd.DataFrame()}

    # Outbound: shape idx 0 -> 1 -> 2 ; Return: idx 1 -> 0 -> 0(+offset) (no SENT column)
    coords = [(0, 0), (1, 5), (2, 10), (1, 15), (0, 20)]
    records = [
        {
            "COD": "VEH09", "CODIGOLINHA": "541",
            "LAT": shape_pts.iloc[i]["LAT"], "LON": shape_pts.iloc[i]["LON"],
            "ts": base_time + timedelta(minutes=m), "TABELA": "1"
        }
        for i, m in coords
    ]
    # Final ping near stop 1 but far enough to survive the 5m jitter filter
    records.append({
        "COD": "VEH09", "CODIGOLINHA": "541",
        "LAT": shape_pts.iloc[0]["LAT"] + 0.0001, "LON": shape_pts.iloc[0]["LON"] + 0.0001,
        "ts": base_time + timedelta(minutes=25), "TABELA": "1"
    })
    df_raw = pd.DataFrame(records)
    df_log = TrajectoryReconstructor.reconstruct_event_log(df_raw, static_data, line_code="541")

    assert not df_log.empty
    # The reversal at ping 4 (idx 2 -> 1) must have split the day into 2 trips
    assert df_log["case:concept:name"].nunique() == 2


def test_activity_naming_canonical_and_strippable():
    """Verify canonical activity keys are built by stop identity and parseable."""
    from src.etl.repository import activity_name_for_stop, strip_activity_name
    name = activity_name_for_stop(3, "Rua São José dos Pinhais, 358 - Sítio Cercado")
    assert name == "PASSAGEM_03_Rua São José dos Pinhais, 358 - Sítio Cercado"
    assert strip_activity_name(name) == "Rua São José dos Pinhais, 358 - Sítio Cercado"
    # Legacy name-only fallback stays parseable
    assert strip_activity_name("PASSAGEM_Praça do Japão") == "Praça do Japão"
    assert activity_name_for_stop(None, "Praça do Japão") == "PASSAGEM_Praça do Japão"


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


def test_match_trip_omits_skipped_stops_exceeding_threshold(sample_static_data):
    """
    TDD Spec (Banca Rodada 2):
    Verify that stops where the bus never came within the acceptance threshold
    (150m) are omitted from the event log instead of being artificially interpolated by PCHIP.
    """
    base_time = datetime(2025, 10, 24, 8, 0, 0)
    # Trip visits Stop 1 and Stop 3, but completely bypasses Stop 2 (Praça do Japão)
    records = [
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5350, "LON": -49.2710, "ts": base_time, "SENT": "VOLTA", "TABELA": "1"},
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.5000, "LON": -49.2715, "ts": base_time + timedelta(minutes=5), "SENT": "VOLTA", "TABELA": "1"},
        {"COD": "VEH01", "CODIGOLINHA": "541", "LAT": -25.4350, "LON": -49.2730, "ts": base_time + timedelta(minutes=10), "SENT": "VOLTA", "TABELA": "1"},
    ]
    trip_df = pd.DataFrame(records)
    events_df = TrajectoryReconstructor.match_trip(trip_df, sample_static_data, line_code="541")
    
    stop_names = events_df["stop_name"].tolist()
    assert "Terminal Sítio Cercado" in stop_names
    assert "Praça Rui Barbosa" in stop_names
    # Praça do Japão is ~8km away from the trajectory (min_dist >> 150m). It MUST be omitted from the log!
    assert "Praça do Japão" not in stop_names


def test_stop_shape_idx_does_not_collapse_in_circular_route():
    """
    TDD Spec (Banca Rodada 2 & Ata item 4):
    Verify that in a circular or return route where Stop 3 revisits the initial terminal (index 0),
    stop_shape_idx does not collapse to the maximum index of earlier stops due to maximum.accumulate.
    """
    stops_df = pd.DataFrame([
        {"SEQ": 1, "NUM": "101", "NOME": "Terminal A", "SENTIDO": "CIRCULAR", "LAT": -25.430, "LON": -49.270},
        {"SEQ": 2, "NUM": "102", "NOME": "Ponto Intermediario B", "SENTIDO": "CIRCULAR", "LAT": -25.450, "LON": -49.270},
        {"SEQ": 3, "NUM": "103", "NOME": "Terminal A Retorno", "SENTIDO": "CIRCULAR", "LAT": -25.430, "LON": -49.270},
    ])
    shape_df = pd.DataFrame([
        {"SHP": "SHP_CIRC", "LAT": -25.430, "LON": -49.270},  # idx 0
        {"SHP": "SHP_CIRC", "LAT": -25.440, "LON": -49.270},  # idx 1
        {"SHP": "SHP_CIRC", "LAT": -25.450, "LON": -49.270},  # idx 2
    ])
    static_data = {"pontos": stops_df, "shape": shape_df, "tabela": pd.DataFrame()}

    sentido, stops_f, _ = TrajectoryReconstructor.resolve_route_geometry(static_data, direction="CIRCULAR")

    indices = stops_f["shape_idx"].tolist()
    # Terminal A Retorno is at Pt 0 (LAT: -25.430), so its true nearest shape_idx is 0.
    # np.maximum.accumulate wrongly forced indices to [0, 2, 2].
    assert indices == [0, 2, 0], f"Expected [0, 2, 0], but got {indices} (collapsed by maximum.accumulate)"
