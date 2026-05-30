import lzma
import json

PONTOS_FILE = "dados_c3sl/2025_10_24_pontosLinha.json.xz"
TABELA_FILE = "dados_c3sl/2025_10_24_tabelaLinha.json.xz"

# Ler pontos
with lzma.open(PONTOS_FILE, 'rt', encoding='utf-8') as f:
    pontos_data = json.load(f)

# Ver chaves exclusivas de pontos
# Vamos ver quais são os valores únicos da chave 'COD' nos pontos que representam a linha 541.
# Primeiro, como a linha se chama "SÍTIO CERCADO / B. NOVO A" ou similar, ou talvez o código da linha esteja em algum campo?
# Vamos procurar por registros onde o nome contenha 'Sítio Cercado' ou 'Bairro Novo'
for p in pontos_data[:20]:
    print("KEYS:", list(p.keys()))
    break

# Vamos pesquisar registros onde 'COD' == '541'
cod_541_pontos = [p for p in pontos_data if p.get('COD') == '541']
print(f"Pontos com COD == '541': {len(cod_541_pontos)}")
if cod_541_pontos:
    print("Exemplo de ponto com COD == '541':", cod_541_pontos[0])
    # mostrar todos os sentidos únicos e itinerary_id únicos
    sentidos = set(p.get('SENTIDO') for p in cod_541_pontos)
    itineraries = set(p.get('ITINERARY_ID') for p in cod_541_pontos)
    print("Sentidos únicos:", sentidos)
    print("Itinerary IDs únicos:", itineraries)

print("\n--- Tabela da Linha ---")
with lzma.open(TABELA_FILE, 'rt', encoding='utf-8') as f:
    tabela_data = json.load(f)

cod_541_tabela = [t for t in tabela_data if t.get('COD') == '541']
print(f"Registros de tabela com COD == '541': {len(cod_541_tabela)}")
if cod_541_tabela:
    print("Exemplo tabela:", cod_541_tabela[0])
    pontos_tab = set(t.get('PONTO') for t in cod_541_tabela)
    print(f"Pontos de parada na tabela ({len(pontos_tab)}):", list(pontos_tab)[:10])
