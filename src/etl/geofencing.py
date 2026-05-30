import numpy as np
import pandas as pd
from src.etl.clean_data import haversine_vectorized

def map_gps_to_shape(gps_lats, gps_lons, shape_lats, shape_lons):
    """
    Projeta coordenadas GPS nos índices sequenciais da rota física (shape).
    Retorna o índice no shape para cada ponto GPS.
    """
    shape_indices = []
    for lat, lon in zip(gps_lats, gps_lons):
        # Calcular distância deste ponto a todos os pontos do shape
        dists = haversine_vectorized(
            np.full_like(shape_lats, lat),
            np.full_like(shape_lons, lon),
            shape_lats,
            shape_lons
        )
        shape_indices.append(dists.argmin())
    return np.array(shape_indices)

def resolve_sentido_and_shp(trip_df, static_data):
    """
    Resolve dinamicamente o sentido estático e o ID do shape correspondente para a viagem atual.
    Retorna (sentido_static, shp_id).
    """
    pontos_df = static_data['pontos']
    if pontos_df.empty:
        return None, None
        
    sentidos = pontos_df['SENTIDO'].unique()
    if len(sentidos) == 0:
        return None, None
    elif len(sentidos) == 1:
        sentido_static = sentidos[0]
    else:
        # Comparar a primeira coordenada da viagem GPS com a primeira parada de cada sentido
        trip_start_lat = trip_df['LAT'].iloc[0]
        trip_start_lon = trip_df['LON'].iloc[0]
        
        best_sentido = None
        min_dist = float('inf')
        
        for sent in sentidos:
            stops = pontos_df[pontos_df['SENTIDO'] == sent].sort_values('SEQ')
            if stops.empty:
                continue
            start_stop_lat = stops['LAT'].iloc[0]
            start_stop_lon = stops['LON'].iloc[0]
            
            # Calcular distância Haversine
            dist = haversine_vectorized(
                np.array([trip_start_lat]), np.array([trip_start_lon]),
                np.array([start_stop_lat]), np.array([start_stop_lon])
            )[0]
            
            if dist < min_dist:
                min_dist = dist
                best_sentido = sent
                
        sentido_static = best_sentido

    # Encontrar o ID do shape mais próximo para o sentido estático selecionado
    shape_df = static_data['shape']
    shp_id = None
    if not shape_df.empty and 'SHP' in shape_df.columns:
        shps = shape_df['SHP'].unique()
        if len(shps) == 1:
            shp_id = shps[0]
        elif len(shps) > 1:
            # Obter todas as paradas do sentido estático selecionado
            stops = pontos_df[pontos_df['SENTIDO'] == sentido_static]
            stop_lats = stops['LAT'].values
            stop_lons = stops['LON'].values
            
            best_shp = None
            min_avg_dist = float('inf')
            
            for shp in shps:
                shp_pts = shape_df[shape_df['SHP'] == shp]
                if shp_pts.empty:
                    continue
                shp_lats = shp_pts['LAT'].values
                shp_lons = shp_pts['LON'].values
                
                # Calcular distância média de cada parada ao ponto mais próximo do shape
                dists_list = []
                for s_lat, s_lon in zip(stop_lats, stop_lons):
                    dists = haversine_vectorized(
                        np.full_like(shp_lats, s_lat), np.full_like(shp_lons, s_lon),
                        shp_lats, shp_lons
                    )
                    dists_list.append(dists.min())
                avg_dist = np.mean(dists_list)
                
                if avg_dist < min_avg_dist:
                    min_avg_dist = avg_dist
                    best_shp = shp
            shp_id = best_shp
            
    return sentido_static, shp_id

