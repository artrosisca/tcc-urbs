import lzma
import json
import pandas as pd

PONTOS_FILE = "dados_c3sl/2025_10_24_pontosLinha.json.xz"
TABELA_FILE = "dados_c3sl/2025_10_24_tabelaLinha.json.xz"
LINHAS_FILE = "dados_c3sl/2025_10_24_linhas.json.xz"

print("--- Lendo Linhas ---")
with lzma.open(LINHAS_FILE, 'rt', encoding='utf-8') as f:
    linhas_data = json.load(f)
    print("Total de registros:", len(linhas_data))
    print("Exemplo de registro:", list(linhas_data.items())[:3] if isinstance(linhas_data, dict) else linhas_data[:3])

print("\n--- Lendo Pontos da Linha ---")
with lzma.open(PONTOS_FILE, 'rt', encoding='utf-8') as f:
    pontos_data = json.load(f)
    print("Total de registros:", len(pontos_data))
    # Se for lista, mostra os primeiros
    if isinstance(pontos_data, list):
        print("Exemplo 1:", pontos_data[0])
        # Filtrar por linha 541
        line_541 = [p for p in pontos_data if p.get('COD') == '541' or p.get('CODIGOLINHA') == '541' or '541' in str(p.values())]
        print(f"Total pontos para 541: {len(line_541)}")
        if line_541:
            print("Exemplo ponto 541:", line_541[0])
    elif isinstance(pontos_data, dict):
        print("Keys:", list(pontos_data.keys())[:5])
        # ver se 541 está nas chaves
        if '541' in pontos_data:
            print("Ponto 541:", pontos_data['541'][:2])

print("\n--- Lendo Tabela da Linha ---")
with lzma.open(TABELA_FILE, 'rt', encoding='utf-8') as f:
    tabela_data = json.load(f)
    print("Total de registros:", len(tabela_data))
    if isinstance(tabela_data, list):
        print("Exemplo 1:", tabela_data[0])
        line_541_t = [t for t in tabela_data if t.get('COD') == '541' or t.get('CODIGOLINHA') == '541' or '541' in str(t.values())]
        print(f"Total tabela para 541: {len(line_541_t)}")
        if line_541_t:
            print("Exemplo tabela 541:", line_541_t[0])
    elif isinstance(tabela_data, dict):
        print("Keys:", list(tabela_data.keys())[:5])
        if '541' in tabela_data:
            print("Tabela 541:", tabela_data['541'][:2])
