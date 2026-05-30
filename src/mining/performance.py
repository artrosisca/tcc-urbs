import pandas as pd
import numpy as np

def analyze_segment_performance(event_log_df):
    """
    Calcula o tempo de viagem entre pontos de parada consecutivos (gargalos).
    
    Args:
        event_log_df (pd.DataFrame): Log de eventos
        
    Returns:
        pd.DataFrame: Estatísticas de tempo de viagem por trecho/segmento
    """
    if event_log_df.empty:
        return pd.DataFrame()
        
    # Garantir ordenação por caso e seq de pontos
    df = event_log_df.sort_values(by=['case:concept:name', 'stop_seq']).copy()
    
    # Adicionar colunas do ponto anterior
    df['prev_stop'] = df.groupby('case:concept:name')['concept:name'].shift(1)
    df['prev_timestamp'] = df.groupby('case:concept:name')['time:timestamp'].shift(1)
    
    # Filtrar apenas registros que têm um ponto anterior (pula a primeira parada de cada viagem)
    df_segments = df.dropna(subset=['prev_stop']).copy()
    
    # Calcular delta tempo em segundos e minutos
    df_segments['duration_sec'] = (df_segments['time:timestamp'] - df_segments['prev_timestamp']).dt.total_seconds()
    df_segments['duration_min'] = df_segments['duration_sec'] / 60.0
    
    # Criar label do segmento
    # Remover o prefixo PASSAGEM_ das labels para ficar mais limpo
    df_segments['segment_name'] = df_segments['prev_stop'].str.replace('PASSAGEM_', '') + " -> " + df_segments['concept:name'].str.replace('PASSAGEM_', '')
    
    # Agrupar por segmento e calcular estatísticas
    segment_stats = df_segments.groupby('segment_name').agg(
        total_passages=('case:concept:name', 'count'),
        mean_time_min=('duration_min', 'mean'),
        median_time_min=('duration_min', 'median'),
        std_time_min=('duration_min', 'std'),
        max_time_min=('duration_min', 'max'),
        min_time_min=('duration_min', 'min')
    ).reset_index()
    
    # Ordenar por tempo médio para identificar gargalos
    segment_stats = segment_stats.sort_values(by='mean_time_min', ascending=False)
    
    return segment_stats

