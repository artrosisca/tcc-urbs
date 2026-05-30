import os
import pandas as pd
import numpy as np
from src.etl.build_event_log import build_event_log
from src.etl.load_c3sl import load_static_data
from src.mining.conformance import analyze_conformance
from src.mining.performance import analyze_segment_performance, analyze_schedule_delays

def evaluate_regime(name, start_date, end_date):
    print(f"\n========================================================")
    print(f"PROCESSANDO REGIME: {name} ({start_date} a {end_date})")
    print(f"========================================================")
    
    # 1. Rodar ETL + Map Matching + Geofencing + Interpolação
    df_log = build_event_log("541", start_date, end_date)
    if df_log.empty:
        print(f"Erro ao gerar log de eventos para o {name}.")
        return None
        
    static = load_static_data(start_date, "541")
    
    # 2. Conformidade
    conf = analyze_conformance(df_log, static['pontos'])
    
    # Pegar sentido VOLTA como referência para simplificar a comparação
    tbr_fitness = 0.0
    fit_pct = 0.0
    avg_skipped = 0.0
    avg_interpolated = 0.0
    total_trips = 0
    
    if 'VOLTA' in conf:
        tbr_fitness = conf['VOLTA']['avg_fitness']
        fit_pct = conf['VOLTA']['fit_percentage']
        total_trips = conf['VOLTA']['total_cases']
        avg_skipped = conf['VOLTA']['deviations']['skipped_count'].mean()
        avg_interpolated = conf['VOLTA']['deviations']['interpolated_count'].mean()
        
    # 3. Performance e Atrasos
    df_delays = analyze_schedule_delays(df_log, static['tabela'], start_date)
    pct_ontime = 0.0
    pct_late = 0.0
    
    if not df_delays.empty:
        counts = df_delays['status'].value_counts(normalize=True) * 100
        pct_ontime = counts.get('NO HORÁRIO', 0.0)
        pct_late = counts.get('ATRASADO', 0.0)
        
    # 4. Gargalos
    df_seg = analyze_segment_performance(df_log[df_log['gps_direction'] == 'VOLTA'])
    longest_segment = "N/A"
    longest_time = 0.0
    if not df_seg.empty:
        longest_segment = df_seg['segment_name'].iloc[0]
        longest_time = df_seg['mean_time_min'].iloc[0]
        
    return {
        'Regime': name,
        'Período': f"{start_date} a {end_date}",
        'Total Viagens (VOLTA)': total_trips,
        'Total Eventos': len(df_log),
        'Fitness Médio (TBR)': round(tbr_fitness, 3),
        'Viagens 100% Conformantes': f"{fit_pct:.1f}%",
        'Média Paradas Puladas': round(avg_skipped, 2),
        'Média Paradas Interpoladas (Gaps)': round(avg_interpolated, 2),
        'Partidas no Horário': f"{pct_ontime:.1f}%",
        'Partidas Atrasadas (>5 min)': f"{pct_late:.1f}%",
        'Ponto Crítico de Lentidão': longest_segment,
        'Tempo no Ponto Crítico': f"{longest_time:.1f} min"
    }

def main():
    # Avaliar Regime A
    res_a = evaluate_regime("Regime A (2 min)", "2025-10-24", "2025-10-30")
    
    # Avaliar Regime B
    res_b = evaluate_regime("Regime B (20s)", "2025-12-02", "2025-12-08")
    
    if res_a and res_b:
        df_comp = pd.DataFrame([res_a, res_b])
        
        print("\n\n" + "=" * 80)
        print("TABELA COMPARATIVA DE RESULTADOS DO TCC")
        print("=" * 80)
        print(df_comp.to_string(index=False))
        
        # Salvar em Markdown para o walkthrough
        output_path = "dados_processados/comparativo_tcc.md"
        df_comp.to_markdown(output_path, index=False)
        print(f"\nResultados salvos em markdown em: {output_path}")

if __name__ == "__main__":
    main()
