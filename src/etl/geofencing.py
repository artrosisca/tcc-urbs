import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
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

def map_gps_to_shape_hmm(gps_lats, gps_lons, shape_lats, shape_lons, search_radius=150.0, sigma_z=30.0, beta=50.0):
    """
    Projeta coordenadas GPS nos índices sequenciais da rota física (shape) usando HMM + Viterbi.
    
    Args:
        gps_lats (np.ndarray): Latitudes da telemetria GPS
        gps_lons (np.ndarray): Longitudes da telemetria GPS
        shape_lats (np.ndarray): Latitudes do shape estático
        shape_lons (np.ndarray): Longitudes do shape estático
        search_radius (float): Raio de busca para candidatos no shape (metros)
        sigma_z (float): Erro de medição do GPS (metros)
        beta (float): Parâmetro da distribuição de transição (metros)
        
    Returns:
        np.ndarray: Sequência ótima de índices do shape para cada ponto de GPS
    """
    n_gps = len(gps_lats)
    n_shape = len(shape_lats)
    
    if n_gps == 0 or n_shape == 0:
        return np.array([])
        
    # 1. Calcular distância Haversine acumulada ao longo do shape
    shape_dists = np.zeros(n_shape)
    if n_shape > 1:
        shape_dists[1:] = haversine_vectorized(
            shape_lats[:-1], shape_lons[:-1],
            shape_lats[1:], shape_lons[1:]
        )
    shape_cum_dists = np.cumsum(shape_dists)
    
    # 2. Gerar candidatos para cada ponto GPS
    candidate_states = []
    
    for i in range(n_gps):
        gps_lat = gps_lats[i]
        gps_lon = gps_lons[i]
        
        dists = haversine_vectorized(
            np.full_like(shape_lats, gps_lat),
            np.full_like(shape_lons, gps_lon),
            shape_lats,
            shape_lons
        )
        
        cand_indices = np.where(dists <= search_radius)[0]
        
        if len(cand_indices) == 0:
            cand_indices = np.array([dists.argmin()])
            
        cands = []
        for idx in cand_indices:
            cands.append({
                'idx': idx,
                'dist': dists[idx],
                's': shape_cum_dists[idx]
            })
        candidate_states.append(cands)
        
    # 3. Execução do Algoritmo de Viterbi em log-space
    V = []
    ptr = []
    
    cands_0 = candidate_states[0]
    V_0 = np.zeros(len(cands_0))
    for j, cand in enumerate(cands_0):
        V_0[j] = -0.5 * ((cand['dist'] / sigma_z) ** 2)
    V.append(V_0)
    ptr.append(np.zeros(len(cands_0), dtype=int))
    
    for i in range(1, n_gps):
        cands_prev = candidate_states[i-1]
        cands_curr = candidate_states[i]
        
        dist_gps = haversine_vectorized(
            np.array([gps_lats[i-1]]), np.array([gps_lons[i-1]]),
            np.array([gps_lats[i]]), np.array([gps_lons[i]])
        )[0]
        
        V_curr = np.zeros(len(cands_curr))
        ptr_curr = np.zeros(len(cands_curr), dtype=int)
        
        for j, cand_curr in enumerate(cands_curr):
            best_log_prob = -np.inf
            best_prev_idx = 0
            
            for k, cand_prev in enumerate(cands_prev):
                delta_shape = cand_curr['s'] - cand_prev['s']
                
                # Tolerância a pequenos retrocessos locais (e.g. 20m) devido a jitter GPS em paradas
                if delta_shape < -20.0:
                    log_trans = -np.inf
                else:
                    delta_shape_clamped = max(0.0, delta_shape)
                    log_trans = -abs(dist_gps - delta_shape_clamped) / beta
                    
                log_prob = V[-1][k] + log_trans
                if log_prob > best_log_prob:
                    best_log_prob = log_prob
                    best_prev_idx = k
            
            # Restart se o trellis falhar (por exemplo, quebras graves de sinal)
            if best_log_prob == -np.inf:
                best_log_prob = 0.0
                prev_s_vals = np.array([c['s'] for c in cands_prev])
                best_prev_idx = np.abs(prev_s_vals - cand_curr['s']).argmin()
                
            log_emission = -0.5 * ((cand_curr['dist'] / sigma_z) ** 2)
            V_curr[j] = log_emission + best_log_prob
            ptr_curr[j] = best_prev_idx
            
        V.append(V_curr)
        ptr.append(ptr_curr)
        
    # 4. Backtracking
    optimal_indices = np.zeros(n_gps, dtype=int)
    best_last_state = np.argmax(V[-1])
    optimal_indices[-1] = candidate_states[-1][best_last_state]['idx']
    
    curr_state_idx = best_last_state
    for i in range(n_gps - 1, 0, -1):
        prev_state_idx = ptr[i][curr_state_idx]
        optimal_indices[i-1] = candidate_states[i-1][prev_state_idx]['idx']
        curr_state_idx = prev_state_idx
        
    return optimal_indices

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
    Aplica geofencing e interpolação spline cúbica monótona para uma viagem individual.
    
    Args:
        trip_df (pd.DataFrame): Dados de GPS de uma única viagem
        static_data (dict): Dicionário com 'pontos', 'tabela' e 'shape' carregados
        line_code (str): Código da linha (ex: '541')
        geofence_radius (float): Raio de geofence (mantido na assinatura, mas ignorado)
        
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
    
    # Calcular distância acumulada ao longo do shape
    shape_dists = np.zeros(len(shape_lats))
    if len(shape_lats) > 1:
        shape_dists[1:] = haversine_vectorized(
            shape_lats[:-1], shape_lons[:-1],
            shape_lats[1:], shape_lons[1:]
        )
    shape_cum_dists = np.cumsum(shape_dists)
    
    # 3. Projetar pontos GPS da viagem e os pontos de parada no shape
    trip_df = trip_df.sort_values('ts').copy()
    gps_lats = trip_df['LAT'].values
    gps_lons = trip_df['LON'].values
    gps_ts = trip_df['ts'].values
    
    gps_shape_idx = map_gps_to_shape_hmm(gps_lats, gps_lons, shape_lats, shape_lons)
    # Garantir que o índice no shape do GPS é não-decrescente (sempre avança na rota)
    gps_shape_idx = np.maximum.accumulate(gps_shape_idx)
    trip_df['shape_idx'] = gps_shape_idx
    
    gps_cum_dists = shape_cum_dists[gps_shape_idx]
    
    stop_lats = stops_df['LAT'].values
    stop_lons = stops_df['LON'].values
    stop_shape_idx = map_gps_to_shape(stop_lats, stop_lons, shape_lats, shape_lons)
    stop_shape_idx = np.maximum.accumulate(stop_shape_idx)
    stops_df['shape_idx'] = stop_shape_idx
    
    stop_cum_dists = shape_cum_dists[stop_shape_idx]
    stops_df['cum_dist'] = stop_cum_dists
    
    # Converter timestamps para segundos unix epoch (float)
    gps_ts_floats = pd.to_datetime(gps_ts).astype('datetime64[ns]').view('int64') / 1e9
    
    # Consolidar pontos estacionários: agrupar por distância acumulada no shape
    df_pts = pd.DataFrame({'s': gps_cum_dists, 't': gps_ts_floats})
    df_unique = df_pts.groupby('s')['t'].mean().reset_index().sort_values('s')
    
    s_unique = df_unique['s'].values
    t_unique = df_unique['t'].values
    
    # Ajustar interpolador Pchip
    if len(s_unique) < 2:
        def pchip_fallback(s_val):
            return t_unique[0] if len(t_unique) > 0 else 0.0
        pchip = pchip_fallback
    else:
        pchip = PchipInterpolator(s_unique, t_unique)
        
    s_min, s_max = s_unique[0], s_unique[-1]
    t_min, t_max = t_unique[0], t_unique[-1]
    
    events = []
    
    for idx, stop in stops_df.iterrows():
        # Calcular distância deste ponto de parada a todos os pontos de GPS da viagem (para fins informativos)
        dists = haversine_vectorized(
            np.full_like(gps_lats, stop['LAT']),
            np.full_like(gps_lons, stop['LON']),
            gps_lats,
            gps_lons
        )
        min_dist = dists.min()
        
        s_stop = stop['cum_dist']
        
        # Interpolação Spline Monótona (dentro do intervalo útil)
        if s_min <= s_stop <= s_max:
            t_stop = pchip(s_stop)
        # Extrapolação linear backwards
        elif s_stop < s_min:
            if len(s_unique) >= 2 and (s_unique[1] - s_unique[0]) > 0 and (t_unique[1] - t_unique[0]) > 0:
                speed = (s_unique[1] - s_unique[0]) / (t_unique[1] - t_unique[0])
                t_stop = t_min - (s_min - s_stop) / speed
            else:
                t_stop = t_min
        # Extrapolação linear forwards
        else:
            if len(s_unique) >= 2 and (s_unique[-1] - s_unique[-2]) > 0 and (t_unique[-1] - t_unique[-2]) > 0:
                speed = (s_unique[-1] - s_unique[-2]) / (t_unique[-1] - t_unique[-2])
                t_stop = t_max + (s_stop - s_max) / speed
            else:
                t_stop = t_max
                
        # Converter timestamp resultante de volta
        t_stop_timestamp = pd.to_datetime(t_stop, unit='s')
        if hasattr(trip_df['ts'].dt, 'tz') and trip_df['ts'].dt.tz is not None:
            t_stop_timestamp = t_stop_timestamp.tz_localize('UTC').tz_convert(trip_df['ts'].dt.tz)
            
        events.append({
            'stop_seq': stop['SEQ'],
            'stop_num': stop['NUM'],
            'stop_name': stop['NOME'],
            'event_type': 'PASSAGE',
            'timestamp': t_stop_timestamp,
            'distance': min_dist,
            'interpolated': bool(min_dist > 100.0),
            'vehicle': trip_df['COD'].iloc[0],
            'tabela': trip_df['TABELA'].iloc[0],
            'gps_direction': gps_direction,
            'cum_dist': s_stop
        })
        
    events_df = pd.DataFrame(events)
    if not events_df.empty and enforce_monotonicity:
        events_df = events_df.sort_values('stop_seq').copy()
        
        last_ts = None
        last_s = None
        new_timestamps = []
        for idx, row in events_df.iterrows():
            ts = row['timestamp']
            s_val = row.get('cum_dist', 0.0)
            
            if last_ts is not None:
                d_space = s_val - last_s
                # Velocidade máxima de 80 km/h (22.2 m/s), tempo mínimo de 5.0 segundos
                min_seconds = max(5.0, d_space / 22.2) if d_space > 0 else 5.0
                min_ts = last_ts + pd.Timedelta(seconds=min_seconds)
                if ts < min_ts:
                    ts = min_ts
            new_timestamps.append(ts)
            last_ts = ts
            last_s = s_val
        events_df['timestamp'] = new_timestamps
        
    return events_df
