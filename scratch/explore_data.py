"""Script de exploração dos dados para entender qualidade e precisão GPS."""
import pandas as pd
import lzma
import json
import os
from math import radians, cos, sin, asin, sqrt

# ============================================================
# 1. Carregar dados de uma amostra da linha 541
# ============================================================

# Carregar pontos de parada da linha 541
with lzma.open('dados_c3sl/2025_10_24_pontosLinha.json.xz') as f:
    all_pontos = json.loads(f.read())

pontos_541 = [p for p in all_pontos if p['COD'] == '541']
print(f"=== PONTOS DE PARADA DA LINHA 541 ===")
print(f"Total de pontos: {len(pontos_541)}")

# Converter coordenadas (formato BR usa vírgula)
for p in pontos_541:
    p['LAT_NUM'] = float(p['LAT'].replace(',', '.'))
    p['LON_NUM'] = float(p['LON'].replace(',', '.'))

# Separar por sentido
sentidos = {}
for p in pontos_541:
    s = p['SENTIDO']
    if s not in sentidos:
        sentidos[s] = []
    sentidos[s].append(p)

for s, pts in sentidos.items():
    pts_sorted = sorted(pts, key=lambda x: int(x['SEQ']))
    print(f"\nSentido: {s} ({len(pts)} pontos)")
    for p in pts_sorted:
        print(f"  Seq {p['SEQ']:>3}: ({p['LAT_NUM']:.6f}, {p['LON_NUM']:.6f}) - {p['NOME'][:60]}")

# ============================================================
# 2. Carregar dados GPS da linha 541 em um dia
# ============================================================
print("\n\n=== DADOS GPS DA LINHA 541 - 2025-10-24 ===")

csv_dir = 'dados_em_tempo_real_2026/2025-10-24'
dfs = []
for f in sorted(os.listdir(csv_dir)):
    if f.endswith('.csv'):
        df = pd.read_csv(os.path.join(csv_dir, f))
        dfs.append(df)

df_dia = pd.concat(dfs, ignore_index=True)
print(f"Total registros do dia: {len(df_dia)}")
print(f"Linhas únicas: {df_dia['CODIGOLINHA'].nunique()}")

# Filtrar linha 541
df_541 = df_dia[df_dia['CODIGOLINHA'] == '541'].copy()
# Também tentar como int
if len(df_541) == 0:
    df_541 = df_dia[df_dia['CODIGOLINHA'] == 541].copy()

print(f"\nRegistros da linha 541: {len(df_541)}")
if len(df_541) > 0:
    print(f"Veículos: {df_541['COD'].unique()}")
    print(f"Tabelas: {sorted(df_541['TABELA'].dropna().unique())}")
    print(f"Situações: {df_541['SITUACAO'].value_counts().to_dict()}")
    print(f"Sentidos: {df_541['SENT'].value_counts().to_dict()}")
    
    # Verificar precisão GPS - calcular distância entre leituras consecutivas
    # Para um veículo específico
    veiculos = df_541['COD'].unique()
    v = veiculos[0]
    df_v = df_541[df_541['COD'] == v].copy()
    df_v = df_v.sort_values('request_timestamp')
    
    print(f"\n--- Veículo {v} ---")
    print(f"  Total leituras: {len(df_v)}")
    print(f"  Primeira: {df_v['request_timestamp'].iloc[0]}")
    print(f"  Última: {df_v['request_timestamp'].iloc[-1]}")
    print(f"  Timestamps únicos: {df_v['request_timestamp'].nunique()}")
    
    # Mostrar primeiras leituras
    print(f"\n  Primeiras leituras:")
    for _, row in df_v.head(20).iterrows():
        print(f"    {row['request_timestamp']} | Lat={row['LAT']:.6f}, Lon={row['LON']:.6f} | {row['SITUACAO']} | {row['SENT']} | Tab={row['TABELA']}")

# ============================================================
# 3. Análise de precisão GPS - distância entre pontos GPS e pontos de parada
# ============================================================
print("\n\n=== ANÁLISE DE PRECISÃO GPS ===")

def haversine(lat1, lon1, lat2, lon2):
    """Distância em metros entre dois pontos GPS."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371000 * c  # metros

if len(df_541) > 0:
    # Para cada leitura GPS, encontrar o ponto de parada mais próximo
    min_dists = []
    sample = df_541.sample(min(500, len(df_541)), random_state=42)
    
    for _, row in sample.iterrows():
        lat_gps = row['LAT']
        lon_gps = row['LON']
        
        dists = []
        for p in pontos_541:
            d = haversine(lat_gps, lon_gps, p['LAT_NUM'], p['LON_NUM'])
            dists.append(d)
        
        min_dists.append(min(dists))
    
    print(f"Distância mínima do GPS ao ponto de parada mais próximo:")
    print(f"  Média: {sum(min_dists)/len(min_dists):.1f} m")
    print(f"  Mediana: {sorted(min_dists)[len(min_dists)//2]:.1f} m")
    print(f"  Mínimo: {min(min_dists):.1f} m")
    print(f"  Máximo: {max(min_dists):.1f} m")
    
    # Distribuição por faixas
    faixas = [0, 50, 100, 200, 500, 1000, float('inf')]
    for i in range(len(faixas)-1):
        count = sum(1 for d in min_dists if faixas[i] <= d < faixas[i+1])
        pct = count / len(min_dists) * 100
        lbl = f"{faixas[i]}-{faixas[i+1] if faixas[i+1] != float('inf') else 'inf'}m"
        print(f"  {lbl:>12}: {count:>4} ({pct:.1f}%)")

# ============================================================
# 4. Verificar frequência de coleta e duplicatas
# ============================================================
print("\n\n=== FREQUÊNCIA DE COLETA ===")
print(f"Total registros do dia: {len(df_dia)}")
print(f"Timestamps únicos: {df_dia['request_timestamp'].nunique()}")
print(f"Registros com CODIGOLINHA='REC': {len(df_dia[df_dia['CODIGOLINHA'] == 'REC'])}")
print(f"Registros com SITUACAO nula: {df_dia['SITUACAO'].isna().sum()}")

# Verificar coluna CODIGOLINHA - valores não numéricos
non_numeric = df_dia[~df_dia['CODIGOLINHA'].astype(str).str.match(r'^\d+$')]
print(f"Registros com CODIGOLINHA não numérico: {len(non_numeric)}")
if len(non_numeric) > 0:
    print(f"  Valores: {non_numeric['CODIGOLINHA'].unique()[:10]}")

print("\n=== CATEGORIAS DE LINHAS ===")
with lzma.open('dados_c3sl/2025_10_24_linhas.json.xz') as f:
    linhas = json.loads(f.read())

categorias = {}
for l in linhas:
    cat = l['CATEGORIA_SERVICO']
    if cat not in categorias:
        categorias[cat] = 0
    categorias[cat] += 1

for cat, count in sorted(categorias.items(), key=lambda x: -x[1]):
    print(f"  {cat}: {count} linhas")