def analyze_schedule_delays(event_log_df, planned_table_df, date_str, static_stops_df=None):
    """
    Calcula a pontualidade comparando horários reais de saída com os planejados.
    
    Args:
        event_log_df (pd.DataFrame): Log de eventos
        planned_table_df (pd.DataFrame): Tabela de horários planejados
        date_str (str): Data da operação 'YYYY-MM-DD'
        static_stops_df (pd.DataFrame, opcional): Pontos de parada estáticos para resolução de nomes
        
    Returns:
        pd.DataFrame: Atrasos calculados por viagem
    """
    if event_log_df.empty or planned_table_df.empty:
        return pd.DataFrame()
        
    # Converter date_str para dia da semana correspondente na tabela da URBS
    # DIA: '1' (útil), '2' (sábado), '3' (domingo)
    dt = pd.to_datetime(date_str)
    weekday = dt.weekday() # 0 (segunda) a 6 (domingo)
    if weekday < 5:
        dia_urbs = '1'
    elif weekday == 5:
        dia_urbs = '2'
    else:
        dia_urbs = '3'
        
    # Filtrar tabela planejada para o tipo de dia correspondente
    planned_day = planned_table_df[planned_table_df['DIA'] == dia_urbs].copy()
    if planned_day.empty:
        return pd.DataFrame()
        
    # Identificar saídas reais dos terminais de cada viagem
    # A saída ocorre no stop_seq = 1
    departures = event_log_df[event_log_df['stop_seq'] == 1].copy()
    
    # Mapear cada gps_direction para o seu ponto de controle (partida) correspondente
    control_point_mapping = {}
    control_points = planned_day['PONTO'].unique()
    
    if len(control_points) == 1:
        # Apenas um ponto de controle disponível
        for gps_dir in event_log_df['gps_direction'].unique():
            control_point_mapping[gps_dir] = control_points[0]
    elif len(control_points) >= 2 and static_stops_df is not None and not static_stops_df.empty:
        # Resolver usando acoplamento reverso Jaccard dos nomes dos sentidos
        gps_dirs = event_log_df['gps_direction'].unique()
        sentido_mapping = {}
        for gps_dir in gps_dirs:
            group = event_log_df[event_log_df['gps_direction'] == gps_dir]
            if not group.empty:
                first_concept = group['concept:name'].iloc[0]
                sample_stop_name = first_concept.replace('PASSAGEM_', '')
                matching_stops = static_stops_df[static_stops_df['NOME'] == sample_stop_name]
                if not matching_stops.empty:
                    sentido_mapping[gps_dir] = matching_stops['SENTIDO'].iloc[0]
                    
        # Se conseguimos identificar os sentidos para ambas as direções
        if len(sentido_mapping) >= 2:
            import unicodedata
            import re
            
            def normalize_txt(text):
                if not text:
                    return ""
                text = str(text).upper()
                text = "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
                text = re.sub(r'[^A-Z0-9\s]', ' ', text)
                return " ".join(text.split())

            def get_word_intersection(s1, s2):
                w1 = set(normalize_txt(s1).split())
                w2 = set(normalize_txt(s2).split())
                return len(w1.intersection(w2))
                
            dirs_list = list(sentido_mapping.keys())[:2]
            sent0, sent1 = sentido_mapping[dirs_list[0]], sentido_mapping[dirs_list[1]]
            cp0, cp1 = control_points[0], control_points[1]
            
            score_p1 = get_word_intersection(sent0, cp0) + get_word_intersection(sent1, cp1)
            score_p2 = get_word_intersection(sent0, cp1) + get_word_intersection(sent1, cp0)
            
            # Se sent0 (destino) matches cp0 (destino), então seu ponto de partida é cp1!
            if score_p1 >= score_p2:
                control_point_mapping[dirs_list[0]] = cp1
                control_point_mapping[dirs_list[1]] = cp0
            else:
                control_point_mapping[dirs_list[0]] = cp0
                control_point_mapping[dirs_list[1]] = cp1
                
    # Fallback caso não consiga resolver dinamicamente
    for gps_dir in event_log_df['gps_direction'].unique():
        if gps_dir not in control_point_mapping:
            if gps_dir == 'VOLTA':
                control_point_mapping[gps_dir] = control_points[0] if len(control_points) > 0 else None
            else:
                control_point_mapping[gps_dir] = control_points[1] if len(control_points) > 1 else (control_points[0] if len(control_points) > 0 else None)
    
    delays = []
    
    for idx, row in departures.iterrows():
        case_id = row['case:concept:name']
        tabela = str(row['tabela'])
        actual_time = row['time:timestamp']
        gps_dir = row['gps_direction']
        
        # Mapear ponto de controle na tabela planejada correspondente à saída desta direção
        control_point = control_point_mapping.get(gps_dir)
        
        # Filtrar tabela planejada por tabela (run) e ponto de controle
        planned_times = planned_day[
            (planned_day['TABELA'].astype(str) == tabela) & 
            (planned_day['PONTO'] == control_point)
        ].copy()
        
        if planned_times.empty:
            continue
            
        # Converter horários planejados (string "HH:MM") para datetime na mesma data
        planned_datetimes = []
        for h in planned_times['HORA']:
            h_dt = pd.to_datetime(f"{date_str} {h}:00")
            # Lidar com virada da meia-noite se necessário
            if h.startswith('00') and actual_time.hour == 23:
                h_dt += pd.Timedelta(days=1)
            planned_datetimes.append(h_dt)
            
        # Achar o horário planejado mais próximo da saída real
        dists = [abs((actual_time - p_dt).total_seconds()) for p_dt in planned_datetimes]
        min_idx = np.argmin(dists)
        closest_planned = planned_datetimes[min_idx]
        
        # Diferença em minutos (positivo = atraso, negativo = adiantado)
        delay_min = (actual_time - closest_planned).total_seconds() / 60.0
        
        # Só registrar se o horário planejado mais próximo estiver em uma janela de 45 minutos
        # (evita casamentos errados para ônibus que quebraram ou saíram de escala)
        if abs(delay_min) <= 45:
            delays.append({
                'case_id': case_id,
                'vehicle': row['org:resource'],
                'tabela': tabela,
                'direction': gps_dir,
                'planned_departure': closest_planned.strftime('%H:%M'),
                'actual_departure': actual_time.strftime('%H:%M:%S'),
                'delay_minutes': delay_min,
                'status': 'ATRASADO' if delay_min > 5 else ('ADIANTADO' if delay_min < -2 else 'NO HORÁRIO')
            })
            
    return pd.DataFrame(delays)

if __name__ == "__main__":
    from src.etl.load_c3sl import load_static_data
    import os
    
    # Teste rápido
    csv_path = "dados_processados/event_log_541_2025-10-24_2025-10-24.csv"
    if os.path.exists(csv_path):
        print(f"Lendo log de testes de: {csv_path}")
        df = pd.read_csv(csv_path)
        df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
        
        # 1. Testar análise de segmentos
        print("\n=== MAIORES GARGALOS DETECTADOS (TEMPO MÉDIO DE VIAGEM) ===")
        df_seg = analyze_segment_performance(df)
        print(df_seg[['segment_name', 'total_passages', 'mean_time_min', 'max_time_min']].head(5))
        
        # 2. Testar análise de pontualidade
        static = load_static_data("2025-10-24", "541")
        df_delays = analyze_schedule_delays(df, static['tabela'], "2025-10-24")
        if not df_delays.empty:
            print("\n=== ANÁLISE DE PONTUALIDADE (ATRASOS) ===")
            print(df_delays[['case_id', 'planned_departure', 'actual_departure', 'delay_minutes', 'status']].head(5))
            print("\nDistribuição de status de pontualidade:")
            print(df_delays['status'].value_counts())
    else:
        print("Execute o ETL primeiro para rodar este teste.")
