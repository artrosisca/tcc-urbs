import lzma
import json
import pandas as pd

SHAPE_FILE = "dados_c3sl/2025_10_24_shapeLinha.json.xz"

with lzma.open(SHAPE_FILE, 'rt', encoding='utf-8') as f:
    shape_data = json.load(f)

df = pd.DataFrame([s for s in shape_data if s.get('COD') == '541'])
print("Unique SHP values for 541:", df['SHP'].unique())
for shp in df['SHP'].unique():
    subset = df[df['SHP'] == shp]
    print(f"Shape {shp}: {len(subset)} points")
    print(subset.head(3))
