"""
Conformance analysis adapter module.
Delegates to ProcessMiningEngine for backward compatibility.
"""

import pandas as pd
from src.mining.engine import ProcessMiningEngine


def create_normative_petri_net(stops_df: pd.DataFrame):
    """Backward-compatible wrapper for normative Petri Net creation."""
    return ProcessMiningEngine.create_normative_petri_net(stops_df)


def analyze_conformance(event_log_df: pd.DataFrame, static_stops_df: pd.DataFrame):
    """Backward-compatible wrapper for conformance analysis."""
    return ProcessMiningEngine.evaluate_conformance(event_log_df, static_stops_df)


if __name__ == "__main__":
    import os
    from src.etl.load_c3sl import load_static_data

    csv_path = "data/dados_processados/event_log_541_2025-10-24_2025-10-24.csv"
    if os.path.exists(csv_path):
        print(f"Lendo log de testes de: {csv_path}")
        df = pd.read_csv(csv_path)
        static = load_static_data("2025-10-24", "541")
        res = analyze_conformance(df, static['pontos'])
        for direction, data in res.items():
            print(f"\n=== RESULTADOS CONFORMIDADE SENTIDO: {direction} ===")
            print(f"Total de viagens: {data['total_cases']}")
            print(f"Fitness Médio: {data['avg_fitness']:.3f}")
            print(f"Percentual 100% em conformidade: {data['fit_percentage']:.1f}%")
    else:
        print("Execute o ETL primeiro para rodar este teste.")
