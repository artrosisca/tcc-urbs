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


def test_evaluate_conformance_sanitizes_mojibake_names():
    """
    Regression test for line 542 / mojibake bug:
    Raw event log with mojibake concept:name (e.g. 'PASSAGEM_Terminal SÃ\xadtio Cercado')
    must be repaired so that direction matching against clean static stops succeeds
    and doesn't erroneously pick the opposite direction producing hundreds of fake skipped stops.
    """
    base_time = datetime(2025, 12, 2, 8, 0, 0)
    # Static stops for two directions
    stops_data = [
        {"SENTIDO": "IDA", "SEQ": 1, "NOME": "Praça Rui Barbosa"},
        {"SENTIDO": "IDA", "SEQ": 2, "NOME": "Terminal Sítio Cercado"},
        {"SENTIDO": "VOLTA", "SEQ": 1, "NOME": "Terminal Sítio Cercado"},
        {"SENTIDO": "VOLTA", "SEQ": 2, "NOME": "Praça Rui Barbosa"},
    ]
    stops_df = pd.DataFrame(stops_data)

    # Event log with mojibake in VOLTA
    records = [
        {
            "case:concept:name": "CASE_1",
            "concept:name": "PASSAGEM_Terminal SÃ\xadtio Cercado",
            "time:timestamp": base_time,
            "stop_seq": 1,
            "org:resource": "V1",
            "tabela": "1",
            "gps_direction": "VOLTA",
            "interpolated": False,
        },
        {
            "case:concept:name": "CASE_1",
            "concept:name": "PASSAGEM_PraÃ§a Rui Barbosa",
            "time:timestamp": base_time + timedelta(minutes=10),
            "stop_seq": 2,
            "org:resource": "V1",
            "tabela": "1",
            "gps_direction": "VOLTA",
            "interpolated": False,
        },
    ]
    event_log_df = pd.DataFrame(records)

    conf = ProcessMiningEngine.evaluate_conformance(event_log_df, stops_df, direction="VOLTA")
    assert conf["total_cases"] == 1
    assert conf["fit_percentage"] == 100.0
    assert len(conf["skipped_stops"]) == 0
    assert conf["fit_count"] == 1


def test_aggregate_conformance_weighted_merge():
    """Verify that aggregate_conformance correctly weights fitness and merges skipped stops."""
    per_dir = {
        "IDA": {
            "total_cases": 100,
            "avg_fitness": 0.8,
            "fit_percentage": 70.0,
            "fit_count": 70,
            "total_interpolated": 15,
            "skipped_stops": [
                {"stop_seq": 1, "stop_name": "Stop A", "count": 10},
                {"stop_seq": 2, "stop_name": "Stop B", "count": 5},
            ],
            "deviations": [
                {"case_id": "C_IDA_1", "skipped_count": 3, "vehicle": "V1", "tabela": "1", "total_visited": 10, "skipped_stops": ["A"], "interpolated_count": 1}
            ]
        },
        "VOLTA": {
            "total_cases": 200,
            "avg_fitness": 0.95,
            "fit_percentage": 90.0,
            "fit_count": 180,
            "total_interpolated": 30,
            "skipped_stops": [
                {"stop_seq": 1, "stop_name": "Stop A", "count": 20},
                {"stop_seq": 3, "stop_name": "Stop C", "count": 8},
            ],
            "deviations": [
                {"case_id": "C_VOLTA_1", "skipped_count": 5, "vehicle": "V2", "tabela": "2", "total_visited": 8, "skipped_stops": ["C"], "interpolated_count": 2}
            ]
        }
    }

    agg = ProcessMiningEngine.aggregate_conformance(per_dir)

    assert agg["total_cases"] == 300
    # Weighted avg_fitness: (0.8 * 100 + 0.95 * 200) / 300 = 270 / 300 = 0.9
    assert abs(agg["avg_fitness"] - 0.9) < 1e-4
    # Weighted fit_percentage: (70 * 100 + 90 * 200) / 300 = 25000 / 300 = 83.3333%
    assert abs(agg["fit_percentage"] - 83.3333) < 1e-2
    assert agg["fit_count"] == 250
    assert agg["total_interpolated"] == 45

    # Check merged skipped stops: Stop A (10 + 20 = 30), Stop C (8), Stop B (5)
    assert len(agg["skipped_stops"]) == 3
    assert agg["skipped_stops"][0]["stop_name"] == "Stop A"
    assert agg["skipped_stops"][0]["count"] == 30
    assert agg["skipped_stops"][1]["stop_name"] == "Stop C"
    assert agg["skipped_stops"][1]["count"] == 8
    assert agg["skipped_stops"][2]["stop_name"] == "Stop B"
    assert agg["skipped_stops"][2]["count"] == 5

    # Check top deviant trips: C_VOLTA_1 (skipped_count 5) followed by C_IDA_1 (3)
    assert len(agg["deviant_trips"]) == 2
    assert agg["deviant_trips"][0]["case_id"] == "C_VOLTA_1"
    assert agg["deviant_trips"][1]["case_id"] == "C_IDA_1"


def test_evaluate_conformance_reports_total_interpolated(sample_event_log, sample_stops):
    """Verify that total_interpolated is counted across the entire selection."""
    df = sample_event_log.copy()
    # Mark two events as interpolated
    df.loc[df.index[:2], "interpolated"] = True

    conf = ProcessMiningEngine.evaluate_conformance(df, sample_stops, direction="VOLTA")
    assert "total_interpolated" in conf
    assert conf["total_interpolated"] >= 1

