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
    dir_a = os.path.join(data_dir, '2025-10-24')
    lines_a = set()
    if os.path.exists(dir_a):
        for f in os.listdir(dir_a):
            if f.endswith('.csv'):
                try:
                    df = pd.read_csv(os.path.join(dir_a, f), usecols=['CODIGOLINHA'])
                    lines_a.update(df['CODIGOLINHA'].dropna().astype(str).unique())
                except:
                    pass
                    
    dir_b = os.path.join(data_dir, '2025-12-02')
    lines_b = set()
    if os.path.exists(dir_b):
        for f in os.listdir(dir_b):
            if f.endswith('.csv'):
                try:
                    df = pd.read_csv(os.path.join(dir_b, f), usecols=['CODIGOLINHA'])
                    lines_b.update(df['CODIGOLINHA'].dropna().astype(str).unique())
                except:
                    pass
                    
    intersection = lines_a.intersection(lines_b)
    intersection = {l for l in intersection if l != 'REC' and not l.startswith('X')}
    return sorted(list(intersection))

# Helper to filter DataFrame by start_hour and end_hour query params
def filter_df_by_hours(df: pd.DataFrame, start_hour: str = None, end_hour: str = None) -> pd.DataFrame:
    if df.empty:
        return df
    
    # Garantir datetime
    df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
    
    if start_hour and end_hour:
        try:
            if end_hour.startswith("24:00") or end_hour == "24:00":
                end_hour = "23:59:59"
            
            # Parsing robusto sem depender de strings de formato estritas
            sh_split = start_hour.split(":")
            eh_split = end_hour.split(":")
            
            from datetime import time
            start_t = time(int(sh_split[0]), int(sh_split[1]) if len(sh_split) > 1 else 0)
            end_t = time(
                int(eh_split[0]), 
                int(eh_split[1]) if len(eh_split) > 1 else 0, 
                int(eh_split[2]) if len(eh_split) > 2 else 0
            )
            
            # Filtro da faixa de horário
            times = df['time:timestamp'].dt.time
            df = df[(times >= start_t) & (times <= end_t)]
        except Exception as e:
            print(f"Erro ao filtrar faixas de horário ({start_hour} - {end_hour}): {str(e)}")
            
    return df

