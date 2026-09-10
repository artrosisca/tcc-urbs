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
from src.etl.geofencing import match_trip_events, resolve_sentido_and_shp

def test_spline_interpolation():
    line_code = "541"
    date_str = "2025-10-24"
    
    print(f"Carregando dados para a linha {line_code} na data {date_str}...")
    static_data = load_static_data(date_str, line_code)
    df_realtime = load_realtime_data(line_code, date_str, date_str)
    
    if df_realtime.empty or static_data['pontos'].empty or static_data['shape'].empty:
        print("Erro ao carregar dados.")
        return
        
    df_clean = clean_gps_data(df_realtime, static_data['pontos'])
    if df_clean.empty:
        print("Erro: Dados limpos vazios.")
        return
        
    # Identificar uma viagem com boa quantidade de pontos
    df_clean['data_str'] = df_clean['ts'].dt.strftime('%Y-%m-%d')
    groups = list(df_clean.groupby(['COD', 'data_str']))
    
    trip_df = None
    for (vehicle_cod, day_str), group in groups:
        group = group.sort_values('ts')
        group['time_diff'] = group['ts'].diff().dt.total_seconds() / 60.0
        group['sent_change'] = (group['SENT'] != group['SENT'].shift(1)) | (group['time_diff'] > 10.0)
        group['trip_num'] = group['sent_change'].cumsum()
        
        for trip_num, trip_group in group.groupby('trip_num'):
            if len(trip_group) >= 15:
                duration = (trip_group['ts'].max() - trip_group['ts'].min()).total_seconds()
                if duration > 300:
                    trip_df = trip_group.sort_values('ts').copy()
                    break
        if trip_df is not None:
            break
            
    if trip_df is None:
        print("Erro: Nenhuma viagem longa o suficiente.")
        return
    print(f"\nViagem selecionada: Veiculo {trip_df['COD'].iloc[0]}, {len(trip_df)} pontos GPS.")
    print("Primeiro GPS:", trip_df['ts'].min(), "Ultimo GPS:", trip_df['ts'].max())
    
    # Executar a geração de eventos usando nossa nova spline Pchip
    events_df = match_trip_events(trip_df, static_data, line_code)
    if events_df.empty:
        print("Erro ao gerar eventos da viagem.")
        return
        
    # Obter dados de shape e stops para cálculo comparativo de interpolação linear manual
    sentido, shp_id = resolve_sentido_and_shp(trip_df, static_data)
    stops_df = static_data['pontos']
    stops_df = stops_df[stops_df['SENTIDO'] == sentido].sort_values('SEQ').copy()
    shape_df = static_data['shape']
    if shp_id and not shape_df.empty:
        shape_df = shape_df[shape_df['SHP'] == shp_id].copy()
        
    shape_lats = shape_df['LAT'].values
    shape_lons = shape_df['LON'].values
    
    # Calcular distâncias acumuladas do shape
    from src.etl.clean_data import haversine_vectorized
    shape_dists = np.zeros(len(shape_lats))
    if len(shape_lats) > 1:
        shape_dists[1:] = haversine_vectorized(shape_lats[:-1], shape_lons[:-1], shape_lats[1:], shape_lons[1:])
    shape_cum_dists = np.cumsum(shape_dists)
    
    # Projetar paradas e GPS no shape
    from src.etl.geofencing import map_gps_to_shape, map_gps_to_shape_hmm
    gps_lats = trip_df['LAT'].values
    gps_lons = trip_df['LON'].values
    gps_ts = trip_df['ts'].values
    gps_ts_floats = pd.to_datetime(gps_ts).astype('datetime64[ns]').view('int64') / 1e9
    
    gps_shape_idx = map_gps_to_shape_hmm(gps_lats, gps_lons, shape_lats, shape_lons)
    gps_shape_idx = np.maximum.accumulate(gps_shape_idx)
    gps_cum_dists = shape_cum_dists[gps_shape_idx]
    print("Primeiro cum_dist:", gps_cum_dists.min(), "Ultimo cum_dist:", gps_cum_dists.max())
    
    stop_lats = stops_df['LAT'].values
    stop_lons = stops_df['LON'].values
    stop_shape_idx = map_gps_to_shape(stop_lats, stop_lons, shape_lats, shape_lons)
    stop_shape_idx = np.maximum.accumulate(stop_shape_idx)
    stop_cum_dists = shape_cum_dists[stop_shape_idx]
    
    # Consolidar para interpolação linear
    df_pts = pd.DataFrame({'s': gps_cum_dists, 't': gps_ts_floats})
    df_unique = df_pts.groupby('s')['t'].mean().reset_index().sort_values('s')
    s_unique = df_unique['s'].values
    t_unique = df_unique['t'].values
    
    # Calcular linear para cada parada
    t_linear_vals = np.interp(stop_cum_dists, s_unique, t_unique)
    
    # Montar tabela comparativa
    comparison = []
    for idx, (stop_idx, row_stop) in enumerate(stops_df.iterrows()):
        s_stop = stop_cum_dists[idx]
        
        # Obter timestamp da spline calculado por match_trip_events
        row_event = events_df[events_df['stop_seq'] == row_stop['SEQ']]
        if row_event.empty:
            continue
            
        t_spline_ts = row_event['timestamp'].iloc[0]
        t_spline = t_spline_ts.timestamp()
        
        t_linear = t_linear_vals[idx]
        t_linear_ts = pd.to_datetime(t_linear, unit='s')
        if hasattr(trip_df['ts'].dt, 'tz') and trip_df['ts'].dt.tz is not None:
            t_linear_ts = t_linear_ts.tz_localize('UTC').tz_convert(trip_df['ts'].dt.tz)
            
        diff_sec = t_spline - t_linear
        
        comparison.append({
            "SEQ": row_stop['SEQ'],
            "Parada": row_stop['NOME'][:25],
            "Dist Acum (m)": f"{s_stop:.1f}",
            "Tempo Linear": t_linear_ts.strftime('%H:%M:%S'),
            "Tempo Spline": t_spline_ts.strftime('%H:%M:%S'),
            "Diferenca (s)": f"{diff_sec:+.2f}"
        })
        
    print("\n--- Comparacao de Tempos de Passagem: Linear vs. Spline Monotona (Pchip) ---")
    print(tabulate(comparison, headers="keys", tablefmt="grid"))
    
    # Validar monotonicidade estrita
    visited_seqs = [s for s in stops_df['SEQ'] if not events_df[events_df['stop_seq'] == s].empty]
    t_spline_vals = [events_df[events_df['stop_seq'] == s]['timestamp'].iloc[0] for s in visited_seqs]
    diff_t_spline = np.diff([ts.timestamp() for ts in t_spline_vals])
    is_strict = np.all(diff_t_spline > 0)
    print(f"\nMonotonicidade estrita no Log de Eventos Spline: {'Sim' if is_strict else 'Nao (ha empates ou voltas)'}")
    if not is_strict:
        print("Diferencas de tempo negativas ou nulas:", diff_t_spline[diff_t_spline <= 0])

if __name__ == "__main__":
    test_spline_interpolation()