def match_trip_events(trip_df, static_data, line_code, geofence_radius=100.0, enforce_monotonicity=True):
    """
    Aplica geofencing e interpolação para uma viagem individual.
    
    Args:
        trip_df (pd.DataFrame): Dados de GPS de uma única viagem
        static_data (dict): Dicionário com 'pontos', 'tabela' e 'shape' carregados
        line_code (str): Código da linha (ex: '541')
        geofence_radius (float): Raio do geofence circular em metros
        
    Returns:
        pd.DataFrame: Log de eventos para esta viagem
    """
    gps_direction = trip_df['SENT'].iloc[0]
    
    # Resolver dinamicamente o sentido estático e o shape ID
    sentido_static, shp_id = resolve_sentido_and_shp(trip_df, static_data)
    
    if not sentido_static:
        return pd.DataFrame()
        
    # 1. Obter pontos de parada ordenados por SEQ para este sentido
    stops_df = static_data['pontos']
    stops_df = stops_df[stops_df['SENTIDO'] == sentido_static].sort_values('SEQ').copy()
    
    if stops_df.empty:
        return pd.DataFrame()
        
    # 2. Obter shape ordenado para esta direção
    shape_df = static_data['shape']
    if shp_id and not shape_df.empty:
        shape_df = shape_df[shape_df['SHP'] == shp_id].copy()
    
    # Se o shape estiver vazio, tentamos usar a sequência de pontos de parada como shape básico
    if shape_df.empty:
        shape_df = stops_df.rename(columns={'NOME': 'SHP'})
        
    shape_lats = shape_df['LAT'].values
    shape_lons = shape_df['LON'].values
    
    # 3. Projetar pontos GPS da viagem e os pontos de parada no shape
    trip_df = trip_df.sort_values('ts').copy()
    gps_lats = trip_df['LAT'].values
    gps_lons = trip_df['LON'].values
    gps_ts = trip_df['ts'].values
    
    gps_shape_idx = map_gps_to_shape(gps_lats, gps_lons, shape_lats, shape_lons)
    # Garantir que o índice no shape do GPS é não-decrescente (sempre avança na rota)
    gps_shape_idx = np.maximum.accumulate(gps_shape_idx)
    trip_df['shape_idx'] = gps_shape_idx
    
    stop_lats = stops_df['LAT'].values
    stop_lons = stops_df['LON'].values
    stop_shape_idx = map_gps_to_shape(stop_lats, stop_lons, shape_lats, shape_lons)
    # Garantir que as paradas seguem uma ordem não-decrescente ao longo do shape
    stop_shape_idx = np.maximum.accumulate(stop_shape_idx)
    stops_df['shape_idx'] = stop_shape_idx
    
    events = []
    
    for idx, stop in stops_df.iterrows():
        # Calcular distância deste ponto de parada a todos os pontos de GPS da viagem
        dists = haversine_vectorized(
            np.full_like(gps_lats, stop['LAT']),
            np.full_like(gps_lons, stop['LON']),
            gps_lats,
            gps_lons
        )
        
        min_dist = dists.min()
        min_idx = dists.argmin()
        
        # Caso 1: Veículo passou dentro do geofence (Martins et al. 2022)
        if min_dist <= geofence_radius:
            event_ts = gps_ts[min_idx]
            events.append({
                'stop_seq': stop['SEQ'],
                'stop_num': stop['NUM'],
                'stop_name': stop['NOME'],
                'event_type': 'PASSAGE',
                'timestamp': event_ts,
                'distance': min_dist,
                'interpolated': False,
                'vehicle': trip_df['COD'].iloc[0],
                'tabela': trip_df['TABELA'].iloc[0],
                'gps_direction': gps_direction
            })
            
        # Caso 2: Gaps de sinal - Interpolação Temporal (Borges et al. 2023)
        else:
            target_idx = stop['shape_idx']
            
            # Encontrar o último ponto GPS antes do ponto de parada no shape
            before_indices = np.where(gps_shape_idx <= target_idx)[0]
            # Encontrar o primeiro ponto GPS depois do ponto de parada no shape
            after_indices = np.where(gps_shape_idx > target_idx)[0]
            
            if len(before_indices) > 0 and len(after_indices) > 0:
                idx_A = before_indices[-1]
                idx_B = after_indices[0]
                
                t_A = gps_ts[idx_A]
                t_B = gps_ts[idx_B]
                s_A = gps_shape_idx[idx_A]
                s_B = gps_shape_idx[idx_B]
                
                # Interpolação linear temporal baseada na posição do shape
                total_s = (t_B - t_A).astype('timedelta64[s]').astype(float)
                total_dist_idx = s_B - s_A
                
                if total_dist_idx > 0:
                    pct = (target_idx - s_A) / total_dist_idx
                    interpolated_delta = pd.Timedelta(seconds=total_s * pct)
                    interpolated_ts = t_A + interpolated_delta
                else:
                    # Se caírem no mesmo índice do shape, faz média simples dos tempos
                    interpolated_ts = t_A + (t_B - t_A) / 2
                    
                events.append({
                    'stop_seq': stop['SEQ'],
                    'stop_num': stop['NUM'],
                    'stop_name': stop['NOME'],
                    'event_type': 'PASSAGE',
                    'timestamp': interpolated_ts,
                    'distance': min_dist,
                    'interpolated': True,
                    'vehicle': trip_df['COD'].iloc[0],
                    'tabela': trip_df['TABELA'].iloc[0],
                    'gps_direction': gps_direction
                })
            else:
                # Extrapolação simples para início ou fim de viagem se faltar um dos lados
                # Usa o timestamp do GPS mais próximo
                event_ts = gps_ts[min_idx]
                events.append({
                    'stop_seq': stop['SEQ'],
                    'stop_num': stop['NUM'],
                    'stop_name': stop['NOME'],
                    'event_type': 'PASSAGE',
                    'timestamp': event_ts,
                    'distance': min_dist,
                    'interpolated': True, # Considerado interpolado/estimado
                    'vehicle': trip_df['COD'].iloc[0],
                    'tabela': trip_df['TABELA'].iloc[0],
                    'gps_direction': gps_direction
                })
                
    events_df = pd.DataFrame(events)
    if not events_df.empty and enforce_monotonicity:
        # Garantir que a ordem cronológica dos timestamps respeita estritamente a ordem física (stop_seq)
        # Como iteramos na ordem de stops_df (que está sorted por SEQ), events_df já está na ordem física.
        # Caso haja inversões (tempo voltando por ruído de GPS/interpolação), ajustamos somando 1 segundo.
        events_df = events_df.sort_values('stop_seq').copy()
        
        last_ts = None
        new_timestamps = []
        for idx, row in events_df.iterrows():
            ts = row['timestamp']
            if last_ts is not None and ts <= last_ts:
                ts = last_ts + pd.Timedelta(seconds=1)
            new_timestamps.append(ts)
            last_ts = ts
        events_df['timestamp'] = new_timestamps
        
    return events_df
