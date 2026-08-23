"""
Telemetry Repository & Storage Adapter Module.

Deep domain module that encapsulates data source resolution, date filtering,
line discovery, encoding repair, and telemetry caching behind a clean seam.
"""

import os
import re
import lzma
import json
from abc import ABC, abstractmethod
from datetime import datetime, time
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np


def _parse_coord(val: Any) -> Optional[float]:
    """Parse string/numeric coordinate with comma or dot."""
    if pd.isna(val):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, str):
        val = val.strip().replace(',', '.')
        try:
            return float(val)
        except ValueError:
            return None
    return None


def _fix_encoding(text: Any) -> Any:
    """Repair Latin-1 / UTF-8 mixed encodings."""
    if not isinstance(text, str):
        return text
    try:
        return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        try:
            return text.encode('utf-8').decode('latin-1')
        except Exception:
            return text


class TelemetryStorageAdapter(ABC):
    """Abstract storage adapter interface at the repository seam."""

    @abstractmethod
    def get_static_data(self, date_str: str, line_code: str) -> Dict[str, pd.DataFrame]:
        """Load static stops, planned timetable, and shape geometry."""
        pass

    @abstractmethod
    def get_realtime_telemetry(self, line_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        """Load raw GPS telemetry for a line and date range."""
        pass

    @abstractmethod
    def get_processed_event_log(self, line_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """Load processed event log CSV if available."""
        pass

    @abstractmethod
    def list_available_lines(self, regime: Optional[str] = None) -> List[str]:
        """List line codes available for a given operational regime."""
        pass

    @abstractmethod
    def check_telemetry_status(
        self,
        line_code: str,
        start_date: str,
        end_date: str,
        start_hour: Optional[str] = None,
        end_hour: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check whether processed or raw data exists and count records."""
        pass


class FilesystemTelemetryAdapter(TelemetryStorageAdapter):
    """Production filesystem adapter loading from C3SL and realtime data directories."""

    def __init__(self, base_data_dir: str = "data"):
        self.base_data_dir = base_data_dir
        self.c3sl_dir = os.path.join(base_data_dir, "dados_c3sl")
        self.realtime_dir = os.path.join(base_data_dir, "dados_em_tempo_real_2026")
        self.processed_dir = os.path.join(base_data_dir, "dados_processados")

    def get_static_data(self, date_str: str, line_code: str) -> Dict[str, pd.DataFrame]:
        formatted_date = date_str.replace('-', '_')
        pontos_file = os.path.join(self.c3sl_dir, f"{formatted_date}_pontosLinha.json.xz")
        tabela_file = os.path.join(self.c3sl_dir, f"{formatted_date}_tabelaLinha.json.xz")
        shape_file = os.path.join(self.c3sl_dir, f"{formatted_date}_shapeLinha.json.xz")

        if not os.path.exists(pontos_file) and os.path.exists(self.c3sl_dir):
            fallback_files = [f for f in os.listdir(self.c3sl_dir) if f.endswith("_pontosLinha.json.xz")]
            if fallback_files:
                fallback_date = fallback_files[0].replace("_pontosLinha.json.xz", "")
                pontos_file = os.path.join(self.c3sl_dir, f"{fallback_date}_pontosLinha.json.xz")
                tabela_file = os.path.join(self.c3sl_dir, f"{fallback_date}_tabelaLinha.json.xz")
                shape_file = os.path.join(self.c3sl_dir, f"{fallback_date}_shapeLinha.json.xz")

        # 1. Stops
        pontos_df = pd.DataFrame()
        if os.path.exists(pontos_file):
            try:
                with lzma.open(pontos_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                with lzma.open(pontos_file, 'rt', encoding='latin1') as f:
                    data = json.load(f)
            line_pontos = [p for p in data if p.get('COD') == str(line_code)]
            if line_pontos:
                pontos_df = pd.DataFrame(line_pontos)
                for col in ['NOME', 'SENTIDO']:
                    if col in pontos_df.columns:
                        pontos_df[col] = pontos_df[col].apply(_fix_encoding)
                pontos_df['LAT'] = pontos_df['LAT'].apply(_parse_coord)
                pontos_df['LON'] = pontos_df['LON'].apply(_parse_coord)
                pontos_df['SEQ'] = pontos_df['SEQ'].astype(int)

        # 2. Timetable
        tabela_df = pd.DataFrame()
        if os.path.exists(tabela_file):
            try:
                with lzma.open(tabela_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                with lzma.open(tabela_file, 'rt', encoding='latin1') as f:
                    data = json.load(f)
            line_tabela = [t for t in data if t.get('COD') == str(line_code)]
            if line_tabela:
                tabela_df = pd.DataFrame(line_tabela)
                if 'PONTO' in tabela_df.columns:
                    tabela_df['PONTO'] = tabela_df['PONTO'].apply(_fix_encoding)

        # 3. Shape
        shape_df = pd.DataFrame()
        if os.path.exists(shape_file):
            try:
                with lzma.open(shape_file, 'rt', encoding='utf-8') as f:
                    data = json.load(f)
            except UnicodeDecodeError:
                with lzma.open(shape_file, 'rt', encoding='latin1') as f:
                    data = json.load(f)
            line_shape = [s for s in data if s.get('COD') == str(line_code)]
            if line_shape:
                shape_df = pd.DataFrame(line_shape)
                shape_df['LAT'] = shape_df['LAT'].apply(_parse_coord)
                shape_df['LON'] = shape_df['LON'].apply(_parse_coord)

        # 4. Fallback to static_cache or URBS Open Data API if local C3SL files are missing
        if pontos_df.empty or shape_df.empty:
            cache_dir = os.path.join(self.base_data_dir, "static_cache")
            os.makedirs(cache_dir, exist_ok=True)
            
            # Helper to load or fetch
            def load_or_fetch(kind: str, endpoint: str):
                cache_file = os.path.join(cache_dir, f"{line_code}_{kind}.json")
                if os.path.exists(cache_file):
                    try:
                        with open(cache_file, "r", encoding="utf-8") as f:
                            return json.load(f)
                    except Exception:
                        pass
                try:
                    import requests
                    url = f"https://transporteservico.urbs.curitiba.pr.gov.br/{endpoint}?linha={line_code}&c=65d35"
                    r = requests.get(url, timeout=5)
                    if r.status_code == 200:
                        data = r.json()
                        with open(cache_file, "w", encoding="utf-8") as f:
                            json.dump(data, f)
                        return data
                except Exception:
                    pass
                return []

            if pontos_df.empty:
                pts_data = load_or_fetch("pontos", "getPontosLinha.php")
                if pts_data:
                    pontos_df = pd.DataFrame(pts_data)
                    for col in ['NOME', 'SENTIDO']:
                        if col in pontos_df.columns:
                            pontos_df[col] = pontos_df[col].apply(_fix_encoding)
                    pontos_df['LAT'] = pontos_df['LAT'].apply(_parse_coord)
                    pontos_df['LON'] = pontos_df['LON'].apply(_parse_coord)
                    if 'SEQ' in pontos_df.columns:
                        pontos_df['SEQ'] = pd.to_numeric(pontos_df['SEQ'], errors='coerce').fillna(0).astype(int)

            if tabela_df.empty:
                tab_data = load_or_fetch("tabela", "getTabelaLinha.php")
                if tab_data:
                    tabela_df = pd.DataFrame(tab_data)
                    if 'PONTO' in tabela_df.columns:
                        tabela_df['PONTO'] = tabela_df['PONTO'].apply(_fix_encoding)

            if shape_df.empty:
                shp_data = load_or_fetch("shape", "getShapeLinha.php")
                if shp_data:
                    shape_df = pd.DataFrame(shp_data)
                    shape_df['LAT'] = shape_df['LAT'].apply(_parse_coord)
                    shape_df['LON'] = shape_df['LON'].apply(_parse_coord)

        return {
            'pontos': pontos_df,
            'tabela': tabela_df,
            'shape': shape_df
        }

    def get_realtime_telemetry(self, line_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            return pd.DataFrame()

        date_list = pd.date_range(start_dt, end_dt).strftime("%Y-%m-%d").tolist()
        dfs = []

        for date_str in date_list:
            day_dir = os.path.join(self.realtime_dir, date_str)
            if not os.path.exists(day_dir):
                day_dir_alt = os.path.join(self.realtime_dir, date_str.replace('-', '_'))
                if os.path.exists(day_dir_alt):
                    day_dir = day_dir_alt
                else:
                    continue

            try:
                csv_files = sorted([f for f in os.listdir(day_dir) if f.endswith('.csv')])
            except Exception:
                continue

            for csv_file in csv_files:
                filepath = os.path.join(day_dir, csv_file)
                try:
                    df_temp = pd.read_csv(filepath)
                    if 'CODIGOLINHA' in df_temp.columns:
                        df_temp['CODIGOLINHA_clean'] = df_temp['CODIGOLINHA'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                        search_clean = str(line_code).strip().lstrip('0') or "0"
                        df_filtered = df_temp[
                            (df_temp['CODIGOLINHA_clean'] == str(line_code).strip()) |
                            (df_temp['CODIGOLINHA_clean'] == search_clean) |
                            (df_temp['CODIGOLINHA_clean'].str.lstrip('0') == search_clean)
                        ].copy()
                        if not df_filtered.empty:
                            dfs.append(df_filtered)
                except Exception:
                    pass

        return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

    def get_processed_event_log(self, line_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        csv_path = os.path.join(self.processed_dir, f"event_log_{line_code}_{start_date}_{end_date}.csv")
        if os.path.exists(csv_path):
            try:
                return pd.read_csv(csv_path)
            except Exception:
                return None
        return None

    def list_available_lines(self, regime: Optional[str] = None) -> List[str]:
        processed_lines = set()
        if os.path.exists(self.processed_dir):
            for f in os.listdir(self.processed_dir):
                if f.startswith("event_log_") and f.endswith(".csv"):
                    match = re.match(r"^event_log_(.+?)_(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.csv$", f)
                    if match:
                        line_code, start_date_str, _ = match.groups()
                        if regime == "A" and start_date_str == "2025-10-24":
                            processed_lines.add(line_code)
                        elif regime == "B" and start_date_str == "2025-12-02":
                            processed_lines.add(line_code)
                        elif regime not in ["A", "B"]:
                            processed_lines.add(line_code)

        processed_lines = {l for l in processed_lines if l != 'REC' and not l.startswith('X')}
        if processed_lines:
            return sorted(list(processed_lines))

        # Fallback to raw data directories
        def extract_lines_from_dir(day_dir: str) -> set:
            lines = set()
            if os.path.exists(day_dir):
                for f in os.listdir(day_dir):
                    if f.endswith('.csv'):
                        try:
                            df = pd.read_csv(os.path.join(day_dir, f), usecols=['CODIGOLINHA'])
                            lines.update(df['CODIGOLINHA'].dropna().astype(str).unique())
                        except Exception:
                            pass
            return {l for l in lines if l != 'REC' and not l.startswith('X')}

        if regime == "A":
            return sorted(list(extract_lines_from_dir(os.path.join(self.realtime_dir, '2025-10-24'))))
        elif regime == "B":
            return sorted(list(extract_lines_from_dir(os.path.join(self.realtime_dir, '2025-12-02'))))
        else:
            lines_a = extract_lines_from_dir(os.path.join(self.realtime_dir, '2025-10-24'))
            lines_b = extract_lines_from_dir(os.path.join(self.realtime_dir, '2025-12-02'))
            return sorted(list(lines_a.intersection(lines_b)))

    def check_telemetry_status(
        self,
        line_code: str,
        start_date: str,
        end_date: str,
        start_hour: Optional[str] = None,
        end_hour: Optional[str] = None
    ) -> Dict[str, Any]:
        df_processed = self.get_processed_event_log(line_code, start_date, end_date)
        if df_processed is not None and not df_processed.empty:
            df_filtered = df_processed.copy()
            if 'time:timestamp' in df_filtered.columns:
                df_filtered['time:timestamp'] = pd.to_datetime(df_filtered['time:timestamp'])
                if start_hour and end_hour:
                    try:
                        eh_str = "23:59:59" if ("24:00" in end_hour or "23:59" in end_hour) else end_hour
                        sh_parts = [int(p) for p in start_hour.split(":")]
                        eh_parts = [int(p) for p in eh_str.split(":")]
                        st = time(sh_parts[0], sh_parts[1] if len(sh_parts) > 1 else 0)
                        et = time(eh_parts[0], eh_parts[1] if len(eh_parts) > 1 else 0, eh_parts[2] if len(eh_parts) > 2 else 0)
                        times = df_filtered['time:timestamp'].dt.time
                        df_filtered = df_filtered[(times >= st) & (times <= et)]
                    except Exception:
                        pass
            count = int(df_filtered['case:concept:name'].nunique()) if 'case:concept:name' in df_filtered.columns else len(df_filtered)
            if count > 0:
                min_t = df_filtered['time:timestamp'].min().strftime("%H:%M:%S")
                max_t = df_filtered['time:timestamp'].max().strftime("%H:%M:%S")
                msg = f"Já existem dados minerados! Encontradas {count} viagens processadas das {min_t} às {max_t}."
            else:
                msg = "Já existem dados minerados para esse período, mas não há viagens na faixa horária selecionada."
            return {"exists": count > 0, "count": count, "message": msg, "status": "processed"}

        # Scan raw GPS points
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            date_list = pd.date_range(start_dt, end_dt).strftime("%Y-%m-%d").tolist()
        except Exception:
            return {"exists": False, "count": 0, "message": "Datas inválidas", "status": "raw"}

        start_h_int = int(start_hour.split(":")[0]) if start_hour else 0
        end_h_int = 24 if (not end_hour or "24:00" in end_hour or "23:59" in end_hour) else int(end_hour.split(":")[0])

        total_records = 0
        for date_str in date_list:
            day_dir = os.path.join(self.realtime_dir, date_str)
            if not os.path.exists(day_dir):
                day_dir_alt = os.path.join(self.realtime_dir, date_str.replace('-', '_'))
                if os.path.exists(day_dir_alt):
                    day_dir = day_dir_alt
                else:
                    continue
            try:
                files = os.listdir(day_dir)
            except Exception:
                continue

            for f in files:
                if not f.endswith('.csv'):
                    continue
                try:
                    hour_part = int(f.split('_')[-1].split('-')[0])
                    if hour_part < start_h_int or hour_part > end_h_int:
                        continue
                except Exception:
                    pass

                filepath = os.path.join(day_dir, f)
                try:
                    df_temp = pd.read_csv(filepath, usecols=['CODIGOLINHA', 'request_timestamp'])
                    df_temp['CODIGOLINHA_clean'] = df_temp['CODIGOLINHA'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
                    search_clean = str(line_code).strip().lstrip('0') or "0"
                    df_line = df_temp[
                        (df_temp['CODIGOLINHA_clean'] == str(line_code).strip()) |
                        (df_temp['CODIGOLINHA_clean'] == search_clean) |
                        (df_temp['CODIGOLINHA_clean'].str.lstrip('0') == search_clean)
                    ]
                    if not df_line.empty:
                        total_records += len(df_line)
                except Exception:
                    pass

        if total_records > 0:
            msg = f"Nenhum log processado ainda. Porém, foram encontrados {total_records} pontos de GPS brutos para a linha {line_code}. Clique em 'Processar Mineração' para executar."
        else:
            msg = f"Nenhum registro bruto de GPS foi encontrado para a linha {line_code} no período selecionado."

        return {"exists": total_records > 0, "count": total_records, "message": msg, "status": "raw"}


class InMemoryTelemetryAdapter(TelemetryStorageAdapter):
    """Test adapter with in-memory tables."""

    def __init__(
        self,
        static_data: Optional[Dict[str, pd.DataFrame]] = None,
        realtime_data: Optional[pd.DataFrame] = None,
        processed_logs: Optional[Dict[str, pd.DataFrame]] = None,
        lines_by_regime: Optional[Dict[str, List[str]]] = None
    ):
        self.static_data = static_data if static_data is not None else {'pontos': pd.DataFrame(), 'tabela': pd.DataFrame(), 'shape': pd.DataFrame()}
        self.realtime_data = realtime_data if realtime_data is not None else pd.DataFrame()
        self.processed_logs = processed_logs if processed_logs is not None else {}
        self.lines_by_regime = lines_by_regime if lines_by_regime is not None else {"A": ["541", "010"], "B": ["541", "542"], "ALL": ["541"]}

    def get_static_data(self, date_str: str, line_code: str) -> Dict[str, pd.DataFrame]:
        return self.static_data

    def get_realtime_telemetry(self, line_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        if self.realtime_data.empty:
            return pd.DataFrame()
        df = self.realtime_data
        if 'CODIGOLINHA' in df.columns:
            return df[df['CODIGOLINHA'].astype(str) == str(line_code)].copy()
        return df.copy()

    def get_processed_event_log(self, line_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        key = f"{line_code}_{start_date}_{end_date}"
        return self.processed_logs.get(key)

    def list_available_lines(self, regime: Optional[str] = None) -> List[str]:
        if regime in self.lines_by_regime:
            return sorted(self.lines_by_regime[regime])
        return sorted(self.lines_by_regime.get("ALL", ["541"]))

    def check_telemetry_status(
        self,
        line_code: str,
        start_date: str,
        end_date: str,
        start_hour: Optional[str] = None,
        end_hour: Optional[str] = None
    ) -> Dict[str, Any]:
        key = f"{line_code}_{start_date}_{end_date}"
        if key in self.processed_logs:
            df = self.processed_logs[key]
            cnt = int(df['case:concept:name'].nunique()) if 'case:concept:name' in df.columns else len(df)
            return {"exists": True, "count": cnt, "message": f"Found {cnt} trips", "status": "processed"}
        if not self.realtime_data.empty:
            return {"exists": True, "count": len(self.realtime_data), "message": "Raw points available", "status": "raw"}
        return {"exists": False, "count": 0, "message": "No data", "status": "raw"}


class TelemetryRepository:
    """Unified repository coordinator for static and realtime telemetry access."""

    def __init__(self, adapter: Optional[TelemetryStorageAdapter] = None):
        self.adapter: TelemetryStorageAdapter = adapter or FilesystemTelemetryAdapter()

    def get_static_data(self, date_str: str, line_code: str) -> Dict[str, pd.DataFrame]:
        return self.adapter.get_static_data(date_str, line_code)

    def get_realtime_telemetry(self, line_code: str, start_date: str, end_date: str) -> pd.DataFrame:
        return self.adapter.get_realtime_telemetry(line_code, start_date, end_date)

    def get_processed_event_log(self, line_code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        return self.adapter.get_processed_event_log(line_code, start_date, end_date)

    def list_available_lines(self, regime: Optional[str] = None) -> List[str]:
        return self.adapter.list_available_lines(regime)

    def check_telemetry_status(
        self,
        line_code: str,
        start_date: str,
        end_date: str,
        start_hour: Optional[str] = None,
        end_hour: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.adapter.check_telemetry_status(line_code, start_date, end_date, start_hour, end_hour)


# Default global instance
default_telemetry_repo = TelemetryRepository()
