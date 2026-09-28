import time
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
import glob
from typing import Optional
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
def read_lines(regime: str = None, include_raw: bool = False):
    try:
        mined_lines = default_telemetry_repo.list_available_lines(regime=regime)
        raw_lines = default_telemetry_repo.list_raw_lines(regime=regime)
        other_raw = [l for l in raw_lines if l not in mined_lines]
        lines_output = list(mined_lines) + other_raw if include_raw else mined_lines
        return {
            "mined_lines": mined_lines,
            "raw_lines": other_raw,
            "lines": lines_output,
            "total_mined": len(mined_lines),
            "total_raw": len(raw_lines)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 2. Endpoint de Streaming de Logs (SSE) do pipeline
@app.get("/api/process-stream")
def process_stream(line: str, start_date: str, end_date: str):
    q = queue.Queue()
    
    def run_pipeline():
        global _dashboard_cache
        _dashboard_cache.clear()
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
                csv_path = find_event_log_file(line, start_date, end_date)
                if csv_path and os.path.exists(csv_path):
                    print(f"Log de Eventos consolidado pré-existente localizado: {os.path.basename(csv_path)}")
                    print("Os dados minerados já estão prontos para análise no CCO!")
                    q.put("__SUCCESS__")
                else:
                    print("ERRO: Nenhum registro de GPS bruto ou log processado encontrado para estes filtros.")
                    q.put("__FAILURE__")
            else:
                print("Pipeline finalizado: Log de Eventos consolidado e salvo com sucesso!")
                _fleet_audit_cache.clear()
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

def find_event_log_file(line: str, start_date: str, end_date: str) -> Optional[str]:
    # Exact match first
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if os.path.exists(csv_path):
        return csv_path
    # Match line with start_date
    candidates = sorted(glob.glob(f"data/dados_processados/event_log_{line}_{start_date}_*.csv"))
    if candidates:
        return candidates[-1]
    # Fallback to any file for this line
    candidates = sorted(glob.glob(f"data/dados_processados/event_log_{line}_*.csv"))
    if candidates:
        return candidates[-1]
    return None

def resolve_direction_subset(df_log: pd.DataFrame, direction: str):
    available_dirs = [str(d) for d in df_log['gps_direction'].dropna().unique()] if 'gps_direction' in df_log.columns else []
    if direction in available_dirs:
        return direction, df_log[df_log['gps_direction'] == direction]
    if available_dirs:
        chosen = available_dirs[0]
        return chosen, df_log[df_log['gps_direction'] == chosen]
    return direction, df_log

# 3. Endpoint de Dados Geográficos do Mapa e Métricas Gerais (Com Filtro de Horário On-the-Fly)
@app.get("/api/map-data")
def get_map_data(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    regime = "A" if "2025-10" in start_date else "B"
    if direction not in ["IDA", "VOLTA", "CIRCULAR"]:
        return {
            "stops": [],
            "shape": [],
            "segments": [],
            "replay_trips": [],
            "metrics": {},
            "metadata": {
                "line": line,
                "direction": direction,
                "start_date": start_date,
                "end_date": end_date,
                "regime": regime
            }
        }
    csv_path = find_event_log_file(line, start_date, end_date)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        static_data = load_static_data(start_date, line)
        
        stops_df = static_data.get('pontos', pd.DataFrame())
        if stops_df.empty:
            return {
                "stops": [],
                "shape": [],
                "segments": [],
                "replay_trips": [],
                "metrics": {},
                "metadata": {
                    "line": line,
                    "direction": direction,
                    "start_date": start_date,
                    "end_date": end_date,
                    "regime": regime
                }
            }
            
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        chosen_dir, df_log_dir = resolve_direction_subset(df_log, direction)
        
        sentido_static, stops_filtered, shape_filtered = TrajectoryReconstructor.resolve_route_geometry(
            static_data,
            direction=chosen_dir,
            trip_sample_df=df_log_dir
        )
        
        shape_coords = []
        if not shape_filtered.empty:
            shape_coords = list(zip(shape_filtered['LAT'].tolist(), shape_filtered['LON'].tolist()))
            
        segments = TrajectoryReconstructor.calculate_segment_speeds(df_log_dir, shape_filtered, stops_filtered)
        replay_trips = TrajectoryReconstructor.build_replay_trips(df_log_dir, stops_filtered, shape_filtered)
        
        stops_list = []
        for idx, stop in stops_filtered.iterrows():
            if 'stop_seq' in df_log_dir.columns:
                df_stop_events = df_log_dir[df_log_dir['stop_seq'] == int(stop['SEQ'])]
            else:
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
        
        min_time_sec = 0
        max_time_sec = 86400
        if not df_log_raw.empty and 'time:timestamp' in df_log_raw.columns:
            # Pegar o range real de dados na linha filtrada
            times = pd.to_datetime(df_log_dir['time:timestamp'], errors='coerce')
            if not times.empty:
                min_time_sec = int(times.dt.hour.min() * 3600 + times.dt.minute.min() * 60)
                max_time_sec = int(times.dt.hour.max() * 3600 + times.dt.minute.max() * 60 + 59)

        return {
            "time_range": [min_time_sec, max_time_sec],
            "stops": stops_list,
            "shape": shape_coords,
            "segments": segments,
            "replay_trips": replay_trips,
            "metrics": {
                "total_viagens": total_viagens,
                "total_eventos": total_eventos,
                "veiculos_ativos": veiculos_ativos,
                "taxa_interpolacao": taxa_interpolacao
            },
            "metadata": {
                "line": line,
                "direction": chosen_dir,
                "start_date": start_date,
                "end_date": end_date,
                "regime": regime
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Endpoint de Descoberta de Processos (/api/discovery) -> Retorna SVG da Rede de Petri
@app.get("/api/discovery")
def get_discovery(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = find_event_log_file(line, start_date, end_date)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        chosen_dir, df_log_dir = resolve_direction_subset(df_log, direction)
        
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
    csv_path = find_event_log_file(line, start_date, end_date)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        chosen_dir, _ = resolve_direction_subset(df_log, direction)
        static_data = load_static_data(start_date, line)
        return ProcessMiningEngine.evaluate_conformance(df_log, static_data['pontos'], direction=chosen_dir)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6. Endpoint de Desempenho (/api/performance) -> Retorna SVG do Performance DFG (travel times)
@app.get("/api/performance")
def get_performance(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    csv_path = find_event_log_file(line, start_date, end_date)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        chosen_dir, df_log_dir = resolve_direction_subset(df_log, direction)
        
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
    csv_path = find_event_log_file(line, start_date, end_date)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        chosen_dir, df_log_dir = resolve_direction_subset(df_log, direction)
        
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
    csv_path = find_event_log_file(line, start_date, end_date)
    if not csv_path or not os.path.exists(csv_path):
        raise HTTPException(status_code=400, detail="Log de eventos não processado. Por favor, execute a mineração primeiro.")
        
    try:
        df_log_raw = pd.read_csv(csv_path)
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        chosen_dir, df_log_dir = resolve_direction_subset(df_log, direction)
        
        if df_log_dir.empty:
            raise HTTPException(status_code=404, detail="Nenhum evento encontrado para este sentido.")
            
        return ProcessMiningEngine.analyze_performance(df_log_dir, as_svg=False)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 6.7. Endpoint de Auditoria Diária da Frota (Visão Executiva CCO)
_fleet_audit_cache: Dict[str, Dict[str, Any]] = {}


# --- DASHBOARD CACHE ---
_dashboard_cache = {}

def get_dashboard_cache(key: str):
    if key in _dashboard_cache:
        data, timestamp = _dashboard_cache[key]
        if time.time() - timestamp < 300: # 5 minutes TTL
            return data
        del _dashboard_cache[key]
    return None

def set_dashboard_cache(key: str, data: dict):
    _dashboard_cache[key] = (data, time.time())

@app.get("/api/dashboard-overview")
def get_dashboard_overview(line: str, start_date: str, end_date: str, direction: str = "VOLTA", start_hour: str = None, end_hour: str = None):
    cache_key = f"{line}_{start_date}_{end_date}_{direction}_{start_hour}_{end_hour}"
    cached_data = get_dashboard_cache(cache_key)
    if cached_data:
        return cached_data

    try:
        map_data = get_map_data(line, start_date, end_date, direction, start_hour, end_hour)
        discovery_svg = get_discovery(line, start_date, end_date, direction, start_hour, end_hour).body.decode("utf-8")
        conformance = get_conformance(line, start_date, end_date, direction, start_hour, end_hour)
        performance = get_performance(line, start_date, end_date, direction, start_hour, end_hour).body.decode("utf-8")

        result = {
            "map_data": map_data,
            "discovery": discovery_svg,
            "conformance": conformance,
            "performance": performance
        }
        set_dashboard_cache(cache_key, result)
        return result
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# -----------------------

@app.get("/api/fleet-audit")
def get_fleet_audit(regime: str = "B"):
    if regime in _fleet_audit_cache:
        return _fleet_audit_cache[regime]

    lines = default_telemetry_repo.list_available_lines(regime=regime)
    
    start_date = '2025-10-24' if regime == 'A' else '2025-12-02'
    end_date = '2025-10-30' if regime == 'A' else '2025-12-08'
    fleet_lines = []
    line_names = {
        "010": "Interbairros I (Circular)",
        "541": "Bairro Novo A (Troncal)",
        "542": "Bairro Novo B (Alimentador)"
    }
    
    for l in lines:
        import glob
        files = glob.glob(f"data/dados_processados/event_log_{l}_*.csv")
        if not files:
            continue
        
        valid_files = []
        for f in files:
            if regime == "A" and "2025-10" in f:
                valid_files.append(f)
            elif regime == "B" and "2025-12" in f:
                valid_files.append(f)
                
        if not valid_files:
            continue
            
        csv_path = sorted(valid_files)[-1]
        try:
            df = pd.read_csv(csv_path)
            total_cases = int(df['case:concept:name'].nunique()) if 'case:concept:name' in df.columns else 0
            
            static_data = load_static_data('2025-10-24' if regime == 'A' else '2025-12-02', l)
            stops_df = static_data.get('pontos', pd.DataFrame())
            chosen_dir, df_dir = resolve_direction_subset(df, "VOLTA")
            conf = ProcessMiningEngine.evaluate_conformance(df, stops_df, direction=chosen_dir)
            fit_pct = float(conf.get("fit_percentage", 0.0))
            avg_fit = float(conf.get("avg_fitness", 0.0))
            adherence_pct = round(avg_fit * 100, 1)
            skipped_stops_count = sum(s.get("count", 0) for s in conf.get("skipped_stops", []))
            
            perf = ProcessMiningEngine.analyze_performance(df_dir, as_svg=False)
            bottlenecks_count = sum(1 for link in perf.get("links", []) if link.get("avg_duration_sec", 0) > 120)
            
            # Context-aware operational status:
            # In Regime A (2m intervals), telemetry jumps cause discrete token omissions,
            # so adherence_pct reflects physical route following.
            if regime == "A":
                if adherence_pct >= 50 and bottlenecks_count <= 5:
                    status = "CONFORME"
                elif adherence_pct >= 35:
                    status = "ATENÇÃO"
                else:
                    status = "CRÍTICO"
            else:
                if fit_pct >= 90 and bottlenecks_count <= 5:
                    status = "CONFORME"
                elif fit_pct >= 70:
                    status = "ATENÇÃO"
                else:
                    status = "CRÍTICO"
                
            fleet_lines.append({
                "line": l,
                "name": line_names.get(l, f"Linha {l}"),
                "total_cases": total_cases,
                "fit_percentage": fit_pct,
                "avg_fitness": avg_fit,
                "adherence_pct": adherence_pct,
                "skipped_stops_count": skipped_stops_count,
                "bottlenecks_count": bottlenecks_count,
                "status": status,
                "direction": chosen_dir
            })
        except Exception:
            pass
            
    total_trips = sum(f["total_cases"] for f in fleet_lines)
    avg_fleet_adherence = float(np.mean([f["adherence_pct"] for f in fleet_lines])) if fleet_lines else 0.0
    avg_global_fit = float(np.mean([f["fit_percentage"] for f in fleet_lines])) if fleet_lines else 0.0
    total_skipped = sum(f["skipped_stops_count"] for f in fleet_lines)
    
    result = {
        "regime": regime,
        "date_range": f"{start_date} a {end_date}",
        "summary": {
            "total_lines": len(fleet_lines),
            "total_trips_audited": total_trips,
            "avg_fleet_adherence": round(avg_fleet_adherence, 1),
            "avg_fleet_conformance": round(avg_global_fit, 1),
            "total_skipped_stops": total_skipped
        },
        "lines": fleet_lines
    }
    _fleet_audit_cache[regime] = result
    return result

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
