import os
import sys
import numpy as np
import pandas as pd
from tabulate import tabulate

# Adicionar root do projeto ao sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.etl.load_c3sl import load_static_data
from src.etl.load_realtime import load_realtime_data
from src.etl.clean_data import clean_gps_data
from src.etl.geofencing import map_gps_to_shape, map_gps_to_shape_hmm, resolve_sentido_and_shp

def test_hmm_matching():
    line_code = "541"
    date_str = "2025-10-24"
    
    print(f"Carregando dados para a linha {line_code} na data {date_str}...")
    static_data = load_static_data(date_str, line_code)
    df_realtime = load_realtime_data(line_code, date_str, date_str)
    
    if df_realtime.empty:
        print("Erro: Sem dados em tempo real.")
        return
    if static_data['pontos'].empty or static_data['shape'].empty:
        print("Erro: Sem dados estáticos.")
        return
        
    df_clean = clean_gps_data(df_realtime, static_data['pontos'])
    if df_clean.empty:
        print("Erro: Sem dados após limpeza.")
        return
        
    # Agrupar e pegar a primeira viagem válida
    df_clean['data_str'] = df_clean['ts'].dt.strftime('%Y-%m-%d')
    groups = list(df_clean.groupby(['COD', 'data_str']))
    
    trip_df = None
    for (vehicle_cod, day_str), group in groups:
        group = group.sort_values('ts')
        group['time_diff'] = group['ts'].diff().dt.total_seconds() / 60.0
        group['sent_change'] = (group['SENT'] != group['SENT'].shift(1)) | (group['time_diff'] > 10.0)
        group['trip_num'] = group['sent_change'].cumsum()
        
        for trip_num, trip_group in group.groupby('trip_num'):
            if len(trip_group) >= 15: # Pegar uma viagem longa o suficiente
                trip_df = trip_group.sort_values('ts').copy()
                break
        if trip_df is not None:
            break
            
    if trip_df is None:
        print("Erro: Não foi encontrada nenhuma viagem com mais de 15 pontos.")
        return
        
    print(f"\nViagem selecionada: Veículo {trip_df['COD'].iloc[0]}, data {date_str}, com {len(trip_df)} pontos GPS.")
    
    # Obter shape
    sentido, shp_id = resolve_sentido_and_shp(trip_df, static_data)
    print(f"Sentido resolvido: {sentido}, Shape ID: {shp_id}")
    
    shape_df = static_data['shape']
    if shp_id and not shape_df.empty:
        shape_df = shape_df[shape_df['SHP'] == shp_id].copy()
    if shape_df.empty:
        print("Erro: Shape correspondente está vazio.")
        return
        
    shape_lats = shape_df['LAT'].values
    shape_lons = shape_df['LON'].values
    gps_lats = trip_df['LAT'].values
    gps_lons = trip_df['LON'].values
    
    # 1. Rodar Euclidiano Simples
    idx_euclidean = map_gps_to_shape(gps_lats, gps_lons, shape_lats, shape_lons)
    
    # 2. Rodar HMM com parâmetros sugeridos no plano
    idx_hmm_base = map_gps_to_shape_hmm(gps_lats, gps_lons, shape_lats, shape_lons,
                                        search_radius=100.0, sigma_z=15.0, beta=30.0)
                                        
    # 3. Variar parâmetros para comparação
    variations = [
        {"search_radius": 50.0, "sigma_z": 10.0, "beta": 10.0},
        {"search_radius": 150.0, "sigma_z": 30.0, "beta": 50.0},
        {"search_radius": 100.0, "sigma_z": 5.0, "beta": 50.0},
        {"search_radius": 100.0, "sigma_z": 25.0, "beta": 10.0},
    ]
    
    results = []
    
    # Função para medir pulos para trás e descontinuidades
    def analyze_path(indices, name):
        diffs = np.diff(indices)
        backward_steps = np.sum(diffs < 0)
        total_back_distance = np.sum(diffs[diffs < 0])
        max_jump = np.max(np.abs(diffs)) if len(diffs) > 0 else 0
        is_monotonic = np.all(diffs >= 0)
        return {
            "Método / Configuração": name,
            "Monótono?": "Sim" if is_monotonic else "Não",
            "Passos p/ Trás": backward_steps,
            "Soma saltos p/ trás": total_back_distance,
            "Maior Salto Absoluto (índices)": max_jump
        }
        
    results.append(analyze_path(idx_euclidean, "Euclidiano (Original)"))
    results.append(analyze_path(idx_hmm_base, "HMM Base (R=100, sigma=15, beta=30)"))
    
    for i, var in enumerate(variations):
        idx_hmm = map_gps_to_shape_hmm(
            gps_lats, gps_lons, shape_lats, shape_lons,
            search_radius=var["search_radius"],
            sigma_z=var["sigma_z"],
            beta=var["beta"]
        )
        name = f"HMM Var {i+1} (R={var['search_radius']}, sigma={var['sigma_z']}, beta={var['beta']})"
        results.append(analyze_path(idx_hmm, name))
        
    print("\n--- Resultados Comparativos de Map Matching ---")
    print(tabulate(results, headers="keys", tablefmt="grid"))
    
    print("\nComparação de amostra dos primeiros 15 pontos da viagem:")
    sample_data = []
    for i in range(min(15, len(trip_df))):
        sample_data.append({
            "Ponto": i,
            "Timestamp": trip_df['ts'].iloc[i].strftime('%H:%M:%S'),
            "GPS Lat": f"{gps_lats[i]:.6f}",
            "GPS Lon": f"{gps_lons[i]:.6f}",
            "Índice Euclidiano": idx_euclidean[i],
            "Índice HMM Base": idx_hmm_base[i]
        })
    print(tabulate(sample_data, headers="keys", tablefmt="simple"))

if __name__ == "__main__":
    test_hmm_matching()
