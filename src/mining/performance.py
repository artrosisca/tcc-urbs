"""
Performance analysis adapter module.
Delegates to ProcessMiningEngine for backward compatibility.
"""

import pandas as pd
from typing import Optional
from src.mining.engine import ProcessMiningEngine


def analyze_segment_performance(event_log_df: pd.DataFrame) -> pd.DataFrame:
    """Backward-compatible wrapper for segment performance analysis."""
    return ProcessMiningEngine.analyze_segment_performance(event_log_df)


def analyze_schedule_delays(
    event_log_df: pd.DataFrame,
    planned_table_df: pd.DataFrame,
    date_str: str,
    static_stops_df: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """Backward-compatible wrapper for schedule delays analysis."""
    return ProcessMiningEngine.analyze_schedule_delays(event_log_df, planned_table_df, date_str, static_stops_df)


if __name__ == "__main__":
    import os
    from src.etl.load_c3sl import load_static_data

    csv_path = "data/dados_processados/event_log_541_2025-10-24_2025-10-24.csv"
    if os.path.exists(csv_path):
        print(f"Lendo log de testes de: {csv_path}")
        df = pd.read_csv(csv_path)
        print("\n=== MAIORES GARGALOS DETECTADOS ===")
        df_seg = analyze_segment_performance(df)
        print(df_seg[['segment_name', 'total_passages', 'mean_time_min', 'max_time_min']].head(5))

        static = load_static_data("2025-10-24", "541")
        df_delays = analyze_schedule_delays(df, static['tabela'], "2025-10-24")
        if not df_delays.empty:
            print("\n=== ANÁLISE DE PONTUALIDADE ===")
            print(df_delays[['case_id', 'planned_departure', 'actual_departure', 'delay_minutes', 'status']].head(5))
    else:
        print("Execute o ETL primeiro para rodar este teste.")
