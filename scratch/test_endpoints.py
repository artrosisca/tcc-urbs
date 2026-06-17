import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import pandas as pd
    import pm4py
    from src.visualization.dashboard import get_discovery, get_performance
    
    print("Testando /api/discovery...")
    res_disc = get_discovery("541", "2025-12-02", "2025-12-08", "VOLTA")
    print("Discovery ok!", type(res_disc))
    
    print("\nTestando /api/performance...")
    res_perf = get_performance("541", "2025-12-02", "2025-12-08", "VOLTA")
    print("Performance ok!", type(res_perf))
    
except Exception as e:
    import traceback
    print("ERRO ENCONTRADO:")
    traceback.print_exc()
