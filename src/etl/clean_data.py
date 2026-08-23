"""
Data cleaning adapter module.
Delegates to TrajectoryReconstructor for backward compatibility.
"""

import pandas as pd
from typing import Optional
from src.etl.trajectory import TrajectoryReconstructor, haversine_vectorized


def clean_gps_data(
    df_realtime: pd.DataFrame,
    static_stops_df: Optional[pd.DataFrame] = None,
    distance_threshold: float = 5.0,
    outlier_threshold: float = 500.0
) -> pd.DataFrame:
    """Backward-compatible wrapper for telemetry data cleaning."""
    return TrajectoryReconstructor.clean_telemetry(
        df_realtime,
        static_stops_df=static_stops_df,
        distance_threshold=distance_threshold,
        outlier_threshold=outlier_threshold
    )


if __name__ == "__main__":
    from src.etl.load_c3sl import load_static_data
    from src.etl.load_realtime import load_realtime_data

    static = load_static_data("2025-10-24", "541")
    realtime = load_realtime_data("541", "2025-10-24", "2025-10-24")

    cleaned = clean_gps_data(realtime, static['pontos'])
    if not cleaned.empty:
        print("Exemplo de dados limpos:")
        print(cleaned[['COD', 'request_timestamp', 'LAT', 'LON', 'SENT', 'SITUACAO']].head(5))