# 1. Rota de Linhas em Comum
@app.get("/api/lines")
def read_lines(regime: str = None):
    try:
        import re
        processed_dir = "data/dados_processados"
        processed_lines = set()
        if os.path.exists(processed_dir):
            for f in os.listdir(processed_dir):
                if f.startswith("event_log_") and f.endswith(".csv"):
                    match = re.match(r"^event_log_(.+?)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$", f)
                    if match:
                        line_code, start_date_str, end_date_str = match.groups()
                        if regime == "A":
                            if start_date_str == "2025-10-24":
                                processed_lines.add(line_code)
                        elif regime == "B":
                            if start_date_str == "2025-12-02":
                                processed_lines.add(line_code)
                        else:
                            processed_lines.add(line_code)
                            
        processed_lines = {l for l in processed_lines if l != 'REC' and not l.startswith('X')}
        
        if not processed_lines:
            data_dir = "data/dados_em_tempo_real_2026"
            if regime == "A":
                dir_a = os.path.join(data_dir, '2025-10-24')
                lines_a = set()
                if os.path.exists(dir_a):
                    for f in os.listdir(dir_a):
                        if f.endswith('.csv'):
                            try:
                                df = pd.read_csv(os.path.join(dir_a, f), usecols=['CODIGOLINHA'])
                                lines_a.update(df['CODIGOLINHA'].dropna().astype(str).unique())
                            except:
                                pass
                processed_lines = {l for l in lines_a if l != 'REC' and not l.startswith('X')}
            elif regime == "B":
                dir_b = os.path.join(data_dir, '2025-12-02')
                lines_b = set()
                if os.path.exists(dir_b):
                    for f in os.listdir(dir_b):
                        if f.endswith('.csv'):
                            try:
                                df = pd.read_csv(os.path.join(dir_b, f), usecols=['CODIGOLINHA'])
                                lines_b.update(df['CODIGOLINHA'].dropna().astype(str).unique())
                            except:
                                pass
                processed_lines = {l for l in lines_b if l != 'REC' and not l.startswith('X')}
            else:
                processed_lines = get_common_lines()
                
        return {"lines": sorted(list(processed_lines))}
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
    try:
        from datetime import datetime, time
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    except Exception:
        return 0

    date_list = pd.date_range(start_dt, end_dt).strftime("%Y-%m-%d").tolist()
    
    start_h_int = 0
    end_h_int = 24
    if start_hour:
        try:
            start_h_int = int(start_hour.split(":")[0])
        except:
            pass
    if end_hour:
        try:
            end_h_int = int(end_hour.split(":")[0])
            if "23:59" in end_hour or "24:00" in end_hour:
                end_h_int = 24
        except:
            pass
            
    total_records = 0
    
    for date_str in date_list:
        day_dir = os.path.join(data_dir, date_str)
        if not os.path.exists(day_dir):
            day_dir_alt = os.path.join(data_dir, date_str.replace('-', '_'))
            if os.path.exists(day_dir_alt):
                day_dir = day_dir_alt
            else:
                continue
                
        try:
            files = os.listdir(day_dir)
        except:
            continue
            
        for f in files:
            if not f.endswith('.csv'):
                continue
                
            try:
                hour_part = int(f.split('_')[-1].split('-')[0])
            except:
                continue
                
            if hour_part < start_h_int or hour_part > end_h_int:
                continue
                
            filepath = os.path.join(day_dir, f)
            try:
                df_temp = pd.read_csv(filepath, usecols=['CODIGOLINHA', 'request_timestamp'])
                df_temp['CODIGOLINHA_clean'] = df_temp['CODIGOLINHA'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                search_clean = str(line_code).strip().lstrip('0')
                if not search_clean:
                    search_clean = "0"
                df_line = df_temp[
                    (df_temp['CODIGOLINHA_clean'] == str(line_code).strip()) |
                    (df_temp['CODIGOLINHA_clean'] == search_clean) |
                    (df_temp['CODIGOLINHA_clean'].str.lstrip('0') == search_clean)
                ]
                if df_line.empty:
                    continue
                    
                if start_hour or end_hour:
                    df_line = df_line.copy()
                    df_line['ts'] = pd.to_datetime(df_line['request_timestamp'])
                    df_times = df_line['ts'].dt.time
                    
                    sh_split = start_hour.split(":") if start_hour else ["00", "00"]
                    eh_split = end_hour.split(":") if end_hour else ["23", "59", "59"]
                    if len(eh_split) == 2 and eh_split[0] == "24":
                        eh_split = ["23", "59", "59"]
                    elif len(eh_split) == 2 and eh_split[0] == "23" and eh_split[1] == "59":
                        eh_split = ["23", "59", "59"]
                        
                    start_t = time(int(sh_split[0]), int(sh_split[1]) if len(sh_split) > 1 else 0)
                    end_t = time(int(eh_split[0]), int(eh_split[1]) if len(eh_split) > 1 else 0, int(eh_split[2]) if len(eh_split) > 2 else 0)
                    
                    df_line = df_line[(df_times >= start_t) & (df_times <= end_t)]
                    
                total_records += len(df_line)
            except Exception as e:
                pass
                
    return total_records

# 2.1. Endpoint para verificar quantidade de viagens disponíveis antes de processar
@app.get("/api/check-trips")
def check_trips(line: str, start_date: str, end_date: str, start_hour: str = None, end_hour: str = None):
    csv_path = f"data/dados_processados/event_log_{line}_{start_date}_{end_date}.csv"
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path, usecols=['case:concept:name', 'time:timestamp'])
            df = filter_df_by_hours(df, start_hour, end_hour)
            count = int(df['case:concept:name'].nunique())
            
            if count > 0:
                df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
                min_time = df['time:timestamp'].min().strftime("%H:%M:%S")
                max_time = df['time:timestamp'].max().strftime("%H:%M:%S")
                msg = f"Já existem dados minerados! Encontradas {count} viagens processadas das {min_time} às {max_time}."
            else:
                msg = "Já existem dados minerados para esse período, mas não há viagens na faixa horária selecionada."
                
            return {
                "exists": count > 0,
                "count": count,
                "message": msg,
                "status": "processed"
            }
        except Exception as e:
            pass
            
    try:
        total_raw_points = check_raw_gps_data(line, start_date, end_date, start_hour, end_hour)
        if total_raw_points > 0:
            msg = f"Nenhum log processado ainda. Porém, foram encontrados {total_raw_points} pontos de GPS brutos para a linha {line} neste período/horário. Clique em 'Processar Mineração' para executar a mineração e ativar os mapas."
        else:
            msg = f"Nenhum registro bruto de GPS foi encontrado para a linha {line} no período/horário selecionados. Se você rodar a mineração, os mapas ficarão vazios."
            
        return {
            "exists": total_raw_points > 0,
            "count": total_raw_points,
            "message": msg,
            "status": "raw"
        }
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
        
        stops_df = static_data['pontos']
        shape_df = static_data['shape']
        
        if stops_df.empty:
            return {"stops": [], "shape": [], "segments": [], "replay_trips": [], "metrics": {}}
            
        # Filtrar o DataFrame consolidado com base na faixa horária e sentido
        df_log = filter_df_by_hours(df_log_raw, start_hour, end_hour)
        df_log_dir = df_log[df_log['gps_direction'] == direction]
        
        # Resolução do Sentido Estático Planejado
        sentido_static = None
        if not df_log_dir.empty:
            sample_stop_name = df_log_dir['concept:name'].iloc[0].replace('PASSAGEM_', '')
            matching_stops = stops_df[stops_df['NOME'] == sample_stop_name]
            if not matching_stops.empty:
                sentido_static = matching_stops['SENTIDO'].iloc[0]
                
        if not sentido_static and not stops_df.empty:
            sentidos = stops_df['SENTIDO'].unique()
            if len(sentidos) > 0:
                if direction == 'VOLTA' or len(sentidos) == 1:
                    sentido_static = sentidos[0]
                else:
                    sentido_static = sentidos[1]
                    
        stops_filtered = stops_df[stops_df['SENTIDO'] == sentido_static].sort_values('SEQ').copy()
        
        shape_coords = []
        shape_filtered = pd.DataFrame()
        if not shape_df.empty and 'SHP' in shape_df.columns:
            shps = shape_df['SHP'].unique()
            if len(shps) == 1:
                shape_filtered = shape_df[shape_df['SHP'] == shps[0]].copy()
            elif len(shps) > 1 and sentido_static:
                stops_for_sentido = stops_df[stops_df['SENTIDO'] == sentido_static]
                if not stops_for_sentido.empty:
                    stop_lats = stops_for_sentido['LAT'].values
                    stop_lons = stops_for_sentido['LON'].values
                    
                    best_shp = None
                    min_avg_dist = float('inf')
                    
                    for shp in shps:
                        shp_pts = shape_df[shape_df['SHP'] == shp]
                        if shp_pts.empty:
                            continue
                        shp_lats = shp_pts['LAT'].values
                        shp_lons = shp_pts['LON'].values
                        
                        from src.etl.clean_data import haversine_vectorized
                        dists_list = []
                        for s_lat, s_lon in zip(stop_lats, stop_lons):
                            dists = haversine_vectorized(
                                np.full_like(shp_lats, s_lat), np.full_like(shp_lons, s_lon),
                                shp_lats, shp_lons
                            )
                            dists_list.append(dists.min())
                        avg_dist = np.mean(dists_list)
                        if avg_dist < min_avg_dist:
                            min_avg_dist = avg_dist
                            best_shp = shp
                    if best_shp:
                        shape_filtered = shape_df[shape_df['SHP'] == best_shp].copy()
                        
            if not shape_filtered.empty:
                shape_coords = list(zip(shape_filtered['LAT'].tolist(), shape_filtered['LON'].tolist()))
                
        # Projeta paradas no shape
        if not shape_filtered.empty and not stops_filtered.empty:
            from src.etl.geofencing import map_gps_to_shape
            shape_lats = shape_filtered['LAT'].values
            shape_lons = shape_filtered['LON'].values
            stop_shape_indices = map_gps_to_shape(stops_filtered['LAT'].values, stops_filtered['LON'].values, shape_lats, shape_lons)
            stop_shape_indices = np.maximum.accumulate(stop_shape_indices)
            stops_filtered['shape_idx'] = stop_shape_indices

        # ALTERNATIVA A: Calcular velocidades agregadas de segmentos (Trecho i -> Trecho i+1)
        segments = []
        if not df_log_dir.empty and not shape_filtered.empty and not stops_filtered.empty:
            stops_records = stops_filtered.to_dict('records')
            
            # Para cada trecho entre as paradas consecutivas, calcular velocidade média da frota
            for i in range(len(stops_records) - 1):
                st1 = stops_records[i]
                st2 = stops_records[i+1]
                
                idx1 = st1['shape_idx']
                idx2 = st2['shape_idx']
                if idx1 > idx2:
                    idx1, idx2 = idx2, idx1
                    
                seg_df = shape_filtered.iloc[idx1 : idx2 + 1]
                seg_coords = list(zip(seg_df['LAT'].tolist(), seg_df['LON'].tolist()))
                
                # Calcular distância do segmento
                from src.etl.clean_data import haversine_vectorized
                dist = 0.0
                if len(seg_coords) > 1:
                    lats = seg_df['LAT'].values
                    lons = seg_df['LON'].values
                    dists = haversine_vectorized(lats[:-1], lons[:-1], lats[1:], lons[1:])
                    dist = float(dists.sum())
                
                # Coletar passagens de ônibus nesse trecho
                speeds_list = []
                stop_name_1 = f"PASSAGEM_{st1['NOME']}"
                stop_name_2 = f"PASSAGEM_{st2['NOME']}"
                
                # Encontrar casos que passaram por ambos os pontos consecutivamente
                cases_passed = df_log_dir[df_log_dir['concept:name'].isin([stop_name_1, stop_name_2])]
                if not cases_passed.empty:
                    grouped = cases_passed.groupby('case:concept:name')
                    for case_id, group in grouped:
                        if len(group) == 2:
                            # Garantir que o seq da parada está ordenado
                            g_sorted = group.sort_values('stop_seq')
                            t1 = pd.to_datetime(g_sorted['time:timestamp'].iloc[0])
                            t2 = pd.to_datetime(g_sorted['time:timestamp'].iloc[1])
                            duration_sec = (t2 - t1).total_seconds()
                            if duration_sec > 0:
                                speeds_list.append((dist / duration_sec) * 3.6)
                
                # Velocidade agregada (mediana das velocidades ou 25 km/h por padrão se não houver dados)
                avg_speed = float(np.median(speeds_list)) if speeds_list else 25.0
                
                # Cor conforme congestionamento
                if avg_speed < 12.0:
                    color = "#ff4b4b"  # Vermelho (Lento/Congestionado)
                elif avg_speed < 20.0:
                    color = "#f59e0b"  # Laranja (Atenção/Moderado)
                else:
                    color = "#ffffff"  # Branco (Livre/Normal)
                    
                segments.append({
                    "from_stop": st1['NOME'],
                    "to_stop": st2['NOME'],
                    "coords": seg_coords,
                    "speed": avg_speed,
                    "color": color
                })

        # ALTERNATIVA B: Replay Multiveículos (Estrutura de dados das viagens ativas para o JS interpolar)
        replay_trips = []
        if not df_log_dir.empty and not shape_filtered.empty and not stops_filtered.empty:
            cases_ids = df_log_dir['case:concept:name'].unique()
            for cid in cases_ids:
                c_events = df_log_dir[df_log_dir['case:concept:name'] == cid].sort_values('stop_seq')
                
                # Juntar coordenadas geográficas das paradas
                c_merged = pd.merge(
                    c_events[['stop_seq', 'time:timestamp']],
                    stops_filtered[['SEQ', 'NOME', 'LAT', 'LON', 'shape_idx']],
                    left_on='stop_seq',
                    right_on='SEQ',
                    how='inner'
                ).sort_values('stop_seq')
                
                path_pts = []
                for idx, row in c_merged.iterrows():
                    path_pts.append({
                        "time": row['time:timestamp'].isoformat() if hasattr(row['time:timestamp'], "isoformat") else str(row['time:timestamp']),
                        "lat": float(row['LAT']),
                        "lon": float(row['LON']),
                        "stop_name": str(row['NOME'])
                    })
                
                if len(path_pts) > 1:
                    replay_trips.append({
                        "case_id": cid,
                        "vehicle": str(c_events['org:resource'].iloc[0]),
                        "path": path_pts
                    })

        stops_list = []
        for idx, stop in stops_filtered.iterrows():
            stop_name_log = f"PASSAGEM_{stop['NOME']}"
            df_stop_events = df_log_dir[df_log_dir['concept:name'] == stop_name_log]
            passages = len(df_stop_events)
            
            # Identifica se houve interpolação
            is_interpolated = False
            if not df_log_dir.empty:
                rep_event = df_log_dir[df_log_dir['concept:name'] == stop_name_log]
                if not rep_event.empty:
                    is_interpolated = bool(rep_event['interpolated'].iloc[0])
            
            stops_list.append({
                "seq": int(stop['SEQ']),
                "nome": str(stop['NOME']),
                "num": str(stop['NUM']),
                "lat": float(stop['LAT']),
                "lon": float(stop['LON']),
                "passages": passages,
                "interpolated": is_interpolated
            })
            
        # Calcular KPIs Reais Gerais baseados na faixa filtrada
        total_viagens = int(df_log_dir['case:concept:name'].nunique())
        total_eventos = int(len(df_log_dir))
        veiculos_ativos = int(df_log_dir['org:resource'].nunique())
        taxa_interpolacao = float((df_log_dir['interpolated'].sum() / len(df_log_dir)) * 100) if len(df_log_dir) > 0 else 0.0
        
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
