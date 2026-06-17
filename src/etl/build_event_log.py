import os
import pandas as pd
import pm4py
from src.etl.load_c3sl import load_static_data
from src.etl.load_realtime import load_realtime_data
from src.etl.clean_data import clean_gps_data
from src.etl.geofencing import match_trip_events

def build_event_log(line_code, start_date, end_date, output_dir="data/dados_processados"):
    """
    Gera o Log de Eventos consolidado no formato adequado para Mineração de Processos (PM4Py).
    
    Args:
        line_code (str): Código da linha (ex: '541')
        start_date (str): Data de início 'YYYY-MM-DD'
        end_date (str): Data de fim 'YYYY-MM-DD'
        output_dir (str): Pasta de destino para os logs gerados
        
    Returns:
        pd.DataFrame: DataFrame contendo o Event Log formatado
    """
    # 1. Carregar e consolidar dados em tempo real
    df_realtime = load_realtime_data(line_code, start_date, end_date)
    if df_realtime.empty:
        print("Erro: Não foi possível obter dados em tempo real.")
        return pd.DataFrame()
        
    # Carregar dados estáticos correspondentes à primeira data do período (como referência)
    static_data = load_static_data(start_date, line_code)
    if static_data['pontos'].empty:
        print("Erro: Não foi possível obter pontos de parada estáticos.")
        return pd.DataFrame()
        
    # 2. Limpar dados
    df_clean = clean_gps_data(df_realtime, static_data['pontos'])
    if df_clean.empty:
        print("Erro: Nenhum dado restou após a limpeza.")
        return pd.DataFrame()
        
    # 3. Processar viagens
    all_events = []
    
    # Agrupar por veículo e por dia
    df_clean['data_str'] = df_clean['ts'].dt.strftime('%Y-%m-%d')
    
    for (vehicle_cod, day_str), group in df_clean.groupby(['COD', 'data_str']):
        # Ordenar por tempo
        group = group.sort_values('ts')
        
        # Calcular a diferença de tempo em minutos em relação ao ponto anterior
        group['time_diff'] = group['ts'].diff().dt.total_seconds() / 60.0
        
        # Segmentar em viagens com base na mudança de sentido (SENT) OU inatividade de mais de 10 minutos
        group['sent_change'] = (group['SENT'] != group['SENT'].shift(1)) | (group['time_diff'] > 10.0)
        group['trip_num'] = group['sent_change'].cumsum()
        
        for trip_num, trip_group in group.groupby('trip_num'):
            if len(trip_group) < 3:
                continue # Pula viagens muito curtas (ruído)
                
            # Executar map matching + geofencing + interpolação nesta viagem
            trip_events = match_trip_events(trip_group, static_data, line_code)
            if not trip_events.empty:
                # Criar identificador de caso único para mineração (case:concept:name)
                # Formato: {VEICULO}_{LINHA}_{TABELA}_{DATA}_{VIAGEM}
                case_id = f"{vehicle_cod}_{line_code}_{trip_group['TABELA'].iloc[0]}_{day_str}_V{trip_num}"
                trip_events['case:concept:name'] = case_id
                all_events.append(trip_events)
                
    if not all_events:
        print("Nenhum evento pôde ser gerado a partir das viagens detectadas.")
        return pd.DataFrame()
        
    # 4. Consolidar e formatar para PM4Py
    df_log = pd.concat(all_events, ignore_index=True)
    
    # Mapear nomes de colunas exigidos pela especificação XES/PM4Py
    df_log = df_log.rename(columns={
        'stop_name': 'concept:name',       # Nome da atividade (ex: PASSAGEM_Terminal Sitio Cercado)
        'timestamp': 'time:timestamp',     # Carimbo de data/hora
        'vehicle': 'org:resource'          # Recurso operacional
    })
    
    # PREFIXAR o nome do ponto com "PASSAGEM_" para ficar coerente com a nomenclatura do plano
    df_log['concept:name'] = 'PASSAGEM_' + df_log['concept:name'].astype(str)
    
    # Garantir que o timestamp é datetime com timezone ou sem timezone (ingênuo)
    df_log['time:timestamp'] = pd.to_datetime(df_log['time:timestamp'])
    
    # Ordenar por caso e timestamp
    df_log = df_log.sort_values(by=['case:concept:name', 'stop_seq'])
    
    # 5. Salvar em disco
    os.makedirs(output_dir, exist_ok=True)
    
    # Salvar em CSV
    csv_path = os.path.join(output_dir, f"event_log_{line_code}_{start_date}_{end_date}.csv")
    df_log.to_csv(csv_path, index=False, encoding='utf-8')
    print(f"Event Log salvo em CSV: {csv_path} ({len(df_log)} eventos)")
    
    # Salvar em XES (padrão de Process Mining)
    xes_path = os.path.join(output_dir, f"event_log_{line_code}_{start_date}_{end_date}.xes")
    try:
        # Converter dataframe pandas para objeto EventLog do PM4Py
        # O PM4Py gerencia colunas 'case:concept:name', 'concept:name' e 'time:timestamp' automaticamente
        event_log_pm4py = pm4py.format_dataframe(df_log, case_id='case:concept:name', activity_key='concept:name', timestamp_key='time:timestamp')
        pm4py.write_xes(event_log_pm4py, xes_path)
        print(f"Event Log salvo em XES: {xes_path}")
    except Exception as e:
        print(f"Erro ao salvar arquivo XES com PM4Py: {e}")
        
    return df_log

if __name__ == "__main__":
    # Teste rápido de 1 dia (Regime A)
    print("Testando geração do Event Log...")
    df_log = build_event_log("541", "2025-10-24", "2025-10-24")
    if not df_log.empty:
        print("\nExemplo do Event Log Gerado:")
        print(df_log[['case:concept:name', 'concept:name', 'time:timestamp', 'interpolated', 'stop_seq']].head(15))
