"""
Trajectory Reconstruction & Event Log Synthesis Module.

Deep domain module that encapsulates data cleaning, HMM Viterbi map-matching,
monotonic PCHIP spline interpolation, spatial shape resolution, and event log building.
"""

import os
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator
import pm4py


def haversine_vectorized(lat1: Any, lon1: Any, lat2: Any, lon2: Any) -> np.ndarray:
    """Calculate the Great Circle (Haversine) distance in meters between coordinate arrays."""
    r_lat1, r_lon1, r_lat2, r_lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    dlat = r_lat2 - r_lat1
    dlon = r_lon2 - r_lon1
    a = np.sin(dlat / 2.0) ** 2 + np.cos(r_lat1) * np.cos(r_lat2) * np.sin(dlon / 2.0) ** 2
    return 6371000.0 * 2.0 * np.arcsin(np.sqrt(a))


class TrajectoryReconstructor:
    """Deep module for bus GPS telemetry cleaning, map-matching, and event log synthesis."""

    @staticmethod
    def clean_telemetry(
        df_realtime: pd.DataFrame,
        static_stops_df: Optional[pd.DataFrame] = None,
        distance_threshold: float = 5.0,
        outlier_threshold: float = 500.0
    ) -> pd.DataFrame:
        """
        Clean raw GPS telemetry points (remove nulls, REC/garage records, exact dupes, jitter, and outliers).
        """
        if df_realtime.empty:
            return df_realtime

        # 1. Remove null coordinates
        df = df_realtime.dropna(subset=['LAT', 'LON']).copy()
        if 'CODIGOLINHA' in df.columns:
            df = df[df['CODIGOLINHA'].astype(str) != 'REC']

        # 2. Remove null operational states
        if 'SITUACAO' in df.columns and 'SENT' in df.columns:
            df = df.dropna(subset=['SITUACAO', 'SENT'])

        if df.empty:
            return df

        # 3. Drop exact duplicates
        if 'COD' in df.columns and 'request_timestamp' in df.columns:
            df = df.drop_duplicates(subset=['COD', 'request_timestamp'])

        # 4. Sort and filter stationary GPS readings
        if 'request_timestamp' in df.columns and 'ts' not in df.columns:
            df['ts'] = pd.to_datetime(df['request_timestamp'])
        elif 'ts' in df.columns:
            df['ts'] = pd.to_datetime(df['ts'])

        if 'COD' in df.columns:
            df = df.sort_values(by=['COD', 'ts'])
            df['prev_lat'] = df.groupby('COD')['LAT'].shift(1)
            df['prev_lon'] = df.groupby('COD')['LON'].shift(1)
            df['dist_prev'] = haversine_vectorized(df['LAT'], df['LON'], df['prev_lat'], df['prev_lon'])
            keep_mask = df['dist_prev'].isna() | (df['dist_prev'] >= distance_threshold)
            df = df[keep_mask].drop(columns=['prev_lat', 'prev_lon', 'dist_prev'])

        # 5. Outlier distance check against static stops
        if static_stops_df is not None and not static_stops_df.empty and 'LAT' in static_stops_df.columns:
            stop_lats = static_stops_df['LAT'].dropna().values
            stop_lons = static_stops_df['LON'].dropna().values
            if len(stop_lats) > 0:
                valid_gps = []
                for _, row in df.iterrows():
                    dists = haversine_vectorized(
                        np.full_like(stop_lats, row['LAT']),
                        np.full_like(stop_lons, row['LON']),
                        stop_lats,
                        stop_lons
                    )
                    valid_gps.append(bool(dists.min() <= outlier_threshold))
                df = df[valid_gps].copy()

        return df

    @staticmethod
    def map_gps_to_shape(gps_lats: np.ndarray, gps_lons: np.ndarray, shape_lats: np.ndarray, shape_lons: np.ndarray) -> np.ndarray:
        """Project GPS points to nearest sequential shape points."""
        shape_indices = []
        for lat, lon in zip(gps_lats, gps_lons):
            dists = haversine_vectorized(
                np.full_like(shape_lats, lat),
                np.full_like(shape_lons, lon),
                shape_lats,
                shape_lons
            )
            shape_indices.append(int(dists.argmin()))
        return np.array(shape_indices, dtype=int)

    @classmethod
    def map_gps_to_shape_hmm(
        cls,
        gps_lats: np.ndarray,
        gps_lons: np.ndarray,
        shape_lats: np.ndarray,
        shape_lons: np.ndarray,
        search_radius: float = 150.0,
        sigma_z: float = 30.0,
        beta: float = 50.0
    ) -> np.ndarray:
        """
        Map-matching using Hidden Markov Model (HMM) and Viterbi algorithm.
        """
        n_gps = len(gps_lats)
        n_shape = len(shape_lats)

        if n_gps == 0 or n_shape == 0:
            return np.array([], dtype=int)

        # Cumulative distance along shape
        shape_dists = np.zeros(n_shape)
        if n_shape > 1:
            shape_dists[1:] = haversine_vectorized(
                shape_lats[:-1], shape_lons[:-1],
                shape_lats[1:], shape_lons[1:]
            )
        shape_cum_dists = np.cumsum(shape_dists)

        candidate_states = []
        for i in range(n_gps):
            lat = gps_lats[i]
            lon = gps_lons[i]
            dists = haversine_vectorized(
                np.full_like(shape_lats, lat),
                np.full_like(shape_lons, lon),
                shape_lats,
                shape_lons
            )
            cand_indices = np.where(dists <= search_radius)[0]
            if len(cand_indices) == 0:
                cand_indices = np.array([int(dists.argmin())])

            cands = [{'idx': idx, 'dist': dists[idx], 's': shape_cum_dists[idx]} for idx in cand_indices]
            candidate_states.append(cands)

        # Viterbi Trellis in log-probability space
        V = []
        ptr = []

        cands_0 = candidate_states[0]
        V_0 = np.zeros(len(cands_0))
        for j, cand in enumerate(cands_0):
            V_0[j] = -0.5 * ((cand['dist'] / sigma_z) ** 2)
        V.append(V_0)
        ptr.append(np.zeros(len(cands_0), dtype=int))

        for i in range(1, n_gps):
            cands_prev = candidate_states[i - 1]
            cands_curr = candidate_states[i]

            dist_gps = haversine_vectorized(
                np.array([gps_lats[i - 1]]), np.array([gps_lons[i - 1]]),
                np.array([gps_lats[i]]), np.array([gps_lons[i]])
            )[0]

            V_curr = np.zeros(len(cands_curr))
            ptr_curr = np.zeros(len(cands_curr), dtype=int)

            for j, cand_curr in enumerate(cands_curr):
                best_log_prob = -np.inf
                best_prev_idx = 0

                for k, cand_prev in enumerate(cands_prev):
                    delta_shape = cand_curr['s'] - cand_prev['s']
                    if delta_shape < -20.0:
                        log_trans = -np.inf
                    else:
                        delta_shape_clamped = max(0.0, delta_shape)
                        log_trans = -abs(dist_gps - delta_shape_clamped) / beta

                    log_prob = V[-1][k] + log_trans
                    if log_prob > best_log_prob:
                        best_log_prob = log_prob
                        best_prev_idx = k

                if best_log_prob == -np.inf:
                    best_log_prob = 0.0
                    prev_s_vals = np.array([c['s'] for c in cands_prev])
                    best_prev_idx = int(np.abs(prev_s_vals - cand_curr['s']).argmin())

                log_emission = -0.5 * ((cand_curr['dist'] / sigma_z) ** 2)
                V_curr[j] = log_emission + best_log_prob
                ptr_curr[j] = best_prev_idx

            V.append(V_curr)
            ptr.append(ptr_curr)

        # Backtracking
        optimal_indices = np.zeros(n_gps, dtype=int)
        best_last_state = int(np.argmax(V[-1]))
        optimal_indices[-1] = candidate_states[-1][best_last_state]['idx']

        curr_state_idx = best_last_state
        for i in range(n_gps - 1, 0, -1):
            prev_state_idx = ptr[i][curr_state_idx]
            optimal_indices[i - 1] = candidate_states[i - 1][prev_state_idx]['idx']
            curr_state_idx = prev_state_idx

        return optimal_indices

    @classmethod
    def resolve_route_geometry(
        cls,
        static_data: Dict[str, pd.DataFrame],
        direction: str = "VOLTA",
        trip_sample_df: Optional[pd.DataFrame] = None
    ) -> Tuple[Optional[str], pd.DataFrame, pd.DataFrame]:
        """
        Dynamically resolves the static route direction string, filtered stops, and closest physical shape geometry.

        Returns:
            Tuple of (sentido_static_string, stops_filtered_df, shape_filtered_df)
        """
        stops_df = static_data.get('pontos', pd.DataFrame())
        shape_df = static_data.get('shape', pd.DataFrame())

        if stops_df.empty:
            return None, pd.DataFrame(), pd.DataFrame()

        sentido_static = None
        sentidos = stops_df['SENTIDO'].dropna().unique()

        if trip_sample_df is not None and not trip_sample_df.empty and 'LAT' in trip_sample_df.columns and len(sentidos) > 1:
            trip_start_lat = trip_sample_df['LAT'].iloc[0]
            trip_start_lon = trip_sample_df['LON'].iloc[0]
            best_sentido = None
            min_dist = float('inf')
            for sent in sentidos:
                stops = stops_df[stops_df['SENTIDO'] == sent].sort_values('SEQ')
                if stops.empty:
                    continue
                d = haversine_vectorized(
                    np.array([trip_start_lat]), np.array([trip_start_lon]),
                    np.array([stops['LAT'].iloc[0]]), np.array([stops['LON'].iloc[0]])
                )[0]
                if d < min_dist:
                    min_dist = d
                    best_sentido = sent
            sentido_static = best_sentido
        elif trip_sample_df is not None and not trip_sample_df.empty and 'concept:name' in trip_sample_df.columns and len(sentidos) > 1:
            sample_stop_name = trip_sample_df['concept:name'].iloc[0].replace('PASSAGEM_', '')
            matching_stops = stops_df[stops_df['NOME'] == sample_stop_name]
            if not matching_stops.empty:
                sentido_static = matching_stops['SENTIDO'].iloc[0]

        if not sentido_static:
            if len(sentidos) == 1:
                sentido_static = sentidos[0]
            elif len(sentidos) > 1:
                sentido_static = sentidos[0] if (direction == 'VOLTA' or len(sentidos) == 1) else sentidos[1]

        stops_filtered = stops_df[stops_df['SENTIDO'] == sentido_static].sort_values('SEQ').copy()

        # Find best shape geometry
        shape_filtered = pd.DataFrame()
        if not shape_df.empty and 'SHP' in shape_df.columns:
            shps = shape_df['SHP'].dropna().unique()
            if len(shps) == 1:
                shape_filtered = shape_df[shape_df['SHP'] == shps[0]].copy()
            elif len(shps) > 1 and not stops_filtered.empty:
                stop_lats = stops_filtered['LAT'].dropna().values
                stop_lons = stops_filtered['LON'].dropna().values
                best_shp = None
                min_avg_dist = float('inf')
                for shp in shps:
                    shp_pts = shape_df[shape_df['SHP'] == shp]
                    if shp_pts.empty:
                        continue
                    shp_lats = shp_pts['LAT'].values
                    shp_lons = shp_pts['LON'].values
                    dists_list = [
                        haversine_vectorized(
                            np.full_like(shp_lats, s_lat), np.full_like(shp_lons, s_lon),
                            shp_lats, shp_lons
                        ).min()
                        for s_lat, s_lon in zip(stop_lats, stop_lons)
                    ]
                    avg_dist = float(np.mean(dists_list)) if dists_list else float('inf')
                    if avg_dist < min_avg_dist:
                        min_avg_dist = avg_dist
                        best_shp = shp
                if best_shp:
                    shape_filtered = shape_df[shape_df['SHP'] == best_shp].copy()
            else:
                shape_filtered = shape_df.copy()

        # Project stops onto shape
        if not shape_filtered.empty and not stops_filtered.empty:
            shape_lats = shape_filtered['LAT'].values
            shape_lons = shape_filtered['LON'].values
            stop_shape_idx = cls.map_gps_to_shape(stops_filtered['LAT'].values, stops_filtered['LON'].values, shape_lats, shape_lons)
            stop_shape_idx = np.maximum.accumulate(stop_shape_idx)
            stops_filtered['shape_idx'] = stop_shape_idx

        return sentido_static, stops_filtered, shape_filtered

    @classmethod
    def match_trip(
        cls,
        trip_df: pd.DataFrame,
        static_data: Dict[str, pd.DataFrame],
        line_code: Optional[str] = None,
        enforce_monotonicity: bool = True
    ) -> pd.DataFrame:
        """
        Reconstruct stop passage events and timestamps for a single trip via HMM matching and PCHIP spline.
        """
        if trip_df.empty:
            return pd.DataFrame()

        gps_dir = trip_df['SENT'].iloc[0] if 'SENT' in trip_df.columns else "VOLTA"
        sentido_static, stops_filtered, shape_filtered = cls.resolve_route_geometry(static_data, direction=gps_dir, trip_sample_df=trip_df)

        if stops_filtered.empty:
            return pd.DataFrame()

        if shape_filtered.empty:
            shape_filtered = stops_filtered.rename(columns={'NOME': 'SHP'}).copy()

        shape_lats = shape_filtered['LAT'].values
        shape_lons = shape_filtered['LON'].values

        # Cumulative distance along shape
        shape_dists = np.zeros(len(shape_lats))
        if len(shape_lats) > 1:
            shape_dists[1:] = haversine_vectorized(shape_lats[:-1], shape_lons[:-1], shape_lats[1:], shape_lons[1:])
        shape_cum_dists = np.cumsum(shape_dists)

        trip_df = trip_df.sort_values('ts').copy()
        gps_lats = trip_df['LAT'].values
        gps_lons = trip_df['LON'].values
        gps_ts = trip_df['ts'].values

        gps_shape_idx = cls.map_gps_to_shape_hmm(gps_lats, gps_lons, shape_lats, shape_lons)
        gps_shape_idx = np.maximum.accumulate(gps_shape_idx)
        trip_df['shape_idx'] = gps_shape_idx

        gps_cum_dists = shape_cum_dists[gps_shape_idx]

        stop_lats = stops_filtered['LAT'].values
        stop_lons = stops_filtered['LON'].values
        stop_shape_idx = cls.map_gps_to_shape(stop_lats, stop_lons, shape_lats, shape_lons)
        stop_shape_idx = np.maximum.accumulate(stop_shape_idx)
        stops_filtered['shape_idx'] = stop_shape_idx
        stops_filtered['cum_dist'] = shape_cum_dists[stop_shape_idx]

        # Unix timestamps in seconds
        gps_ts_floats = pd.to_datetime(gps_ts).astype('datetime64[ns]').view('int64') / 1e9

        df_pts = pd.DataFrame({'s': gps_cum_dists, 't': gps_ts_floats})
        df_unique = df_pts.groupby('s')['t'].mean().reset_index().sort_values('s')

        s_unique = df_unique['s'].values
        t_unique = df_unique['t'].values

        if len(s_unique) < 2:
            pchip = lambda s_val: t_unique[0] if len(t_unique) > 0 else 0.0
        else:
            pchip = PchipInterpolator(s_unique, t_unique)

        s_min, s_max = s_unique[0], s_unique[-1]
        t_min, t_max = t_unique[0], t_unique[-1]

        events = []
        for idx, stop in stops_filtered.iterrows():
            dists = haversine_vectorized(
                np.full_like(gps_lats, stop['LAT']),
                np.full_like(gps_lons, stop['LON']),
                gps_lats,
                gps_lons
            )
            min_dist = dists.min() if len(dists) > 0 else 0.0
            s_stop = stop['cum_dist']

            # PCHIP Interpolation / Extrapolation
            if s_min <= s_stop <= s_max:
                t_stop = float(pchip(s_stop))
            elif s_stop < s_min:
                speed = (s_unique[1] - s_unique[0]) / (t_unique[1] - t_unique[0]) if (len(s_unique) >= 2 and (t_unique[1] - t_unique[0]) > 0) else 1.0
                t_stop = t_min - (s_min - s_stop) / speed if speed > 0 else t_min
            else:
                speed = (s_unique[-1] - s_unique[-2]) / (t_unique[-1] - t_unique[-2]) if (len(s_unique) >= 2 and (t_unique[-1] - t_unique[-2]) > 0) else 1.0
                t_stop = t_max + (s_stop - s_max) / speed if speed > 0 else t_max

            t_stop_ts = pd.to_datetime(t_stop, unit='s')
            if hasattr(trip_df['ts'].dt, 'tz') and trip_df['ts'].dt.tz is not None:
                t_stop_ts = t_stop_ts.tz_localize('UTC').tz_convert(trip_df['ts'].dt.tz)

            events.append({
                'stop_seq': stop['SEQ'],
                'stop_num': stop.get('NUM', str(stop['SEQ'])),
                'stop_name': stop['NOME'],
                'event_type': 'PASSAGE',
                'timestamp': t_stop_ts,
                'distance': min_dist,
                'interpolated': bool(min_dist > 100.0),
                'vehicle': trip_df['COD'].iloc[0] if 'COD' in trip_df else "N/A",
                'tabela': trip_df['TABELA'].iloc[0] if 'TABELA' in trip_df else "N/A",
                'gps_direction': gps_dir,
                'cum_dist': s_stop
            })

        events_df = pd.DataFrame(events)
        if not events_df.empty and enforce_monotonicity:
            events_df = events_df.sort_values('stop_seq').copy()
            last_ts = None
            last_s = None
            new_timestamps = []
            for _, row in events_df.iterrows():
                ts = row['timestamp']
                s_val = row.get('cum_dist', 0.0)
                if last_ts is not None:
                    d_space = s_val - last_s
                    min_seconds = max(5.0, d_space / 22.2) if d_space > 0 else 5.0
                    min_ts = last_ts + pd.Timedelta(seconds=min_seconds)
                    if ts < min_ts:
                        ts = min_ts
                new_timestamps.append(ts)
                last_ts = ts
                last_s = s_val
            events_df['timestamp'] = new_timestamps

        return events_df

    @classmethod
    def reconstruct_event_log(
        cls,
        realtime_df: pd.DataFrame,
        static_data: Dict[str, pd.DataFrame],
        line_code: str,
        output_dir: Optional[str] = None,
        date_range_tag: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Reconstruct a complete Process Mining event log from raw telemetry and static schedule data.
        """
        if realtime_df.empty or static_data.get('pontos', pd.DataFrame()).empty:
            return pd.DataFrame()

        df_clean = cls.clean_telemetry(realtime_df, static_data.get('pontos'))
        if df_clean.empty:
            return pd.DataFrame()

        df_clean['data_str'] = df_clean['ts'].dt.strftime('%Y-%m-%d')
        all_events = []

        for (vehicle_cod, day_str), group in df_clean.groupby(['COD', 'data_str']):
            group = group.sort_values('ts')
            group['time_diff'] = group['ts'].diff().dt.total_seconds() / 60.0
            group['sent_change'] = (group['SENT'] != group['SENT'].shift(1)) | (group['time_diff'] > 10.0)
            group['trip_num'] = group['sent_change'].cumsum()

            for trip_num, trip_group in group.groupby('trip_num'):
                if len(trip_group) < 3:
                    continue

                trip_events = cls.match_trip(trip_group, static_data, line_code)
                if not trip_events.empty:
                    if trip_events['interpolated'].mean() > 0.90:
                        continue
                    tab = trip_group['TABELA'].iloc[0] if 'TABELA' in trip_group else "1"
                    case_id = f"{vehicle_cod}_{line_code}_{tab}_{day_str}_V{trip_num}"
                    trip_events['case:concept:name'] = case_id
                    all_events.append(trip_events)

        if not all_events:
            return pd.DataFrame()

        df_log = pd.concat(all_events, ignore_index=True)
        df_log = df_log.rename(columns={
            'stop_name': 'concept:name',
            'timestamp': 'time:timestamp',
            'vehicle': 'org:resource'
        })
        df_log['concept:name'] = 'PASSAGEM_' + df_log['concept:name'].astype(str)
        df_log['time:timestamp'] = pd.to_datetime(df_log['time:timestamp'])
        df_log = df_log.sort_values(by=['case:concept:name', 'stop_seq'])

        # Save outputs if directory is given
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            tag = date_range_tag or df_clean['data_str'].iloc[0]
            csv_path = os.path.join(output_dir, f"event_log_{line_code}_{tag}.csv")
            df_log.to_csv(csv_path, index=False, encoding='utf-8')

            xes_path = os.path.join(output_dir, f"event_log_{line_code}_{tag}.xes")
            try:
                log_pm4py = pm4py.format_dataframe(df_log, case_id='case:concept:name', activity_key='concept:name', timestamp_key='time:timestamp')
                pm4py.write_xes(log_pm4py, xes_path)
            except Exception:
                pass

        return df_log

    @staticmethod
    def calculate_segment_speeds(
        df_log_dir: pd.DataFrame,
        shape_filtered: pd.DataFrame,
        stops_filtered: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Aggregate operational bus speeds and congestion colors between consecutive physical stops.
        """
        segments = []
        if df_log_dir.empty or shape_filtered.empty or stops_filtered.empty:
            return segments

        stops_records = stops_filtered.to_dict('records')
        for i in range(len(stops_records) - 1):
            st1 = stops_records[i]
            st2 = stops_records[i + 1]

            idx1 = st1.get('shape_idx', 0)
            idx2 = st2.get('shape_idx', 0)
            if idx1 > idx2:
                idx1, idx2 = idx2, idx1

            seg_df = shape_filtered.iloc[idx1:idx2 + 1]
            seg_coords = list(zip(seg_df['LAT'].tolist(), seg_df['LON'].tolist()))

            dist = 0.0
            if len(seg_coords) > 1:
                lats = seg_df['LAT'].values
                lons = seg_df['LON'].values
                dists = haversine_vectorized(lats[:-1], lons[:-1], lats[1:], lons[1:])
                dist = float(dists.sum())

            stop_name_1 = f"PASSAGEM_{st1['NOME']}"
            stop_name_2 = f"PASSAGEM_{st2['NOME']}"
            cases_passed = df_log_dir[df_log_dir['concept:name'].isin([stop_name_1, stop_name_2])]

            speeds_list = []
            if not cases_passed.empty:
                for _, group in cases_passed.groupby('case:concept:name'):
                    if len(group) == 2:
                        g_sorted = group.sort_values('stop_seq') if 'stop_seq' in group else group
                        t1 = pd.to_datetime(g_sorted['time:timestamp'].iloc[0])
                        t2 = pd.to_datetime(g_sorted['time:timestamp'].iloc[1])
                        duration_sec = (t2 - t1).total_seconds()
                        if duration_sec > 0:
                            speeds_list.append((dist / duration_sec) * 3.6)

            avg_speed = float(np.median(speeds_list)) if speeds_list else 25.0
            if avg_speed < 12.0:
                color = "#ff4b4b"
            elif avg_speed < 20.0:
                color = "#f59e0b"
            else:
                color = "#ffffff"

            segments.append({
                "from_stop": st1['NOME'],
                "to_stop": st2['NOME'],
                "coords": seg_coords,
                "speed": avg_speed,
                "color": color
            })

        return segments

    @staticmethod
    def build_replay_trips(
        df_log_dir: pd.DataFrame,
        stops_filtered: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Build vehicle trajectory timestamp replay points for geospatial frontend animation.
        """
        replay_trips = []
        if df_log_dir.empty or stops_filtered.empty:
            return replay_trips

        for cid in df_log_dir['case:concept:name'].unique():
            c_events = df_log_dir[df_log_dir['case:concept:name'] == cid].sort_values('stop_seq')
            c_merged = pd.merge(
                c_events[['stop_seq', 'time:timestamp']],
                stops_filtered[['SEQ', 'NOME', 'LAT', 'LON']],
                left_on='stop_seq',
                right_on='SEQ',
                how='inner'
            ).sort_values('stop_seq')

            path_pts = []
            for _, row in c_merged.iterrows():
                ts_str = row['time:timestamp'].isoformat() if hasattr(row['time:timestamp'], "isoformat") else str(row['time:timestamp'])
                path_pts.append({
                    "time": ts_str,
                    "lat": float(row['LAT']),
                    "lon": float(row['LON']),
                    "stop_name": str(row['NOME'])
                })

            if len(path_pts) > 1:
                veh = str(c_events['org:resource'].iloc[0]) if 'org:resource' in c_events else "N/A"
                replay_trips.append({
                    "case_id": cid,
                    "vehicle": veh,
                    "path": path_pts
                })

        return replay_trips
