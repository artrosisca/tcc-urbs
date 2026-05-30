import lzma
import json
import pandas as pd

TABELA_FILE = "dados_c3sl/2025_10_24_tabelaLinha.json.xz"

with lzma.open(TABELA_FILE, 'rt', encoding='utf-8') as f:
    tabela_data = json.load(f)

df = pd.DataFrame([t for t in tabela_data if t.get('COD') == '541'])
print("Colunas da Tabela:")
print(df.columns)
print("\nTipos de dia (DIA):", df['DIA'].unique())
print("Pontos de controle (PONTO):", df['PONTO'].unique())
print("Tabelas (veículos programados):", sorted(df['TABELA'].unique()))
print("\nExemplo para DIA=1 (Útil) e TABELA=1:")
print(df[(df['DIA'] == '1') & (df['TABELA'] == '1')].sort_values(by='HORA'))
