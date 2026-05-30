import pm4py
import pandas as pd
from src.mining.conformance import create_normative_petri_net
from src.etl.load_c3sl import load_static_data

df = pd.read_csv('dados_processados/event_log_541_2025-10-24_2025-10-24.csv')
df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])

# Filtrar para VOLTA
group = df[df['gps_direction'] == 'VOLTA']
log = pm4py.format_dataframe(
    group, 
    case_id='case:concept:name', 
    activity_key='concept:name', 
    timestamp_key='time:timestamp'
)

static = load_static_data('2025-10-24', '541')
stops_direction = static['pontos'][static['pontos']['SENTIDO'] == 'Bairro Novo "A"']

net, im, fm = create_normative_petri_net(stops_direction)

replayed = pm4py.conformance_diagnostics_token_based_replay(log, net, im, fm)
print("Replayed length:", len(replayed))
print("First item keys:", list(replayed[0].keys()))
print("First item values:")
for k, v in replayed[0].items():
    print(f"  {k}: {v}")
