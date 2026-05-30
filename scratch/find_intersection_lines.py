import os
import pandas as pd

# Ler todas as linhas de um dia no Regime A (2025-10-24)
dir_a = 'dados_em_tempo_real_2026/2025-10-24'
lines_a = set()
for f in os.listdir(dir_a):
    if f.endswith('.csv'):
        try:
            df = pd.read_csv(os.path.join(dir_a, f), usecols=['CODIGOLINHA'])
            lines_a.update(df['CODIGOLINHA'].dropna().astype(str).unique())
        except:
            pass

# Ler todas as linhas de um dia no Regime B (2025-12-02)
dir_b = 'dados_em_tempo_real_2026/2025-12-02'
lines_b = set()
for f in os.listdir(dir_b):
    if f.endswith('.csv'):
        try:
            df = pd.read_csv(os.path.join(dir_b, f), usecols=['CODIGOLINHA'])
            lines_b.update(df['CODIGOLINHA'].dropna().astype(str).unique())
        except:
            pass

# Interseção e remover REC e linhas X**
intersection = lines_a.intersection(lines_b)
intersection = {l for l in intersection if l != 'REC' and not l.startswith('X')}

print("Total de linhas em comum:", len(intersection))
print("Exemplos de linhas em comum (ordenadas):", sorted(list(intersection))[:30])
