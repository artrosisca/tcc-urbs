import lzma
import json

SHAPE_FILE = "dados_c3sl/2025_10_24_shapeLinha.json.xz"

with lzma.open(SHAPE_FILE, 'rt', encoding='utf-8') as f:
    shape_data = json.load(f)

print("Total registros de shape:", len(shape_data))
if isinstance(shape_data, list):
    print("KEYS:", list(shape_data[0].keys()))
    # Filtrar para 541
    shape_541 = [s for s in shape_data if s.get('COD') == '541']
    print("Total registros de shape para 541:", len(shape_541))
    if shape_541:
        print("Exemplo de shape 541:", shape_541[0])
