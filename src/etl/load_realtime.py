import os
import pandas as pd
from datetime import datetime

def load_realtime_data(line_code, start_date, end_date, data_dir="dados_em_tempo_real_2026"):
    """
    Carrega e consolida dados em tempo real para uma linha específica e um período.
    
    Args:
        line_code (str): Código da linha (ex: '541')
        start_date (str): Data inicial no formato 'YYYY-MM-DD'
        end_date (str): Data final no formato 'YYYY-MM-DD'
        data_dir (str): Caminho para a pasta raiz dos dados em tempo real
        
    Returns:
        pd.DataFrame: DataFrame contendo todos os registros da linha no período
    """
    # Converter para datas e gerar intervalo
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError as e:
        print(f"Erro no formato das datas. Use YYYY-MM-DD. Detalhe: {e}")
        return pd.DataFrame()
        
    date_list = pd.date_range(start_dt, end_dt).strftime("%Y-%m-%d").tolist()
    
    dfs = []
    total_files_loaded = 0
    
    for date_str in date_list:
        day_dir = os.path.join(data_dir, date_str)
        if not os.path.exists(day_dir):
            # Tentar também com sublinhado se houver discrepância
            day_dir_alt = os.path.join(data_dir, date_str.replace('-', '_'))
            if os.path.exists(day_dir_alt):
                day_dir = day_dir_alt
            else:
                print(f"Aviso: Diretório para a data {date_str} não encontrado.")
                continue
                
        # Listar e ler CSVs
        csv_files = sorted([f for f in os.listdir(day_dir) if f.endswith('.csv')])
        for csv_file in csv_files:
            filepath = os.path.join(day_dir, csv_file)
            try:
                # Otimização: ler apenas as colunas necessárias para economizar memória
                df_temp = pd.read_csv(filepath)
                # Filtrar imediatamente pela linha
                if 'CODIGOLINHA' in df_temp.columns:
                    # Garantir que é string para comparação
                    df_filtered = df_temp[df_temp['CODIGOLINHA'].astype(str) == str(line_code)].copy()
                    if not df_filtered.empty:
                        dfs.append(df_filtered)
                total_files_loaded += 1
            except Exception as e:
                print(f"Erro ao ler arquivo {filepath}: {e}")
                
    if not dfs:
        print(f"Nenhum registro encontrado para a linha {line_code} no período de {start_date} a {end_date}.")
        return pd.DataFrame()
        
    df_consolidated = pd.concat(dfs, ignore_index=True)
    print(f"Consolidado com sucesso: {len(df_consolidated)} registros a partir de {total_files_loaded} arquivos.")
    return df_consolidated

if __name__ == "__main__":
    # Teste rápido
    df_res = load_realtime_data("541", "2025-10-24", "2025-10-24")
    if not df_res.empty:
        print(df_res.head(3))
        print("Veículos únicos:", df_res['COD'].unique())
        print("Colunas carregadas:", df_res.columns)
