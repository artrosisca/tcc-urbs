import lzma
import json
import pandas as pd

PONTOS_FILE = "dados_c3sl/2025_10_24_pontosLinha.json.xz"

with lzma.open(PONTOS_FILE, 'rt', encoding='utf-8') as f:
    pontos_data = json.load(f)

df = pd.DataFrame([p for p in pontos_data if p.get('COD') == '541'])
# Converter SEQ para int para ordenar
df['SEQ'] = df['SEQ'].astype(int)

print("Sentidos encontrados:", df['SENTIDO'].unique())

for sent in df['SENTIDO'].unique():
    subset = df[df['SENTIDO'] == sent].sort_values(by='SEQ')
    print(f"\nSentido: {sent} ({len(subset)} pontos)")
    print(subset[['SEQ', 'NUM', 'NOME', 'LAT', 'LON']].to_string(index=False))
