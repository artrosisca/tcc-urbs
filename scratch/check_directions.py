from src.etl.load_c3sl import load_static_data
from src.etl.load_realtime import load_realtime_data
from src.etl.clean_data import clean_gps_data, haversine_vectorized
import pandas as pd
import numpy as np

# Carregar dados
static = load_static_data("2025-10-24", "541")
realtime = load_realtime_data("541", "2025-10-24", "2025-10-24")
cleaned = clean_gps_data(realtime, static['pontos'])

# Pegar um veículo específico (ex: GA181)
df_v = cleaned[cleaned['COD'] == 'GA181'].sort_values('ts').copy()

# Encontrar as viagens
df_v['sent_change'] = df_v['SENT'] != df_v['SENT'].shift(1)
df_v['trip_id'] = df_v['sent_change'].cumsum()

# Terminais
term_sitio = (-25.534155, -49.267309) # Terminal Sítio Cercado
bairro_novo = (-25.543665, -49.248618) # Bairro Novo A

for trip_num, group in df_v.groupby('trip_id'):
    direction = group['SENT'].iloc[0]
    start_point = (group['LAT'].iloc[0], group['LON'].iloc[0])
    end_point = (group['LAT'].iloc[-1], group['LON'].iloc[-1])
    
    # Distâncias aos terminais
    dist_start_term = haversine_vectorized(start_point[0], start_point[1], term_sitio[0], term_sitio[1])
    dist_end_term = haversine_vectorized(end_point[0], end_point[1], term_sitio[0], term_sitio[1])
    
    dist_start_bn = haversine_vectorized(start_point[0], start_point[1], bairro_novo[0], bairro_novo[1])
    dist_end_bn = haversine_vectorized(end_point[0], end_point[1], bairro_novo[0], bairro_novo[1])
    
    print(f"Viagem {trip_num} | SENT no GPS = {direction}")
    print(f"  Ponto inicial GPS: dist a Terminal={dist_start_term:.0f}m, dist a Bairro Novo={dist_start_bn:.0f}m")
    print(f"  Ponto final GPS:   dist a Terminal={dist_end_term:.0f}m, dist a Bairro Novo={dist_end_bn:.0f}m")
