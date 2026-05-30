import pandas as pd
import numpy as np

def haversine_vectorized(lat1, lon1, lat2, lon2):
    """Calcula a distância de Haversine em metros entre duas séries de coordenadas."""
    r_lat1, r_lon1, r_lat2, r_lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = r_lat2 - r_lat1
    dlon = r_lon2 - r_lon1
    a = np.sin(dlat/2)**2 + np.cos(r_lat1) * np.cos(r_lat2) * np.sin(dlon/2)**2
    return 6371000 * 2 * np.arcsin(np.sqrt(a))

def clean_gps_data(df_realtime, static_stops_df, distance_threshold=5.0, outlier_threshold=500.0):
    """
    Executa a limpeza completa dos dados de GPS em tempo real.
    
    Args:
        df_realtime (pd.DataFrame): Dados em tempo real consolidados
        static_stops_df (pd.DataFrame): Pontos de parada da linha (para detecção de outliers)
        distance_threshold (float): Distância mínima em metros para considerar que o veículo se moveu
        outlier_threshold (float): Distância máxima permitida em metros de qualquer ponto de parada
        
    Returns:
        pd.DataFrame: DataFrame limpo
    """
    if df_realtime.empty:
        return df_realtime
        
    initial_rows = len(df_realtime)
    print(f"\n--- Iniciando limpeza de dados (Total inicial: {initial_rows} registros) ---")
    
    # 1. Remover registros onde latitude ou longitude são nulos
    df = df_realtime.dropna(subset=['LAT', 'LON']).copy()
    rows_after_nan_coords = len(df)
    print(f"1. Coordenadas nulas removidas: {initial_rows - rows_after_nan_coords} registros.")
    
    # 2. Filtrar registros REC (veículos recolhidos/garagem)
    # Alguns registros podem ter CODIGOLINHA == 'REC' ou SENT/SITUACAO nulos que indicam recolhimento
    if 'CODIGOLINHA' in df.columns:
        df = df[df['CODIGOLINHA'].astype(str) != 'REC']
    rows_after_rec = len(df)
    print(f"2. Registros da linha 'REC' (garagem) removidos: {rows_after_nan_coords - rows_after_rec} registros.")
    
    # 3. Remover registros operacionais com SITUACAO ou SENT nulos (que representam transições/rec)
    df = df.dropna(subset=['SITUACAO', 'SENT'])
    rows_after_nulls = len(df)
    print(f"3. Registros com SITUACAO/SENT nulos removidos: {rows_after_rec - rows_after_nulls} registros.")
    
    if df.empty:
        print("Aviso: Nenhum registro sobrou após as etapas iniciais de limpeza.")
        return df
        
    # 4. Remover duplicatas exatas de (veículo + timestamp)
    df = df.drop_duplicates(subset=['COD', 'request_timestamp'])
    rows_after_dupes = len(df)
    print(f"4. Duplicatas exatas (veículo+timestamp) removidas: {rows_after_nulls - rows_after_dupes} registros.")
    
    # 5. Ordenar por veículo e timestamp
    df['ts'] = pd.to_datetime(df['request_timestamp'])
    df = df.sort_values(by=['COD', 'ts'])
    
    # 6. Remover leituras consecutivas com GPS estacionário (< 5 metros)
    df['prev_lat'] = df.groupby('COD')['LAT'].shift(1)
    df['prev_lon'] = df.groupby('COD')['LON'].shift(1)
    
    # Para o primeiro registro de cada veículo, prev_lat/lon será NaN, logo a distância será NaN
    df['dist_prev'] = haversine_vectorized(df['LAT'], df['LON'], df['prev_lat'], df['prev_lon'])
    
    # Manter se for a primeira leitura do veículo (NaN) OU se moveu >= threshold
    keep_mask = df['dist_prev'].isna() | (df['dist_prev'] >= distance_threshold)
    df = df[keep_mask].copy()
    
    # Remover colunas temporárias
    df = df.drop(columns=['prev_lat', 'prev_lon', 'dist_prev'])
    rows_after_stationary = len(df)
    print(f"5. Registros de GPS estacionário (<{distance_threshold}m) removidos: {rows_after_dupes - rows_after_stationary} registros.")
    
    # 7. Filtrar outliers (leituras > 500m de qualquer ponto de parada planejado)
    if not static_stops_df.empty:
        # Extrair coordenadas dos pontos estáticos como arrays para busca rápida
        stop_lats = static_stops_df['LAT'].values
        stop_lons = static_stops_df['LON'].values
        
        valid_gps = []
        for idx, row in df.iterrows():
            # Calcular distância deste ponto de GPS a TODOS os pontos de parada da linha
            # Usando uma versão otimizada com numpy
            dists = haversine_vectorized(
                np.full_like(stop_lats, row['LAT']), 
                np.full_like(stop_lons, row['LON']), 
                stop_lats, 
                stop_lons
            )
            min_dist = dists.min()
            if min_dist <= outlier_threshold:
                valid_gps.append(True)
            else:
                valid_gps.append(False)
                
        df = df[valid_gps].copy()
        
    rows_after_outliers = len(df)
    print(f"6. Outliers de GPS (>{outlier_threshold}m da rota) removidos: {rows_after_stationary - rows_after_outliers} registros.")
    print(f"--- Limpeza Concluída: {rows_after_outliers} registros restantes ({rows_after_outliers/initial_rows*100:.1f}% do original) ---\n")
    
    return df

if __name__ == "__main__":
    from src.etl.load_c3sl import load_static_data
    from src.etl.load_realtime import load_realtime_data
    
    # Teste rápido
    static = load_static_data("2025-10-24", "541")
    realtime = load_realtime_data("541", "2025-10-24", "2025-10-24")
    
    cleaned = clean_gps_data(realtime, static['pontos'])
    if not cleaned.empty:
        print("Exemplo de dados limpos:")
        print(cleaned[['COD', 'request_timestamp', 'LAT', 'LON', 'SENT', 'SITUACAO']].head(5))
