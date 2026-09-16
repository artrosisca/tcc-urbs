import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from src.mining.engine import ProcessMiningEngine


@pytest.fixture
def sample_event_log():
    """Generates a small in-memory event log for testing."""
    records = []
    base_time = datetime(2025, 10, 24, 8, 0, 0)
    
    # Case 1: Perfect compliance (Stop A -> Stop B -> Stop C)
    for seq, stop in enumerate(["Terminal Sítio Cercado", "Praça do Japão", "Praça Rui Barbosa"], start=1):
        records.append({
            "case:concept:name": "VEH01_541_1_2025-10-24_V1",
            "concept:name": f"PASSAGEM_{stop}",
            "time:timestamp": base_time + timedelta(minutes=seq * 5),
            "stop_seq": seq,
            "org:resource": "VEH01",
            "tabela": "1",
            "gps_direction": "VOLTA",
            "interpolated": False
        })
        
    # Case 2: Skipped middle stop (Stop A -> Stop C)
    for seq, stop in [(1, "Terminal Sítio Cercado"), (3, "Praça Rui Barbosa")]:
        records.append({
            "case:concept:name": "VEH02_541_1_2025-10-24_V1",
            "concept:name": f"PASSAGEM_{stop}",
            "time:timestamp": base_time + timedelta(minutes=seq * 6),
            "stop_seq": seq,
            "org:resource": "VEH02",
            "tabela": "1",
            "gps_direction": "VOLTA",
            "interpolated": False
        })
        
    # Case 3: Ida direction
    for seq, stop in enumerate(["Praça Rui Barbosa", "Praça do Japão", "Terminal Sítio Cercado"], start=1):
        records.append({
            "case:concept:name": "VEH01_541_1_2025-10-24_V2",
            "concept:name": f"PASSAGEM_{stop}",
            "time:timestamp": base_time + timedelta(hours=1, minutes=seq * 5),
            "stop_seq": seq,
            "org:resource": "VEH01",
            "tabela": "1",
            "gps_direction": "IDA",
            "interpolated": False
        })

    return pd.DataFrame(records)


@pytest.fixture
def sample_stops():
    """Generates static stops fixture."""
    return pd.DataFrame([
        {"SEQ": 1, "NUM": "101", "NOME": "Terminal Sítio Cercado", "SENTIDO": "VOLTA", "LAT": -25.535, "LON": -49.271},
        {"SEQ": 2, "NUM": "102", "NOME": "Praça do Japão", "SENTIDO": "VOLTA", "LAT": -25.442, "LON": -49.288},
        {"SEQ": 3, "NUM": "103", "NOME": "Praça Rui Barbosa", "SENTIDO": "VOLTA", "LAT": -25.435, "LON": -49.273},
        {"SEQ": 1, "NUM": "201", "NOME": "Praça Rui Barbosa", "SENTIDO": "IDA", "LAT": -25.435, "LON": -49.273},
        {"SEQ": 2, "NUM": "202", "NOME": "Praça do Japão", "SENTIDO": "IDA", "LAT": -25.442, "LON": -49.288},
        {"SEQ": 3, "NUM": "203", "NOME": "Terminal Sítio Cercado", "SENTIDO": "IDA", "LAT": -25.535, "LON": -49.271},
    ])


@pytest.fixture
def sample_planned_table():
    """Generates static timetable fixture."""
    return pd.DataFrame([
        {"DIA": "1", "TABELA": "1", "PONTO": "Terminal Sítio Cercado", "HORA": "08:00"},
        {"DIA": "1", "TABELA": "1", "PONTO": "Terminal Sítio Cercado", "HORA": "08:30"},
        {"DIA": "1", "TABELA": "1", "PONTO": "Praça Rui Barbosa", "HORA": "09:00"},
    ])


def test_discover_petri_net_json(sample_event_log):
    """Verify discovery JSON output schema."""
    df_volta = sample_event_log[sample_event_log['gps_direction'] == "VOLTA"]
    result = ProcessMiningEngine.discover_petri_net(df_volta, as_svg=False)
    
    assert isinstance(result, dict)
    assert "places" in result
    assert "transitions" in result
    assert "arcs" in result
    assert "initial_marking" in result
    assert "final_marking" in result
    assert len(result["places"]) > 0
    assert len(result["transitions"]) > 0


def test_discover_petri_net_svg(sample_event_log):
    """Verify discovery SVG generation returns valid XML/SVG."""
    df_volta = sample_event_log[sample_event_log['gps_direction'] == "VOLTA"]
    result = ProcessMiningEngine.discover_petri_net(df_volta, as_svg=True)
    
    assert isinstance(result, str)
    assert "<svg" in result and "</svg>" in result


def test_evaluate_conformance(sample_event_log, sample_stops):
    """Verify conformance replay and deviation detection."""
    df_volta = sample_event_log[sample_event_log['gps_direction'] == "VOLTA"]
    result = ProcessMiningEngine.evaluate_conformance(df_volta, sample_stops, direction="VOLTA")
    
    assert isinstance(result, dict)
    assert "avg_fitness" in result
    assert "fit_percentage" in result
    assert "total_cases" in result
    assert "skipped_stops" in result
    assert "deviant_trips" in result
    
    assert result["total_cases"] == 2
    assert 0.0 < result["avg_fitness"] <= 1.0
    # Case 2 skipped Praça do Japão
    assert any(s["stop_name"] == "Praça do Japão" for s in result["skipped_stops"])


