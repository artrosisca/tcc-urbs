"""
Event log builder adapter module.
Delegates to TrajectoryReconstructor for backward compatibility.
"""

import pandas as pd
from typing import Optional
from src.etl.load_c3sl import load_static_data
from src.etl.load_realtime import load_realtime_data
from src.etl.trajectory import TrajectoryReconstructor


def build_event_log(
    line_code: str,
    start_date: str,
    end_date: str,
    output_dir: str = "data/dados_processados",
    realtime_df: Optional[pd.DataFrame] = None,
    static_data: Optional[dict] = None
) -> pd.DataFrame:
    """
    Backward-compatible wrapper to build and save the PM4Py event log.
    """
    if realtime_df is None:
        realtime_df = load_realtime_data(line_code, start_date, end_date)
    if realtime_df.empty:
        print("Erro: Não foi possível obter dados em tempo real.")
        return pd.DataFrame()

    if static_data is None:
        static_data = load_static_data(start_date, line_code)
    if static_data.get('pontos', pd.DataFrame()).empty:
        print("Erro: Não foi possível obter pontos de parada estáticos.")
        return pd.DataFrame()

    tag = f"{start_date}_{end_date}"
    df_log = TrajectoryReconstructor.reconstruct_event_log(
        realtime_df=realtime_df,
        static_data=static_data,
        line_code=line_code,
        output_dir=output_dir,
        date_range_tag=tag
    )

    if not df_log.empty:
        print(f"Event Log consolidado gerado com sucesso ({len(df_log)} eventos).")
    else:
        print("Nenhum evento pôde ser gerado a partir dos dados fornecidos.")

    return df_log


if __name__ == "__main__":
    print("Testando geração do Event Log...")
    df_log = build_event_log("541", "2025-10-24", "2025-10-24")
    if not df_log.empty:
        print("\nExemplo do Event Log Gerado:")
        print(df_log[['case:concept:name', 'concept:name', 'time:timestamp', 'interpolated', 'stop_seq']].head(15))
