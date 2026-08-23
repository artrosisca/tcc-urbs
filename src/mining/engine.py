"""
Process Mining Engine for URBS Bus Network.

Unified deep module providing discovery, conformance replay, performance DFG,
and delay analytics behind a single consistent domain interface.
"""

import os
import io
import re
import unicodedata
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
import pm4py
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils


def _get_fallback_svg(title: str, message: str, tip: str = "") -> str:
    """Generate an elegant fallback SVG when Graphviz is unavailable."""
    tip_elem = f"""<text x="50%" y="80%" dominant-baseline="middle" text-anchor="middle" fill="#94a3b8" font-family="'Inter', sans-serif" font-size="11px">{tip}</text>""" if tip else ""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 200" width="100%" height="100%">
  <rect width="100%" height="100%" fill="#121214" rx="10"/>
  <text x="50%" y="45%" dominant-baseline="middle" text-anchor="middle" fill="#ff4b4b" font-family="'Inter', sans-serif" font-size="16px" font-weight="bold">
    {title}
  </text>
  <text x="50%" y="65%" dominant-baseline="middle" text-anchor="middle" fill="#cbd5e1" font-family="'Inter', sans-serif" font-size="12px">
    {message}
  </text>
  {tip_elem}
</svg>"""


class ProcessMiningEngine:
    """Deep module for process discovery, conformance, and performance analysis."""

    @staticmethod
    def format_event_log(df: pd.DataFrame) -> Any:
        """Format DataFrame for PM4Py compliance."""
        if df.empty:
            return df
        return pm4py.format_dataframe(
            df,
            case_id='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )

    @classmethod
    def discover_petri_net(
        cls,
        event_log_df: pd.DataFrame,
        as_svg: bool = False
    ) -> Union[Dict[str, Any], str]:
        """
        Discover an Inductive Petri Net from the event log.

        Args:
            event_log_df: DataFrame formatted with case:concept:name, concept:name, time:timestamp
            as_svg: If True, returns SVG string representation; if False, returns JSON-serializable dict.

        Returns:
            SVG string or graph dict containing places, transitions, arcs, markings.
        """
        if event_log_df.empty:
            return "<svg></svg>" if as_svg else {"places": [], "transitions": [], "arcs": [], "initial_marking": [], "final_marking": []}

        log_pm4py = cls.format_event_log(event_log_df)
        net, initial_marking, final_marking = pm4py.discover_petri_net_inductive(log_pm4py)

        if as_svg:
            from pm4py.visualization.petri_net import visualizer as pn_visualizer
            try:
                gviz = pn_visualizer.apply(net, initial_marking, final_marking)
                return gviz.pipe(format='svg').decode('utf-8') if isinstance(gviz.pipe(format='svg'), bytes) else gviz.pipe(format='svg')
            except Exception:
                return _get_fallback_svg(
                    "Graphviz (dot) Não Encontrado ou Falhou",
                    "Para visualizar a representação do modelo, instale o Graphviz e adicione-o ao PATH.",
                    "Dica: Execute 'choco install graphviz -y' no Windows ou 'apt install graphviz' no Linux."
                )

        places = [{"id": p.name, "label": p.name.replace("PASSAGEM_", ""), "type": "place"} for p in net.places]
        transitions = []
        for t in net.transitions:
            label = t.label if t.label else t.name
            transitions.append({
                "id": t.name,
                "label": label.replace("PASSAGEM_", ""),
                "type": "transition",
                "silent": t.label is None
            })
        arcs = [{"source": a.source.name, "target": a.target.name} for a in net.arcs]
        im_list = [p.name for p in initial_marking]
        fm_list = [p.name for p in final_marking]

        return {
            "places": places,
            "transitions": transitions,
            "arcs": arcs,
            "initial_marking": im_list,
            "final_marking": fm_list
        }

    @classmethod
    def create_normative_petri_net(cls, stops_df: pd.DataFrame) -> Tuple[PetriNet, Marking, Marking]:
        """Build a strict sequential normative Petri Net from planned stops."""
        net = PetriNet("Normative_Model")
        stops = stops_df.sort_values(by='SEQ')

        prev_place = PetriNet.Place("place_start")
        net.places.add(prev_place)

        initial_marking = Marking()
        initial_marking[prev_place] = 1

        for idx, row in stops.iterrows():
            act_name = f"PASSAGEM_{row['NOME']}"
            transition = PetriNet.Transition(f"trans_{row['SEQ']}", act_name)
            net.transitions.add(transition)

            next_place = PetriNet.Place(f"place_{row['SEQ']}")
            net.places.add(next_place)

            petri_utils.add_arc_from_to(prev_place, transition, net)
            petri_utils.add_arc_from_to(transition, next_place, net)

            prev_place = next_place

        final_marking = Marking()
        final_marking[prev_place] = 1

        return net, initial_marking, final_marking

    @classmethod
    def evaluate_conformance(
        cls,
        event_log_df: pd.DataFrame,
        static_stops_df: pd.DataFrame,
        direction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluate trace fitness and detect skipped stops against normative route stops.

        Args:
            event_log_df: Event log DataFrame.
            static_stops_df: Planned static stops DataFrame.
            direction: Optional filter ("IDA" or "VOLTA"). If None, returns results per direction.

        Returns:
            Dictionary containing conformance statistics and deviation details.
        """
        if event_log_df.empty or static_stops_df.empty:
            empty_res = {"avg_fitness": 0.0, "fit_percentage": 0.0, "total_cases": 0, "skipped_stops": [], "deviant_trips": []}
            return empty_res if direction else {}

        # Ensure datetime
        if not pd.api.types.is_datetime64_any_dtype(event_log_df['time:timestamp']):
            event_log_df = event_log_df.copy()
            event_log_df['time:timestamp'] = pd.to_datetime(event_log_df['time:timestamp'])

        results: Dict[str, Any] = {}
        grouped = event_log_df.groupby('gps_direction') if 'gps_direction' in event_log_df.columns else [('ALL', event_log_df)]

        for dir_name, group in grouped:
            if direction and dir_name != direction:
                continue

            # Dynamically resolve static direction
            sentido_static = None
            if not group.empty and 'NOME' in static_stops_df.columns and 'SENTIDO' in static_stops_df.columns:
                first_concept = group['concept:name'].iloc[0]
                sample_stop_name = first_concept.replace('PASSAGEM_', '')
                matching = static_stops_df[static_stops_df['NOME'] == sample_stop_name]
                if not matching.empty:
                    sentido_static = matching['SENTIDO'].iloc[0]

            if not sentido_static and 'SENTIDO' in static_stops_df.columns:
                sentidos = static_stops_df['SENTIDO'].unique()
                if len(sentidos) > 0:
                    sentido_static = sentidos[0] if (dir_name == 'VOLTA' or len(sentidos) == 1) else sentidos[1]

            if not sentido_static:
                stops_dir = static_stops_df.sort_values('SEQ').copy()
            else:
                stops_dir = static_stops_df[static_stops_df['SENTIDO'] == sentido_static].sort_values('SEQ').copy()

            if stops_dir.empty:
                continue

            # 1. Normative Petri Net & Token Replay
            net, init_m, final_m = cls.create_normative_petri_net(stops_dir)
            log = cls.format_event_log(group)

            avg_fitness = 0.0
            fit_pct = 0.0
            total_cases = 0

            try:
                replayed = pm4py.conformance_diagnostics_token_based_replay(log, net, init_m, final_m)
                fitnesses = [t['trace_fitness'] for t in replayed]
                avg_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0.0
                fit_count = sum(1 for t in replayed if t['trace_is_fit'])
                fit_pct = (fit_count / len(replayed) * 100) if replayed else 0.0
                total_cases = len(replayed)
            except Exception as e:
                pass

            # 2. Heuristic Skipped Stops & Deviations
            planned_stops = ['PASSAGEM_' + str(n) for n in stops_dir['NOME'].tolist()]
            deviations = []
            skipped_stops_all = []

            for case_id, case_group in group.groupby('case:concept:name'):
                case_sorted = case_group.sort_values('stop_seq') if 'stop_seq' in case_group.columns else case_group
                visited = set(case_sorted['concept:name'].tolist())

                skipped = []
                interp_count = 0
                for stop in planned_stops:
                    stop_rows = case_sorted[case_sorted['concept:name'] == stop]
                    if stop_rows.empty:
                        clean_name = stop.replace('PASSAGEM_', '')
                        skipped.append(clean_name)
                        skipped_stops_all.append(clean_name)
                    elif 'interpolated' in stop_rows.columns and stop_rows['interpolated'].iloc[0]:
                        interp_count += 1

                veh = case_group['org:resource'].iloc[0] if 'org:resource' in case_group.columns else "N/A"
                tab = case_group['tabela'].iloc[0] if 'tabela' in case_group.columns else "N/A"

                deviations.append({
                    'case_id': str(case_id),
                    'vehicle': str(veh),
                    'tabela': str(tab),
                    'total_planned': len(planned_stops),
                    'total_visited': len(visited),
                    'skipped_count': len(skipped),
                    'skipped_stops': skipped,
                    'interpolated_count': interp_count
                })

            df_dev = pd.DataFrame(deviations)

            # Aggregate skipped counts
            skipped_counts = []
            if skipped_stops_all:
                series = pd.Series(skipped_stops_all).value_counts()
                for stop_name, count in series.items():
                    skipped_counts.append({
                        "stop_name": str(stop_name),
                        "count": int(count)
                    })

            # Top deviant trips
            deviant_trips = []
            if not df_dev.empty:
                df_dev_sorted = df_dev.sort_values(by='skipped_count', ascending=False).head(10)
                for idx, row in df_dev_sorted.iterrows():
                    deviant_trips.append({
                        "case_id": str(row['case_id']),
                        "vehicle": str(row['vehicle']),
                        "tabela": str(row['tabela']),
                        "total_visited": int(row['total_visited']),
                        "skipped_count": int(row['skipped_count']),
                        "skipped_stops": row['skipped_stops'],
                        "interpolated_count": int(row['interpolated_count'])
                    })

            dir_result = {
                "avg_fitness": float(avg_fitness),
                "fit_percentage": float(fit_pct),
                "total_cases": int(total_cases),
                "skipped_stops": skipped_counts,
                "deviant_trips": deviant_trips,
                "deviations": df_dev.to_dict('records') if isinstance(df_dev, pd.DataFrame) else []
            }
            results[dir_name] = dir_result

        if direction:
            return results.get(direction, {
                "avg_fitness": 0.0,
                "fit_percentage": 0.0,
                "total_cases": 0,
                "skipped_stops": [],
                "deviant_trips": []
            })
        return results

    @classmethod
    def analyze_performance(
        cls,
        event_log_df: pd.DataFrame,
        as_svg: bool = False
    ) -> Union[Dict[str, Any], str]:
        """
        Discover Directly-Follows Graph (DFG) performance (travel times between stops).

        Args:
            event_log_df: Event log DataFrame.
            as_svg: If True, returns SVG string representation; if False, returns JSON graph dict.

        Returns:
            SVG string or graph dictionary containing nodes, links, and start/end activities.
        """
        if event_log_df.empty:
            return "<svg></svg>" if as_svg else {"nodes": [], "links": [], "start_activities": [], "end_activities": []}

        log_pm4py = cls.format_event_log(event_log_df)
        performance_dfg, start_act, end_act = pm4py.discover_performance_dfg(log_pm4py)

        if as_svg:
            from pm4py.visualization.dfg import visualizer as dfg_visualizer
            try:
                gviz = dfg_visualizer.apply(performance_dfg, log=log_pm4py, variant=dfg_visualizer.Variants.PERFORMANCE)
                return gviz.pipe(format='svg').decode('utf-8') if isinstance(gviz.pipe(format='svg'), bytes) else gviz.pipe(format='svg')
            except Exception:
                return _get_fallback_svg(
                    "Graphviz (dot) Não Encontrado ou Falhou",
                    "Para visualizar o Directly-Follows Graph, instale o Graphviz e adicione-o ao PATH.",
                    "Dica: Execute 'choco install graphviz -y' no Windows ou 'apt install graphviz' no Linux."
                )

        nodes_set = set()
        links = []

        for (act_a, act_b), val in performance_dfg.items():
            nodes_set.add(act_a)
            nodes_set.add(act_b)
            if isinstance(val, dict):
                mean_dur = val.get('mean', 0.0)
                med_dur = val.get('median', 0.0)
                cnt = val.get('count', 0)
            else:
                mean_dur = float(val)
                med_dur = float(val)
                cnt = 0

            links.append({
                "source": act_a,
                "target": act_b,
                "mean_duration": mean_dur,
                "median_duration": med_dur,
                "count": cnt
            })

        nodes = [{"id": n, "label": n.replace("PASSAGEM_", "")} for n in nodes_set]
        start_activities = list(start_act.keys()) if isinstance(start_act, dict) else list(start_act)
        end_activities = list(end_act.keys()) if isinstance(end_act, dict) else list(end_act)

        return {
            "nodes": nodes,
            "links": links,
            "start_activities": start_activities,
            "end_activities": end_activities
        }

    @staticmethod
    def analyze_segment_performance(event_log_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate travel duration statistics across consecutive stops."""
        if event_log_df.empty:
            return pd.DataFrame()

        df = event_log_df.sort_values(by=['case:concept:name', 'stop_seq']).copy() if 'stop_seq' in event_log_df.columns else event_log_df.sort_values(by=['case:concept:name', 'time:timestamp']).copy()
        df['prev_stop'] = df.groupby('case:concept:name')['concept:name'].shift(1)
        df['prev_timestamp'] = df.groupby('case:concept:name')['time:timestamp'].shift(1)

        df_segments = df.dropna(subset=['prev_stop']).copy()
        df_segments['duration_sec'] = (pd.to_datetime(df_segments['time:timestamp']) - pd.to_datetime(df_segments['prev_timestamp'])).dt.total_seconds()
        df_segments['duration_min'] = df_segments['duration_sec'] / 60.0
        df_segments['segment_name'] = df_segments['prev_stop'].str.replace('PASSAGEM_', '') + " -> " + df_segments['concept:name'].str.replace('PASSAGEM_', '')

        segment_stats = df_segments.groupby('segment_name').agg(
            total_passages=('case:concept:name', 'count'),
            mean_time_min=('duration_min', 'mean'),
            median_time_min=('duration_min', 'median'),
            std_time_min=('duration_min', 'std'),
            max_time_min=('duration_min', 'max'),
            min_time_min=('duration_min', 'min')
        ).reset_index()

        return segment_stats.sort_values(by='mean_time_min', ascending=False)

    @staticmethod
    def analyze_schedule_delays(
        event_log_df: pd.DataFrame,
        planned_table_df: pd.DataFrame,
        date_str: str,
        static_stops_df: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Calculate departure delays against scheduled operational tables."""
        if event_log_df.empty or planned_table_df.empty:
            return pd.DataFrame()

        dt = pd.to_datetime(date_str)
        weekday = dt.weekday()
        dia_urbs = '1' if weekday < 5 else ('2' if weekday == 5 else '3')

        planned_day = planned_table_df[planned_table_df['DIA'] == dia_urbs].copy()
        if planned_day.empty:
            return pd.DataFrame()

        departures = event_log_df[event_log_df['stop_seq'] == 1].copy() if 'stop_seq' in event_log_df.columns else event_log_df.groupby('case:concept:name').first().reset_index()

        control_point_mapping: Dict[str, Any] = {}
        control_points = planned_day['PONTO'].unique() if 'PONTO' in planned_day.columns else []

        if len(control_points) == 1:
            for gps_dir in event_log_df['gps_direction'].unique() if 'gps_direction' in event_log_df.columns else ['ALL']:
                control_point_mapping[gps_dir] = control_points[0]
        elif len(control_points) >= 2 and static_stops_df is not None and not static_stops_df.empty:
            gps_dirs = event_log_df['gps_direction'].unique() if 'gps_direction' in event_log_df.columns else []
            sentido_mapping = {}
            for gps_dir in gps_dirs:
                group = event_log_df[event_log_df['gps_direction'] == gps_dir]
                if not group.empty:
                    first_concept = group['concept:name'].iloc[0]
                    sample_stop_name = first_concept.replace('PASSAGEM_', '')
                    matching = static_stops_df[static_stops_df['NOME'] == sample_stop_name]
                    if not matching.empty:
                        sentido_mapping[gps_dir] = matching['SENTIDO'].iloc[0]

            if len(sentido_mapping) >= 2:
                def normalize_txt(text: str) -> str:
                    if not text:
                        return ""
                    t = str(text).upper()
                    t = "".join(c for c in unicodedata.normalize('NFD', t) if unicodedata.category(c) != 'Mn')
                    t = re.sub(r'[^A-Z0-9\s]', ' ', t)
                    return " ".join(t.split())

                def get_word_intersection(s1: str, s2: str) -> int:
                    w1 = set(normalize_txt(s1).split())
                    w2 = set(normalize_txt(s2).split())
                    return len(w1.intersection(w2))

                dirs_list = list(sentido_mapping.keys())[:2]
                sent0, sent1 = sentido_mapping[dirs_list[0]], sentido_mapping[dirs_list[1]]
                cp0, cp1 = control_points[0], control_points[1]

                score_p1 = get_word_intersection(sent0, cp0) + get_word_intersection(sent1, cp1)
                score_p2 = get_word_intersection(sent0, cp1) + get_word_intersection(sent1, cp0)

                if score_p1 >= score_p2:
                    control_point_mapping[dirs_list[0]] = cp1
                    control_point_mapping[dirs_list[1]] = cp0
                else:
                    control_point_mapping[dirs_list[0]] = cp0
                    control_point_mapping[dirs_list[1]] = cp1

        # Fallback mapping
        for gps_dir in (event_log_df['gps_direction'].unique() if 'gps_direction' in event_log_df.columns else ['ALL']):
            if gps_dir not in control_point_mapping:
                if gps_dir == 'VOLTA':
                    control_point_mapping[gps_dir] = control_points[0] if len(control_points) > 0 else None
                else:
                    control_point_mapping[gps_dir] = control_points[1] if len(control_points) > 1 else (control_points[0] if len(control_points) > 0 else None)

        delays = []
        for idx, row in departures.iterrows():
            case_id = row['case:concept:name']
            tabela = str(row['tabela']) if 'tabela' in row else "N/A"
            actual_time = pd.to_datetime(row['time:timestamp'])
            gps_dir = row['gps_direction'] if 'gps_direction' in row else 'ALL'
            control_point = control_point_mapping.get(gps_dir)

            planned_times = planned_day[
                (planned_day['TABELA'].astype(str) == tabela) &
                (planned_day['PONTO'] == control_point)
            ].copy() if 'TABELA' in planned_day.columns and 'PONTO' in planned_day.columns else pd.DataFrame()

            if planned_times.empty:
                continue

            planned_datetimes = []
            for h in planned_times['HORA']:
                h_dt = pd.to_datetime(f"{date_str} {h}:00")
                if h.startswith('00') and actual_time.hour == 23:
                    h_dt += pd.Timedelta(days=1)
                planned_datetimes.append(h_dt)

            dists = [abs((actual_time - p_dt).total_seconds()) for p_dt in planned_datetimes]
            min_idx = int(np.argmin(dists))
            closest_planned = planned_datetimes[min_idx]

            delay_min = (actual_time - closest_planned).total_seconds() / 60.0

            if abs(delay_min) <= 45:
                delays.append({
                    'case_id': case_id,
                    'vehicle': row.get('org:resource', 'N/A'),
                    'tabela': tabela,
                    'direction': gps_dir,
                    'planned_departure': closest_planned.strftime('%H:%M'),
                    'actual_departure': actual_time.strftime('%H:%M:%S'),
                    'delay_minutes': delay_min,
                    'status': 'ATRASADO' if delay_min > 5 else ('ADIANTADO' if delay_min < -2 else 'NO HORÁRIO')
                })

        return pd.DataFrame(delays)