def test_analyze_performance_json(sample_event_log):
    """Verify DFG performance JSON output structure."""
    df_volta = sample_event_log[sample_event_log['gps_direction'] == "VOLTA"]
    result = ProcessMiningEngine.analyze_performance(df_volta, as_svg=False)
    
    assert isinstance(result, dict)
    assert "nodes" in result
    assert "links" in result
    assert "start_activities" in result
    assert "end_activities" in result
    assert len(result["nodes"]) > 0
    assert len(result["links"]) > 0


def test_analyze_performance_svg(sample_event_log):
    """Verify DFG performance SVG output."""
    df_volta = sample_event_log[sample_event_log['gps_direction'] == "VOLTA"]
    result = ProcessMiningEngine.analyze_performance(df_volta, as_svg=True)
    
    assert isinstance(result, str)
    assert "<svg" in result and "</svg>" in result


def test_analyze_segment_performance(sample_event_log):
    """Verify segment bottleneck analysis computation."""
    df_volta = sample_event_log[sample_event_log['gps_direction'] == "VOLTA"]
    result_df = ProcessMiningEngine.analyze_segment_performance(df_volta)
    
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty
    assert "segment_name" in result_df.columns
    assert "mean_time_min" in result_df.columns
    assert "total_passages" in result_df.columns


def test_analyze_schedule_delays(sample_event_log, sample_planned_table, sample_stops):
    """Verify schedule delay computation."""
    result_df = ProcessMiningEngine.analyze_schedule_delays(
        sample_event_log,
        sample_planned_table,
        "2025-10-24",
        sample_stops
    )
    
    assert isinstance(result_df, pd.DataFrame)
    assert not result_df.empty
    assert "case_id" in result_df.columns
    assert "delay_minutes" in result_df.columns
    assert "status" in result_df.columns


def test_analyze_segment_performance_excludes_interpolated():
    """
    TDD Spec (F1.3):
    Segments whose endpoints were fabricated by interpolation must be excluded
    from timing statistics, while the interpolation ratio is reported per segment.
    """
    base_time = datetime(2025, 10, 24, 8, 0, 0)
    records = []
    cases = [
        ("C1", [(1, "P1", False, 0), (2, "P2", False, 10)]),
        ("C2", [(1, "P1", False, 0), (2, "P2", True, 60)]),
        ("C3", [(1, "P1", False, 0), (2, "P2", False, 8)]),
    ]
    for cid, stops in cases:
        for seq, name, interp, mins in stops:
            records.append({
                "case:concept:name": cid,
                "concept:name": f"PASSAGEM_{name}",
                "time:timestamp": base_time + timedelta(minutes=mins),
                "stop_seq": seq,
                "org:resource": cid,
                "interpolated": interp,
            })
    df = pd.DataFrame(records)
    result = ProcessMiningEngine.analyze_segment_performance(df)

    seg = result[result["segment_name"] == "P1 -> P2"]
    assert not seg.empty
    # Only the 2 fully observed passages contribute to timing (10 and 8 min)
    assert seg["total_passages"].iloc[0] == 3
    assert seg["observed_passages"].iloc[0] == 2
    assert abs(seg["mean_time_min"].iloc[0] - 9.0) < 0.01
    assert abs(seg["interp_ratio"].iloc[0] - (1 / 3)) < 0.01


def test_analyze_schedule_delays_skips_interpolated_departures(sample_event_log, sample_planned_table, sample_stops):
    """
    TDD Spec (F1.3):
    Departures whose stop-1 event was interpolated (fabricated timestamp) must be
    excluded from delay computation instead of producing a bogus schedule delay.
    """
    df = sample_event_log.copy()
    df["interpolated"] = False
    df.loc[df['stop_seq'] == 1, 'interpolated'] = True

    result = ProcessMiningEngine.analyze_schedule_delays(df, sample_planned_table, "2025-10-24", sample_stops)
    assert result.empty


def test_empty_dataframe_handling():
    """Verify that all methods handle empty inputs gracefully."""
    empty_df = pd.DataFrame()
    stops_empty = pd.DataFrame()
    
    petri_json = ProcessMiningEngine.discover_petri_net(empty_df, as_svg=False)
    assert petri_json["places"] == []
    
    petri_svg = ProcessMiningEngine.discover_petri_net(empty_df, as_svg=True)
    assert "<svg" in petri_svg
    
    conf = ProcessMiningEngine.evaluate_conformance(empty_df, stops_empty, direction="VOLTA")
    assert conf["total_cases"] == 0
    
    perf_json = ProcessMiningEngine.analyze_performance(empty_df, as_svg=False)
    assert perf_json["nodes"] == []
    
    seg = ProcessMiningEngine.analyze_segment_performance(empty_df)
    assert seg.empty
