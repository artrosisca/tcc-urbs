"""Análise mais profunda dos dados para definir pipeline de tratamento."""
import pandas as pd
import lzma
import json
import os
from math import radians, cos, sin, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    return 6371000 * 2 * asin(sqrt(a))

# Carregar 1 dia
csv_dir = 'dados_em_tempo_real_2026/2025-10-24'
dfs = []
for f in sorted(os.listdir(csv_dir)):
    if f.endswith('.csv'):
        dfs.append(pd.read_csv(os.path.join(csv_dir, f)))
df_dia = pd.concat(dfs, ignore_index=True)

print("=" * 60)
print("PROBLEMAS IDENTIFICADOS NOS DADOS")
print("=" * 60)

# 1. Registros REC (veículos no recolhimento/garagem)
rec = df_dia[df_dia['CODIGOLINHA'] == 'REC']
print(f"\n1. REGISTROS 'REC' (veículo recolhido/garagem)")
print(f"   Total: {len(rec)} ({len(rec)/len(df_dia)*100:.1f}% do total)")
print(f"   -> AÇÃO: Filtrar esses registros (não estão em operação)")

# 2. Linhas X** (expressas/especiais)
linhas_x = df_dia[df_dia['CODIGOLINHA'].astype(str).str.startswith('X')]
print(f"\n2. LINHAS 'X**' (expressas/reforço)")
print(f"   Total: {len(linhas_x)} ({len(linhas_x)/len(df_dia)*100:.1f}%)")
print(f"   Valores: {sorted(linhas_x['CODIGOLINHA'].unique())}")
print(f"   -> AÇÃO: Decidir se incluir (são linhas reforço do expresso)")

# 3. Campos nulos
print(f"\n3. CAMPOS NULOS")
for col in df_dia.columns:
    n = df_dia[col].isna().sum()
    if n > 0:
        print(f"   {col}: {n} nulos ({n/len(df_dia)*100:.1f}%)")

# 4. Registros sem situação (correlação com REC)
sem_situacao = df_dia[df_dia['SITUACAO'].isna()]
sem_sit_rec = sem_situacao[sem_situacao['CODIGOLINHA'] == 'REC']
print(f"\n4. SEM SITUAÇÃO vs REC")
print(f"   Sem situação: {len(sem_situacao)}")
print(f"   Desses, são REC: {len(sem_sit_rec)} ({len(sem_sit_rec)/len(sem_situacao)*100:.1f}%)")
print(f"   -> Praticamente todos sem situação são REC. Confirma que filtrar REC resolve.")

# 5. Duplicatas (mesmo veículo, mesmo timestamp)
print(f"\n5. DUPLICATAS")
df_operando = df_dia[df_dia['CODIGOLINHA'] != 'REC'].copy()
dupes = df_operando.duplicated(subset=['COD', 'request_timestamp'], keep=False)
print(f"   Registros operacionais: {len(df_operando)}")
print(f"   Com (COD+timestamp) duplicado: {dupes.sum()}")

# 6. GPS estacionário (posição não muda entre leituras)
print(f"\n6. GPS ESTACIONÁRIO (análise veículo GA181, linha 541)")
df_541 = df_operando[df_operando['CODIGOLINHA'] == '541']
df_v = df_541[df_541['COD'] == 'GA181'].sort_values('request_timestamp').copy()
df_v['prev_lat'] = df_v['LAT'].shift(1)
df_v['prev_lon'] = df_v['LON'].shift(1)
df_v = df_v.dropna(subset=['prev_lat'])
df_v['dist_prev'] = df_v.apply(
    lambda r: haversine(r['LAT'], r['LON'], r['prev_lat'], r['prev_lon']), axis=1
)
estacionario = (df_v['dist_prev'] < 5).sum()
print(f"   Total leituras consecutivas: {len(df_v)}")
print(f"   Sem movimentação (<5m): {estacionario} ({estacionario/len(df_v)*100:.1f}%)")
print(f"   -> AÇÃO: Remover leituras estacionárias consecutivas")

# 7. Intervalo entre leituras
print(f"\n7. INTERVALO ENTRE LEITURAS")
df_v['ts'] = pd.to_datetime(df_v['request_timestamp'])
df_v['ts_prev'] = df_v['ts'].shift(1)
df_v['delta_s'] = (df_v['ts'] - df_v['ts_prev']).dt.total_seconds()
df_v_d = df_v.dropna(subset=['delta_s'])
print(f"   Média: {df_v_d['delta_s'].mean():.0f}s")
print(f"   Mediana: {df_v_d['delta_s'].median():.0f}s")
print(f"   Min: {df_v_d['delta_s'].min():.0f}s, Max: {df_v_d['delta_s'].max():.0f}s")
print(f"   -> Coleta ~a cada 2min. Bom para geofencing.")

# 8. Mudanças de sentido (IDA/VOLTA) - identificar viagens
print(f"\n8. MUDANÇAS DE SENTIDO (viagens do veículo GA181)")
df_v_sent = df_541[df_541['COD'] == 'GA181'].sort_values('request_timestamp')
sentido_changes = (df_v_sent['SENT'] != df_v_sent['SENT'].shift(1))
n_trips = sentido_changes.sum()
print(f"   Mudanças de sentido: {n_trips}")
print(f"   -> ~{n_trips} viagens detectáveis por mudança de sentido")

# Mostrar as viagens
print(f"\n   Viagens detectadas:")
trips = []
current_sent = None
start_ts = None
for _, row in df_v_sent.iterrows():
    if row['SENT'] != current_sent:
        if current_sent is not None:
            trips.append((current_sent, start_ts, row['request_timestamp'], row['TABELA']))
        current_sent = row['SENT']
        start_ts = row['request_timestamp']

for i, (sent, start, end, tab) in enumerate(trips[:20]):
    print(f"   Viagem {i+1}: {sent:>5} | {start[11:19]} -> {end[11:19]} | Tab={tab}")

# 9. Leituras muito longe da rota (outliers GPS)
print(f"\n9. OUTLIERS GPS")
with lzma.open('dados_c3sl/2025_10_24_pontosLinha.json.xz') as f:
    all_pontos = json.loads(f.read())
pontos_541 = [p for p in all_pontos if p['COD'] == '541']
for p in pontos_541:
    p['LAT_NUM'] = float(p['LAT'].replace(',', '.'))
    p['LON_NUM'] = float(p['LON'].replace(',', '.'))

df_541_clean = df_541[df_541['SITUACAO'].notna()].copy()
outlier_count = 0
for _, row in df_541_clean.iterrows():
    min_d = min(haversine(row['LAT'], row['LON'], p['LAT_NUM'], p['LON_NUM']) for p in pontos_541)
    if min_d > 500:
        outlier_count += 1

print(f"   Leituras >500m de qualquer ponto da rota: {outlier_count}/{len(df_541_clean)} ({outlier_count/len(df_541_clean)*100:.1f}%)")
print(f"   -> AÇÃO: Investigar se são trechos entre pontos ou GPS errado")

# 10. Resumo tabela de horários planejados para linha 541
print(f"\n10. TABELA PLANEJADA DA LINHA 541")
with lzma.open('dados_c3sl/2025_10_24_tabelaLinha.json.xz') as f:
    tab_linhas = json.loads(f.read())
tab_541 = [t for t in tab_linhas if t['COD'] == '541']
print(f"   Total entradas: {len(tab_541)}")
for t in tab_541[:15]:
    print(f"   Hora={t['HORA']}, Ponto={t['PONTO']}, Dia={t['DIA']}, Tabela={t['TABELA']}")
