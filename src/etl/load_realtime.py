"""
Realtime telemetry loading adapter module.
Delegates to TelemetryRepository for backward compatibility.
"""

import os
import pandas as pd
from src.etl.repository import default_telemetry_repo, FilesystemTelemetryAdapter


def load_realtime_data(line_code, start_date, end_date, data_dir="data/dados_em_tempo_real_2026"):
    """
    Backward-compatible wrapper to load realtime GPS data.
    """
    if data_dir == "data/dados_em_tempo_real_2026":
        return default_telemetry_repo.get_realtime_telemetry(line_code, start_date, end_date)
    # If custom data_dir provided
    adapter = FilesystemTelemetryAdapter(base_data_dir=os.path.dirname(data_dir) or "data")
    adapter.realtime_dir = data_dir
    return adapter.get_realtime_telemetry(line_code, start_date, end_date)


if __name__ == "__main__":
    df_res = load_realtime_data("541", "2025-10-24", "2025-10-24")
    if not df_res.empty:
        print("Registros carregados:", len(df_res))
