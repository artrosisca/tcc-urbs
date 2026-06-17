import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.etl.load_realtime import load_realtime_data

df = load_realtime_data("541", "2025-10-24", "2025-10-24")
if not df.empty:
    print("Colunas:", df.columns)
    print("\nExemplo de dados:")
    print(df[['COD', 'request_timestamp', 'REFRESH', 'LAT', 'LON']].head(10))
