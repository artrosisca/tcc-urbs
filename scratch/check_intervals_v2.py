"""Investigar dias com coleta < 2min - versão corrigida."""
import os
import pandas as pd

DATA_DIR = 'dados_em_tempo_real_2026'

print("=" * 70)
print("INTERVALO REAL DE COLETA POR DIA (baseado em request_timestamp)")
print("=" * 70)

print(f"\n{'Dia':<14} {'Arqs':>5} {'Interv. médio':>16} {'Interv. mín':>16} {'Nota':>20}")
print("-" * 75)

dias_sub2min = []

for day_dir in sorted(os.listdir(DATA_DIR)):
    day_path = os.path.join(DATA_DIR, day_dir)
    if not os.path.isdir(day_path):
        continue
    
    csvs = sorted([f for f in os.listdir(day_path) if f.endswith('.csv')])
    if len(csvs) < 2:
        continue
    
    all_ts = set()
    for f in csvs:
        try:
            df_ts = pd.read_csv(os.path.join(day_path, f), usecols=['request_timestamp'])
            # Remover NaN
            valid = df_ts['request_timestamp'].dropna().unique()
            all_ts.update(str(t) for t in valid if isinstance(t, str) or not pd.isna(t))
        except:
            pass
    
    # Filtrar strings vazias, nan, e valores que não são timestamps reais
    all_ts = {t for t in all_ts if t and t != 'nan' and t.startswith('202')}
    ts_sorted = sorted(all_ts)
    
    if len(ts_sorted) > 1:
        try:
            ts_dt = [pd.Timestamp(t) for t in ts_sorted]
        except:
            continue
        intervals_sec = [(ts_dt[i] - ts_dt[i-1]).total_seconds() for i in range(1, len(ts_dt))]
        # Remover intervalos negativos ou zero
        intervals_sec = [iv for iv in intervals_sec if iv > 0]
        
        if not intervals_sec:
            continue
            
        avg_sec = sum(intervals_sec) / len(intervals_sec)
        min_sec = min(intervals_sec)
        
        nota = ""
        if min_sec < 120:
            nota = f"*** MIN={min_sec:.0f}s!"
            dias_sub2min.append((day_dir, min_sec, avg_sec, len(csvs)))
        
        print(f"{day_dir:<14} {len(csvs):>5} {avg_sec:>10.0f}s ({avg_sec/60:>4.1f}m) {min_sec:>10.0f}s ({min_sec/60:>4.1f}m) {nota:>20}")

# Detalhar os dias com coleta < 2min
if dias_sub2min:
    print(f"\n\n{'=' * 70}")
    print(f"DETALHES DOS DIAS COM COLETA < 2 MINUTOS")
    print(f"{'=' * 70}")
    
    for day_dir, min_sec, avg_sec, n_csvs in dias_sub2min:
        day_path = os.path.join(DATA_DIR, day_dir)
        csvs = sorted([f for f in os.listdir(day_path) if f.endswith('.csv')])
        
        # Carregar todos os timestamps
        all_ts = set()
        for f in csvs:
            try:
                df_ts = pd.read_csv(os.path.join(day_path, f), usecols=['request_timestamp'])
                valid = df_ts['request_timestamp'].dropna()
                all_ts.update(valid.astype(str).unique())
            except:
                pass
        
        all_ts = {t for t in all_ts if t and t != 'nan' and t.startswith('202')}
        ts_sorted = sorted(all_ts)
        try:
            ts_dt = [pd.Timestamp(t) for t in ts_sorted]
        except Exception as e:
            print(f"  Erro ao converter timestamps: {e}")
            continue
        
        print(f"\n--- {day_dir} ---")
        print(f"  Total timestamps únicos: {len(ts_dt)}")
        
        # Encontrar os pares com intervalo < 120s
        sub2 = []
        for i in range(1, len(ts_dt)):
            diff = (ts_dt[i] - ts_dt[i-1]).total_seconds()
            if 0 < diff < 120:
                sub2.append((ts_dt[i-1], ts_dt[i], diff))
        
        print(f"  Intervalos < 2min encontrados: {len(sub2)}")
        
        if sub2:
            print(f"  Exemplos (timestamp_A -> timestamp_B = intervalo):")
            for t1, t2, d in sub2[:20]:
                print(f"    {t1.strftime('%H:%M:%S.%f')[:12]} -> {t2.strftime('%H:%M:%S.%f')[:12]} = {d:.0f}s ({d/60:.1f}min)")
            
            if len(sub2) > 20:
                print(f"    ... e mais {len(sub2) - 20} intervalos")
            
            # Verificar se esses intervalos curtos são contíguos (período de coleta mais rápida)
            print(f"\n  Períodos de coleta rápida:")
            start_fast = sub2[0][0]
            end_fast = sub2[0][1]
            periods = []
            
            for i in range(1, len(sub2)):
                if (sub2[i][0] - end_fast).total_seconds() < 300:  # gap < 5min = mesmo período
                    end_fast = sub2[i][1]
                else:
                    periods.append((start_fast, end_fast))
                    start_fast = sub2[i][0]
                    end_fast = sub2[i][1]
            periods.append((start_fast, end_fast))
            
            for s, e in periods:
                duration = (e - s).total_seconds() / 60
                print(f"    {s.strftime('%H:%M')} - {e.strftime('%H:%M')} ({duration:.0f} min de coleta rápida)")
else:
    print("\n  Nenhum dia com intervalo < 2 minutos encontrado.")
