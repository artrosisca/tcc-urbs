import os
import pm4py
import pandas as pd
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.petri_net.utils import petri_utils

def create_normative_petri_net(stops_df):
    """
    Cria uma Rede de Petri normativa contendo a sequência estrita de passagens pelos pontos de parada.
    """
    net = PetriNet("Normative_Model")
    
    # Ordenar pontos por SEQ
    stops = stops_df.sort_values(by='SEQ')
    
    # Criar lugar inicial
    prev_place = PetriNet.Place("place_start")
    net.places.add(prev_place)
    
    initial_marking = Marking()
    initial_marking[prev_place] = 1
    
    # Criar transição e lugar para cada ponto de parada
    for idx, row in stops.iterrows():
        act_name = f"PASSAGEM_{row['NOME']}"
        transition = PetriNet.Transition(f"trans_{row['SEQ']}", act_name)
        net.transitions.add(transition)
        
        next_place = PetriNet.Place(f"place_{row['SEQ']}")
        net.places.add(next_place)
        
        # Conectar prev_place -> transition -> next_place
        petri_utils.add_arc_from_to(prev_place, transition, net)
        petri_utils.add_arc_from_to(transition, next_place, net)
        
        prev_place = next_place
        
    final_marking = Marking()
    final_marking[prev_place] = 1
    
    return net, initial_marking, final_marking

def analyze_conformance(event_log_df, static_stops_df):
    """
    Analisa a conformidade do log de eventos contra o modelo planejado.
    
    Args:
        event_log_df (pd.DataFrame): Log de eventos
        static_stops_df (pd.DataFrame): Pontos de parada planejados
        
    Returns:
        dict: Estatísticas de conformidade e lista de desvios por viagem
    """
    if event_log_df.empty or static_stops_df.empty:
        return {}
        
    results = {}
    
    # Separar análise por sentido do GPS
    for direction, group in event_log_df.groupby('gps_direction'):
        direction_results = {}
        
        # Resolver dinamicamente o sentido estático correspondente à direção do GPS (VOLTA/IDA)
        sentido_static = None
        if not group.empty:
            first_concept = group['concept:name'].iloc[0]
            sample_stop_name = first_concept.replace('PASSAGEM_', '')
            matching_stops = static_stops_df[static_stops_df['NOME'] == sample_stop_name]
            if not matching_stops.empty:
                sentido_static = matching_stops['SENTIDO'].iloc[0]
                
        if not sentido_static:
            sentidos = static_stops_df['SENTIDO'].unique()
            if len(sentidos) > 0:
                if direction == 'VOLTA' or len(sentidos) == 1:
                    sentido_static = sentidos[0]
                else:
                    sentido_static = sentidos[1]
                    
        if not sentido_static:
            continue
            
        stops_direction = static_stops_df[static_stops_df['SENTIDO'] == sentido_static].sort_values('SEQ').copy()
        if stops_direction.empty:
            continue
            
        # 1. Criar modelo normativo
        net, initial_marking, final_marking = create_normative_petri_net(stops_direction)
        
        # 2. Formatar log de eventos para PM4Py
        log = pm4py.format_dataframe(
            group,
            case_id='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )
        
        # 3. Rodar Token-based Replay
        try:
            replayed_traces = pm4py.conformance_diagnostics_token_based_replay(log, net, initial_marking, final_marking)
            
            # Calcular métricas agregadas
            fitnesses = [t['trace_fitness'] for t in replayed_traces]
            avg_fitness = sum(fitnesses) / len(fitnesses) if fitnesses else 0.0
            fit_count = sum(1 for t in replayed_traces if t['trace_is_fit'])
            fit_pct = (fit_count / len(replayed_traces) * 100) if replayed_traces else 0.0
            
            direction_results['avg_fitness'] = avg_fitness
            direction_results['fit_percentage'] = fit_pct
            direction_results['total_cases'] = len(replayed_traces)
        except Exception as e:
            print(f"Erro no Token-based Replay para {direction}: {e}")
            continue
            
        # 4. Análise heurística detalhada de desvios (Skipped stops)
        # Mais intuitiva para relatórios do TCC do que métricas formais do Petri net
        planned_stops_set = set('PASSAGEM_' + stops_direction['NOME'].astype(str))
        planned_stops_list = ['PASSAGEM_' + n for n in stops_direction['NOME'].tolist()]
        
        deviations = []
        for case_id, case_group in group.groupby('case:concept:name'):
            case_group = case_group.sort_values('stop_seq')
            visited = case_group['concept:name'].tolist()
            
            # Identificar quais pontos planejados não foram visitados (desconsiderando se foi interpolado)
            # Se foi interpolado (interpolated == True), o GPS falhou em capturar
            # Se não foi nem interpolado nem visitado (não está na lista), foi pulado
            skipped = []
            interpolated_count = 0
            for stop in planned_stops_list:
                stop_rows = case_group[case_group['concept:name'] == stop]
                if stop_rows.empty:
                    skipped.append(stop.replace('PASSAGEM_', ''))
                elif stop_rows['interpolated'].iloc[0]:
                    interpolated_count += 1
                    
            deviations.append({
                'case_id': case_id,
                'vehicle': case_group['org:resource'].iloc[0],
                'tabela': case_group['tabela'].iloc[0],
                'total_planned': len(planned_stops_list),
                'total_visited': len(visited),
                'skipped_count': len(skipped),
                'skipped_stops': skipped,
                'interpolated_count': interpolated_count
            })
            
        df_deviations = pd.DataFrame(deviations)
        direction_results['deviations'] = df_deviations
        
        results[direction] = direction_results
        
    return results

if __name__ == "__main__":
    from src.etl.load_c3sl import load_static_data
    
    # Teste rápido
    csv_path = "data/dados_processados/event_log_541_2025-10-24_2025-10-24.csv"
    if os.path.exists(csv_path):
        print(f"Lendo log de testes de: {csv_path}")
        df = pd.read_csv(csv_path)
        df['time:timestamp'] = pd.to_datetime(df['time:timestamp'])
        
        static = load_static_data("2025-10-24", "541")
        
        res = analyze_conformance(df, static['pontos'])
        for direction, data in res.items():
            print(f"\n=== RESULTADOS CONFORMIDADE SENTIDO: {direction} ===")
            print(f"Total de viagens: {data['total_cases']}")
            print(f"Fitness Médio: {data['avg_fitness']:.3f}")
            print(f"Percentual de viagens 100% em conformidade: {data['fit_percentage']:.1f}%")
            
            df_dev = data['deviations']
            print(f"Média de pontos pulados por viagem: {df_dev['skipped_count'].mean():.1f}")
            print(f"Média de pontos interpolados (falha GPS) por viagem: {df_dev['interpolated_count'].mean():.1f}")
            
            # Mostrar os casos com maior desvio
            top_deviant = df_dev.sort_values(by='skipped_count', ascending=False).head(3)
            print("\nTop 3 viagens com mais desvios (pontos pulados):")
            for _, row in top_deviant.iterrows():
                print(f"  Caso: {row['case_id']} | Pulou {row['skipped_count']} pontos: {row['skipped_stops']}")
    else:
        print("Execute o ETL primeiro para rodar este teste.")
