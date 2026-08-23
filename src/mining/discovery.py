"""
Process discovery adapter module.
Delegates to ProcessMiningEngine for backward compatibility.
"""

import os
import pm4py
import pandas as pd
from src.mining.engine import ProcessMiningEngine


def run_process_discovery(event_log, output_dir="data/dados_processados"):
    """
    Backward-compatible wrapper for running process discovery and saving visualizations.
    """
    os.makedirs(output_dir, exist_ok=True)
    if isinstance(event_log, pd.DataFrame):
        log = ProcessMiningEngine.format_event_log(event_log)
    else:
        log = event_log

    results = {}

    # 1. DFG
    print("Executando descoberta DFG...")
    dfg, start_activities, end_activities = pm4py.discover_dfg(log)
    results['dfg'] = (dfg, start_activities, end_activities)
    dfg_path = os.path.join(output_dir, "discovered_dfg.png")
    try:
        pm4py.save_vis_dfg(dfg, start_activities, end_activities, dfg_path)
        print(f"  DFG visual salvo em: {dfg_path}")
    except Exception as e:
        print(f"  Erro ao salvar visualização do DFG: {e}")

    # 2. Inductive Miner
    print("Executando descoberta Inductive Miner (Rede de Petri)...")
    net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log)
    results['petri_net'] = (net, initial_marking, final_marking)
    petri_path = os.path.join(output_dir, "discovered_petri_net.png")
    try:
        pm4py.save_vis_petri_net(net, initial_marking, final_marking, petri_path)
        print(f"  Rede de Petri salva em: {petri_path}")
    except Exception as e:
        print(f"  Erro ao salvar visualização da Rede de Petri: {e}")

    pnml_path = os.path.join(output_dir, "discovered_petri_net.pnml")
    try:
        pm4py.write_pnml(net, initial_marking, final_marking, pnml_path)
        print(f"  Rede de Petri serializada salva em: {pnml_path}")
    except Exception as e:
        print(f"  Erro ao exportar PNML: {e}")

    # 3. Heuristic Miner
    print("Executando descoberta Heuristic Miner...")
    try:
        heuristic_net = pm4py.discover_heuristics_net(log)
        results['heuristic_net'] = heuristic_net
        heuristics_path = os.path.join(output_dir, "discovered_heuristic_net.png")
        pm4py.save_vis_heuristics_net(heuristic_net, heuristics_path)
        print(f"  Modelo heurístico salvo em: {heuristics_path}")
    except Exception as e:
        print(f"  Erro no Heuristic Miner: {e}")

    return results


if __name__ == "__main__":
    csv_path = "data/dados_processados/event_log_541_2025-10-24_2025-10-24.csv"
    if os.path.exists(csv_path):
        print(f"Lendo log de testes de: {csv_path}")
        df = pd.read_csv(csv_path)
        df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
        for direction, group in df.groupby('gps_direction'):
            print(f"\n=== DESCOBERTA SENTIDO: {direction} ({len(group)} eventos) ===")
            run_process_discovery(group, output_dir=f"data/dados_processados/descoberta_{direction}")
    else:
        print("Arquivo de teste do Event Log não encontrado. Execute o ETL primeiro.")
