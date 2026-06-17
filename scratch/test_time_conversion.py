import os
import sys
import pandas as pd
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.etl.load_c3sl import load_static_data
from src.etl.load_realtime import load_realtime_data
from src.etl.clean_data import clean_gps_data

line_code = "541"
date_str = "2025-10-24"
static_data = load_static_data(date_str, line_code)
df_realtime = load_realtime_data(line_code, date_str, date_str)
df_clean = clean_gps_data(df_realtime, static_data['pontos'])

df_clean['data_str'] = df_clean['ts'].dt.strftime('%Y-%m-%d')
groups = list(df_clean.groupby(['COD', 'data_str']))
trip_df = None
for (vehicle_cod, day_str), group in groups:
    group = group.sort_values('ts')
    group['time_diff'] = group['ts'].diff().dt.total_seconds() / 60.0
    group['sent_change'] = (group['SENT'] != group['SENT'].shift(1)) | (group['time_diff'] > 10.0)
    group['trip_num'] = group['sent_change'].cumsum()
    for trip_num, trip_group in group.groupby('trip_num'):
        if len(trip_group) >= 15:
            duration = (trip_group['ts'].max() - trip_group['ts'].min()).total_seconds()
            if duration > 300:
                trip_df = trip_group.sort_values('ts').copy()
                break
    if trip_df is not None:
        break

gps_ts = trip_df['ts'].values
print("gps_ts type:", type(gps_ts))
print("gps_ts dtype:", gps_ts.dtype)
print("gps_ts first:", gps_ts[0])

# Como é convertido em match_trip_events
gps_ts_floats = pd.to_datetime(gps_ts).astype('datetime64[ns]').view('int64') / 1e9
print("gps_ts_floats first:", gps_ts_floats[0])
print("gps_ts_floats last:", gps_ts_floats[-1])
print("gps_ts_floats diff (seconds):", gps_ts_floats[-1] - gps_ts_floats[0])

# Conversão de volta
t_back = pd.to_datetime(gps_ts_floats[0], unit='s')
print("t_back:", t_back)
