"""Investigar quais dados têm coleta com intervalo menor que 2 minutos."""
import os
import pandas as pd
from collections import defaultdict

DATA_DIR = 'dados_em_tempo_real_2026'

# 1. Verificar a granularidade dos arquivos CSV por dia
print("=" * 70)
print("ANÁLISE DE GRANULARIDADE DE COLETA POR DIA")
print("=" * 70)

results = []

for day_dir in sorted(os.listdir(DATA_DIR)):
    day_path = os.path.join(DATA_DIR, day_dir)
    if not os.path.isdir(day_path):
        continue
    
    csvs = sorted([f for f in os.listdir(day_path) if f.endswith('.csv')])
    
    if len(csvs) == 0:
        continue
    
    # Extrair timestamps dos nomes dos arquivos
    file_times = []
    for f in csvs:
        # formato: 2025-10-24_06-00.csv ou 2025-10-24_06-30.csv etc
        parts = f.replace('.csv', '').split('_')
        if len(parts) >= 2:
            time_part = parts[-1]  # "06-00" or "06-30"
            hour_min = time_part.split('-')
            if len(hour_min) == 2:
                file_times.append(f"{hour_min[0]}:{hour_min[1]}")
    
    # Calcular intervalos entre arquivos
    if len(file_times) > 1:
        intervals = []
        for i in range(1, len(file_times)):
            h1, m1 = map(int, file_times[i-1].split(':'))
            h2, m2 = map(int, file_times[i].split(':'))
            diff_min = (h2 * 60 + m2) - (h1 * 60 + m1)
            if diff_min < 0:
                diff_min += 24 * 60
            intervals.append(diff_min)
        
        min_interval = min(intervals)
        max_interval = max(intervals)
        avg_interval = sum(intervals) / len(intervals)
        
        results.append({
            'dia': day_dir,
            'n_arquivos': len(csvs),
            'min_intervalo_min': min_interval,
            'max_intervalo_min': max_interval,
            'avg_intervalo_min': round(avg_interval, 1),
            'primeiro': file_times[0],
            'ultimo': file_times[-1],
        })

# Separar dias com coleta != 60min
print("\n--- DIAS COM COLETA DIFERENTE DE 1 HORA ---\n")
print(f"{'Dia':<14} {'Arqs':>5} {'Min(min)':>9} {'Avg(min)':>9} {'Max(min)':>9} {'Período':>15}")
print("-" * 70)

dias_especiais = []
for r in results:
    if r['min_intervalo_min'] != 60 or r['max_intervalo_min'] != 60:
        dias_especiais.append(r)
        print(f"{r['dia']:<14} {r['n_arquivos']:>5} {r['min_intervalo_min']:>9} {r['avg_intervalo_min']:>9} {r['max_intervalo_min']:>9} {r['primeiro']+'-'+r['ultimo']:>15}")

if not dias_especiais:
    print("  (Nenhum dia com intervalo diferente de 60min entre arquivos)")

print(f"\n--- DIAS COM COLETA PADRÃO (1 HORA) ---\n")
print(f"Total: {len(results) - len(dias_especiais)} dias")

# 2. Agora verificar dentro dos CSVs - o request_timestamp
print("\n\n" + "=" * 70)
print("ANÁLISE DE INTERVALO ENTRE request_timestamp DENTRO DOS CSVs")
print("=" * 70)

# Verificar um dia normal e comparar com dias especiais
dias_para_analisar = [results[0]['dia']]  # primeiro dia como baseline
for r in dias_especiais[:5]:
    if r['dia'] not in dias_para_analisar:
        dias_para_analisar.append(r['dia'])

for day in dias_para_analisar:
    day_path = os.path.join(DATA_DIR, day)
    csvs = sorted([f for f in os.listdir(day_path) if f.endswith('.csv')])
    
    # Carregar todos os CSVs do dia
    all_timestamps = set()
    for f in csvs[:5]:  # primeiros 5 arquivos para amostra
        df = pd.read_csv(os.path.join(day_path, f))
        all_timestamps.update(df['request_timestamp'].unique())
    
    ts_sorted = sorted(all_timestamps)
    
    print(f"\n--- {day} ({len(csvs)} arquivos) ---")
    print(f"  Timestamps únicos (amostra): {len(ts_sorted)}")
    
    if len(ts_sorted) > 1:
        # Calcular intervalos entre timestamps
        ts_dt = [pd.Timestamp(t) for t in ts_sorted]
        intervals_sec = [(ts_dt[i] - ts_dt[i-1]).total_seconds() for i in range(1, len(ts_dt))]
        
        print(f"  Intervalo mínimo: {min(intervals_sec):.0f}s ({min(intervals_sec)/60:.1f}min)")
        print(f"  Intervalo médio: {sum(intervals_sec)/len(intervals_sec):.0f}s ({sum(intervals_sec)/len(intervals_sec)/60:.1f}min)")
        print(f"  Intervalo máximo: {max(intervals_sec):.0f}s ({max(intervals_sec)/60:.1f}min)")
        
        # Distribuição de intervalos
        buckets = defaultdict(int)
        for iv in intervals_sec:
            if iv < 60:
                buckets['<1min'] += 1
            elif iv < 120:
                buckets['1-2min'] += 1
            elif iv < 180:
                buckets['2-3min'] += 1
            elif iv < 300:
                buckets['3-5min'] += 1
            else:
                buckets['>5min'] += 1
        
        print(f"  Distribuição de intervalos:")
        for k in ['<1min', '1-2min', '2-3min', '3-5min', '>5min']:
            if k in buckets:
                print(f"    {k:>8}: {buckets[k]}")
        
        # Mostrar primeiros timestamps
        print(f"  Primeiros timestamps:")
        for t in ts_sorted[:10]:
            print(f"    {t}")

# 3. Verificar TODOS os dias - intervalo real entre timestamps
print("\n\n" + "=" * 70)
print("RESUMO: INTERVALO REAL DE COLETA POR DIA (baseado em request_timestamp)")
print("=" * 70)

print(f"\n{'Dia':<14} {'Arqs':>5} {'Intervalo médio':>18} {'Intervalo mín':>18}")
print("-" * 60)

for day_dir in sorted(os.listdir(DATA_DIR)):
    day_path = os.path.join(DATA_DIR, day_dir)
    if not os.path.isdir(day_path):
        continue
    
    csvs = sorted([f for f in os.listdir(day_path) if f.endswith('.csv')])
    if len(csvs) < 2:
        continue
    
    # Coletar timestamps únicos de TODOS os CSVs (apenas a coluna timestamp para economizar)
    all_ts = set()
    for f in csvs:
        try:
            df_ts = pd.read_csv(os.path.join(day_path, f), usecols=['request_timestamp'])
            all_ts.update(df_ts['request_timestamp'].unique())
        except:
            pass
    
    ts_sorted = sorted(all_ts)
    if len(ts_sorted) > 1:
        ts_dt = [pd.Timestamp(t) for t in ts_sorted]
        intervals_sec = [(ts_dt[i] - ts_dt[i-1]).total_seconds() for i in range(1, len(ts_dt))]
        avg_sec = sum(intervals_sec) / len(intervals_sec)
        min_sec = min(intervals_sec)
        
        marker = ""
        if avg_sec < 110:  # menos de ~2min
            marker = " ⭐ COLETA MAIS FREQUENTE!"
        
        print(f"{day_dir:<14} {len(csvs):>5} {avg_sec:>12.0f}s ({avg_sec/60:>4.1f}min) {min_sec:>12.0f}s ({min_sec/60:>4.1f}min){marker}")
