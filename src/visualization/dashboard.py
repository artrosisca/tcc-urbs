import os
import sys
import queue
import threading
import io

# Adicionar a raiz do projeto ao sys.path para resolver as importações do pacote 'src'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi import FastAPI, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import pandas as pd
import numpy as np
from src.etl.load_c3sl import load_static_data
from src.etl.trajectory import TrajectoryReconstructor
from src.etl.repository import default_telemetry_repo, FilesystemTelemetryAdapter, _fix_encoding
from src.mining.engine import ProcessMiningEngine

app = FastAPI(title="Process Mining URBS — CCO API")

@app.middleware("http")
async def add_no_cache_headers(request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static") or request.url.path == "/":
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# Wrapper de stdout thread-safe para redirecionar saídas do pipeline para a fila do SSE
class SSEStdoutRedirector:
    def __init__(self, q):
        self.q = q
        self.buffer = []
        
    def write(self, s):
        if s == '\n':
            if self.buffer:
                line = "".join(self.buffer)
                self.q.put(line)
                self.buffer = []
        elif '\n' in s:
            parts = s.split('\n')
            for part in parts[:-1]:
                self.buffer.append(part)
                line = "".join(self.buffer)
                self.q.put(line)
                self.buffer = []
            if parts[-1]:
                self.buffer.append(parts[-1])
        else:
            self.buffer.append(s)
            
    def flush(self):
        if self.buffer:
            line = "".join(self.buffer)
            self.q.put(line)
            self.buffer = []

def get_common_lines(data_dir="data/dados_em_tempo_real_2026"):
    if data_dir == "data/dados_em_tempo_real_2026":
        return default_telemetry_repo.list_available_lines()
    adapter = FilesystemTelemetryAdapter(base_data_dir=os.path.dirname(data_dir) or "data")
    adapter.realtime_dir = data_dir
    adapter.processed_dir = data_dir
    return adapter.list_available_lines()

# Helper to filter DataFrame by start_hour and end_hour query params
def filter_df_by_hours(df: pd.DataFrame, start_hour: str = None, end_hour: str = None) -> pd.DataFrame:
    if df.empty:
        return df
    
    # Garantir datetime e sanitizar encoding de nomes de paradas
    df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
    if 'concept:name' in df.columns:
        df['concept:name'] = df['concept:name'].apply(_fix_encoding)
    
    if start_hour and end_hour:
        try:
            if end_hour.startswith("24:00") or end_hour == "24:00":
                end_hour = "23:59:59"
            
            sh_split = start_hour.split(":")
            eh_split = end_hour.split(":")
            
            from datetime import time
            start_t = time(int(sh_split[0]), int(sh_split[1]) if len(sh_split) > 1 else 0)
            end_t = time(
                int(eh_split[0]), 
                int(eh_split[1]) if len(eh_split) > 1 else 0, 
                int(eh_split[2]) if len(eh_split) > 2 else 0
            )
            
            times = df['time:timestamp'].dt.time
            df = df[(times >= start_t) & (times <= end_t)]
        except Exception as e:
            print(f"Erro ao filtrar faixas de horário ({start_hour} - {end_hour}): {str(e)}")
            
    return df

# 1. Rota de Linhas em Comum
@app.get("/api/lines")
def read_lines(regime: str = None):
    try:
        return {"lines": default_telemetry_repo.list_available_lines(regime=regime)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint de Streaming de Logs (SSE) do pipeline
@app.get("/api/process-stream")
def process_stream(line: str, start_date: str, end_date: str):
    q = queue.Queue()
    
    def run_pipeline():
        old_stdout = sys.stdout
        sys.stdout = SSEStdoutRedirector(q)
        try:
            print(f"Iniciando pipeline de processamento para Linha: {line}...")
            print(f"Período: {start_date} até {end_date}")
            
            from src.etl.build_event_log import build_event_log
            
            # Executa o pipeline de dados
            df_log = build_event_log(line, start_date, end_date, output_dir="data/dados_processados")
            # Força o carregamento dos metadados estáticos para garantir consistência
            _ = load_static_data(start_date, line)
            
            if df_log.empty:
                print("ERRO: Nenhum registro de GPS válido localizado para estes filtros.")
                q.put("__FAILURE__")
            else:
                print("Pipeline finalizado: Log de Eventos consolidado e salvo com sucesso!")
                q.put("__SUCCESS__")
        except Exception as e:
            print(f"ERRO CRÍTICO no processamento: {str(e)}")
            q.put("__FAILURE__")
        finally:
            sys.stdout.flush()
            sys.stdout = old_stdout
            q.put(None)  # Envia marcador de encerramento da conexão
            
    threading.Thread(target=run_pipeline).start()
    
    def event_generator():
        while True:
            msg = q.get()
            if msg is None:
                break
            yield f"data: {msg}\n\n"
    return StreamingResponse(event_generator(), media_type="text/event-stream")

def check_raw_gps_data(line_code: str, start_date: str, end_date: str, start_hour: str = None, end_hour: str = None, data_dir="data/dados_em_tempo_real_2026") -> int:
    if data_dir == "data/dados_em_tempo_real_2026":
        res = default_telemetry_repo.check_telemetry_status(line_code, start_date, end_date, start_hour, end_hour)
        return res.get("count", 0) if res.get("status") == "raw" else 0
    adapter = FilesystemTelemetryAdapter(base_data_dir=os.path.dirname(data_dir) or "data")
    adapter.realtime_dir = data_dir
    res = adapter.check_telemetry_status(line_code, start_date, end_date, start_hour, end_hour)
    return res.get("count", 0) if res.get("status") == "raw" else 0

# 2.1. Endpoint para verificar quantidade de viagens disponíveis antes de processar
@app.get("/api/check-trips")
def check_trips(line: str, start_date: str, end_date: str, start_hour: str = None, end_hour: str = None):
    try:
        return default_telemetry_repo.check_telemetry_status(line, start_date, end_date, start_hour, end_hour)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 3. Endpoint de Dados Geográficos do Mapa e Métricas Gerais (Com Filtro de Horário On-the-Fly)
@app.get("/api/map-data")
def get_map_data(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    if direction not in ["IDA", "VOLTA"]:
        return {"stops": [], "shape": [], "segments": [], "replay_trips": [], "metrics": {}}
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        static_data = load_static_data(start_date, line)
        
        stops_df = static_data.get('pontos', pd.DataFrame())
        if stops_df.empty:
            return {"stops": [], "shape": [], "segments": [], "replay_trips": [], "metrics": {}}
            
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        df_log_dir = df_log[df_log['gps_direction'] == direction]
        
        sentido_static, stops_filtered, shape_filtered = TrajectoryReconstructor.resolve_route_geometry(
            static_data,
            direction=direction,
            trip_sample_df=df_log_dir
        )
        
        shape_coords = []
        if not shape_filtered.empty:
            shape_coords = list(zip(shape_filtered['LAT'].tolist(), shape_filtered['LON'].tolist()))
            
        segments = TrajectoryReconstructor.calculate_segment_speeds(df_log_dir, shape_filtered, stops_filtered)
        replay_trips = TrajectoryReconstructor.build_replay_trips(df_log_dir, stops_filtered)
        
        stops_list = []
        for idx, stop in stops_filtered.iterrows():
            stop_name_log = f"PASSAGEM_{stop['NOME']}"
            df_stop_events = df_log_dir[df_log_dir['concept:name'] == stop_name_log]
            passages = len(df_stop_events)
            is_interpolated = False
            if not df_stop_events.empty and 'interpolated' in df_stop_events.columns:
                is_interpolated = bool(df_stop_events['interpolated'].iloc[0])
                
            stops_list.append({
                "seq": int(stop['SEQ']),
                "nome": str(stop['NOME']),
                "num": str(stop.get('NUM', stop['SEQ'])),
                "lat": float(stop['LAT']),
                "lon": float(stop['LON']),
                "passages": passages,
                "interpolated": is_interpolated
            })
            
        total_viagens = int(df_log_dir['case:concept:name'].nunique())
        total_eventos = int(len(df_log_dir))
        veiculos_ativos = int(df_log_dir['org:resource'].nunique()) if 'org:resource' in df_log_dir.columns else 0
        taxa_interpolacao = float((df_log_dir['interpolated'].sum() / len(df_log_dir)) * 100) if (len(df_log_dir) > 0 and 'interpolated' in df_log_dir.columns) else 0.0
        
        return {
            "stops": stops_list,
            "shape": shape_coords,
            "segments": segments,
            "replay_trips": replay_trips,
            "metrics": {
                "total_viagens": total_viagens,
                "total_eventos": total_eventos,
                "veiculos_ativos": veiculos_ativos,
                "taxa_interpolacao": taxa_interpolacao
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Endpoint de Descoberta de Processos (/api/discovery) -> Retorna SVG da Rede de Petri
@app.get("/api/discovery")
def get_discovery(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        df_log_dir = df_log[df_log['gps_direction'] == direction]
        
        if df_log_dir.empty:
            raise HTTPException(status_code=404, detail="Nenhum evento encontrado para este sentido.")
            
        svg_data = ProcessMiningEngine.discover_petri_net(df_log_dir, as_svg=True)
        return Response(content=svg_data, media_type="image/svg+xml")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 5. Endpoint de Conformidade (/api/conformance) -> Retorna trace fitness e paradas puladas em JSON
@app.get("/api/conformance")
def get_conformance(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        static_data = load_static_data(start_date, line)
        return ProcessMiningEngine.evaluate_conformance(df_log, static_data['pontos'], direction=direction)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Endpoint de Desempenho (/api/performance) -> Retorna SVG do Performance DFG (travel times)
@app.get("/api/performance")
def get_performance(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        df_log_dir = df_log[df_log['gps_direction'] == direction]
        
        if df_log_dir.empty:
            raise HTTPException(status_code=404, detail="Nenhum evento encontrado para este sentido.")
            
        svg_data = ProcessMiningEngine.analyze_performance(df_log_dir, as_svg=True)
        return Response(content=svg_data, media_type="image/svg+xml")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6.5. Endpoint de Descoberta de Processos em JSON (/api/discovery-json)
@app.get("/api/discovery-json")
def get_discovery_json(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        df_log_dir = df_log[df_log['gps_direction'] == direction]
        
        if df_log_dir.empty:
            raise HTTPException(status_code=404, detail="Nenhum evento encontrado para este sentido.")
            
        return ProcessMiningEngine.discover_petri_net(df_log_dir, as_svg=False)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6.6. Endpoint de Desempenho em JSON (/api/performance-json)
@app.get("/api/performance-json")
def get_performance_json(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        df_log_dir = df_log[df_log['gps_direction'] == direction]
        
        if df_log_dir.empty:
            raise HTTPException(status_code=404, detail="Nenhum evento encontrado para este sentido.")
            
        return ProcessMiningEngine.analyze_performance(df_log_dir, as_svg=False)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 7. Configuração e montagem dos arquivos estáticos do front-end
static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return Response(content="Front-end index.html não localizado. Crie o arquivo na pasta 'static'.", status_code=404)
