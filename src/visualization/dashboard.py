import os
import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import pm4py
from pm4py.visualization.dfg import visualizer as dfg_visualizer
from pm4py.visualization.petri_net import visualizer as pn_visualizer
from pm4py.visualization.heuristics_net import visualizer as hn_visualizer

from src.etl.load_c3sl import load_static_data

@st.cache_data(show_spinner="Calculando linhas ativas em ambos os regimes...")
def get_common_lines(data_dir="dados_em_tempo_real_2026"):
    # Carregar do dia 2025-10-24 (Regime A)
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
                    
    # Carregar do dia 2025-12-02 (Regime B)
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
from src.etl.build_event_log import build_event_log
from src.mining.discovery import run_process_discovery
from src.mining.conformance import analyze_conformance
from src.mining.performance import analyze_segment_performance, analyze_schedule_delays

# Configuração da página do Streamlit
st.set_page_config(
    page_title="Process Mining URBS — Transporte Público de Curitiba",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo customizado CSS para estética premium
st.markdown("""
<style>
    .main {
        background-color: #0f111a;
        color: #e6e6e6;
        font-family: 'Inter', sans-serif;
    }
    .stApp {
        background-color: #0f111a;
    }
    h1, h2, h3 {
        color: #ffffff;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    div[data-testid="stSidebar"] {
        background-color: #161925;
        border-right: 1px solid #23283c;
    }
    .stButton>button {
        background: linear-gradient(135deg, #ff4b4b 0%, #ff758c 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 75, 75, 0.4);
    }
    .metric-card {
        background-color: #1a1e2f;
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #262c45;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.15);
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #ff4b4b;
        margin-bottom: 0.2rem;
    }
    .metric-label {
        font-size: 0.9rem;
        color: #a0aec0;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# Título do App
st.title("🚌 Mineração de Processos no Transporte Público")
st.caption("Aplicação de Map Matching, Interpolação Temporal e Process Mining sobre dados de GPS da URBS de Curitiba")

# ----------------- SIDEBAR -----------------
st.sidebar.header("🛠️ Configurações de Análise")

# Obter linhas em comum dinamicamente
common_lines = get_common_lines()

# Linha selecionável (apenas as que existem em ambos os regimes)
linha_selecionada = st.sidebar.selectbox(
    "Selecione a Linha de Ônibus:",
    options=common_lines,
    index=common_lines.index("541") if "541" in common_lines else 0,
    help="Exibindo apenas as linhas ativas em ambos os regimes (Outubro e Dezembro)."
)

st.sidebar.markdown("---")
st.sidebar.subheader("📅 Período de Análise")
st.sidebar.info("Recomenda-se comparar as duas semanas sob regimes diferentes:")

# Opções rápidas de períodos de acordo com os regimes descobertos
opcao_regime = st.sidebar.radio(
    "Selecione o Período / Regime:",
    options=[
        "Regime A: Coleta de 2 min (Outubro/2025)",
        "Regime B: Coleta de 20s (Dezembro/2025)",
        "Personalizado"
    ],
    index=1
)

if opcao_regime == "Regime A: Coleta de 2 min (Outubro/2025)":
    data_inicio = "2025-10-24"
    data_fim = "2025-10-30"
elif opcao_regime == "Regime B: Coleta de 20s (Dezembro/2025)":
    data_inicio = "2025-12-02"
    data_fim = "2025-12-08"
else:
    col_d1, col_d2 = st.sidebar.columns(2)
    data_inicio = col_d1.date_input("Início", pd.to_datetime("2025-10-24")).strftime("%Y-%m-%d")
    data_fim = col_d2.date_input("Fim", pd.to_datetime("2025-10-30")).strftime("%Y-%m-%d")

# Raio do geofencing
raio_geofence = st.sidebar.slider(
    "Raio de Geofencing (metros):",
    min_value=50,
    max_value=200,
    value=100,
    step=10,
    help="Raio recomendado de 100m cobre 88% das leituras do GPS."
)

st.sidebar.markdown("---")
executar = st.sidebar.button("🚀 Executar Process Mining")

# ----------------- CARREGAMENTO / PROCESSAMENTO -----------------
# Cache para evitar re-processar dados idênticos em cliques
@st.cache_data(show_spinner="Consolidando dados e construindo Event Log...")
def process_data_pipeline(line, start_d, end_d, geofence_r):
    # Gerar logs
    df_log = build_event_log(line, start_d, end_d, output_dir="dados_processados")
    static_data = load_static_data(start_d, line)
    return df_log, static_data

# Iniciar estado na sessão
if 'event_log' not in st.session_state:
    st.session_state['event_log'] = None
    st.session_state['static_data'] = None
    st.session_state['line_code'] = None
    st.session_state['start_date'] = None
    st.session_state['end_date'] = None

if executar:
    with st.spinner("Processando dados (ETL, Geofencing, Interpolação)..."):
        df_log, static_data = process_data_pipeline(linha_selecionada, data_inicio, data_fim, raio_geofence)
        
        if not df_log.empty:
            st.session_state['event_log'] = df_log
            st.session_state['static_data'] = static_data
            st.session_state['line_code'] = linha_selecionada
            st.session_state['start_date'] = data_inicio
            st.session_state['end_date'] = data_fim
            st.success("Log de Eventos carregado e processado com sucesso!")
        else:
            st.error("Erro: Não foi possível obter dados para as datas selecionadas.")

# Mostrar dashboard apenas se houver dados carregados
if st.session_state['event_log'] is not None:
    df_log = st.session_state['event_log']
    static_data = st.session_state['static_data']
    line_code = st.session_state['line_code']
    start_date = st.session_state['start_date']
    end_date = st.session_state['end_date']
    
    # ----------------- TABS DO DASHBOARD -----------------
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Visão Geral & Mapa", 
        "🕸️ Grafos Descobertos (PM4Py)", 
        "📊 Estatísticas DFG",
        "🎯 Conformidade", 
        "⚡ Desempenho & Gargalos"
    ])
    
    # ================= TAB 1: VISÃO GERAL & MAPA =================
    with tab1:
        st.header("📊 Resumo da Operação")
        
        # Cards de métricas premium
        col1, col2, col3, col4 = st.columns(4)
        
        total_viagens = df_log['case:concept:name'].nunique()
        total_eventos = len(df_log)
        veiculos_ativos = df_log['org:resource'].nunique()
        taxa_interpolacao = (df_log['interpolated'].sum() / len(df_log)) * 100
        
        with col1:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{total_viagens}</div><div class="metric-label">Viagens Mapeadas</div></div>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{total_eventos}</div><div class="metric-label">Total de Eventos</div></div>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{veiculos_ativos}</div><div class="metric-label">Veículos Únicos</div></div>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{taxa_interpolacao:.1f}%</div><div class="metric-label">Taxa de Interpolação (Gaps)</div></div>', unsafe_allow_html=True)
            
        st.markdown("<br/>", unsafe_allow_html=True)
        
        # Seção do Mapa
        st.subheader("🗺️ Mapa Interativo da Rota e Paradas")
        direction_map = st.selectbox("Selecione o Sentido para visualização:", ["VOLTA", "IDA"])
        
        stops_df = static_data['pontos']
        shape_df = static_data['shape']
        
        # Resolver dinamicamente o sentido_static associado à direção selecionada (VOLTA/IDA)
        df_log_dir = df_log[df_log['gps_direction'] == direction_map]
        sentido_static = None
        if not df_log_dir.empty:
            sample_stop_name = df_log_dir['concept:name'].iloc[0].replace('PASSAGEM_', '')
            matching_stops = stops_df[stops_df['NOME'] == sample_stop_name]
            if not matching_stops.empty:
                sentido_static = matching_stops['SENTIDO'].iloc[0]
        
        if not sentido_static and not stops_df.empty:
            sentido_static = stops_df['SENTIDO'].unique()[0]
            
        stops_filtered = stops_df[stops_df['SENTIDO'] == sentido_static].sort_values('SEQ').copy()
        
        # Resolver dinamicamente a rota (shape) mais próxima para o sentido_static resolvido
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
                        
        if not stops_filtered.empty:
            center_lat = stops_filtered['LAT'].mean()
            center_lon = stops_filtered['LON'].mean()
            
            m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="cartodbpositron")
            
            # Desenhar o shape da rota (se disponível)
            if not shape_filtered.empty:
                shape_coords = list(zip(shape_filtered['LAT'], shape_filtered['LON']))
                folium.PolyLine(
                    shape_coords, 
                    color="#4A90E2", 
                    weight=5, 
                    opacity=0.8,
                    tooltip=f"Shape Rota {direction_map}"
                ).add_to(m)
                
            # Desenhar as paradas
            for idx, stop in stops_filtered.iterrows():
                # Obter a quantidade de passagens por essa parada no event log
                stop_name_log = f"PASSAGEM_{stop['NOME']}"
                passages = len(df_log[(df_log['concept:name'] == stop_name_log) & (df_log['gps_direction'] == direction_map)])
                
                folium.CircleMarker(
                    location=[stop['LAT'], stop['LON']],
                    radius=7,
                    color="#ff4b4b",
                    fill=True,
                    fill_color="#ff758c",
                    fill_opacity=0.9,
                    popup=f"<b>Seq:</b> {stop['SEQ']}<br/><b>Ponto:</b> {stop['NOME']}<br/><b>Passagens Reais:</b> {passages}"
                ).add_to(m)
                
            st_folium(m, width=900, height=500, key=f"folium_map_{line_code}_{direction_map}_{start_date}_{end_date}")
        else:
            st.warning("Dados geográficos não disponíveis para o sentido selecionado.")
            
    # ================= TAB 2: GRAFOS DESCOBERTOS (PM4PY) =================
    with tab2:
        st.header("🕸️ Modelos de Processo Descobertos (PM4Py)")
        st.write("Estes grafos de fluxo foram gerados diretamente a partir dos logs de eventos dos ônibus.")
        
        direction_model = st.selectbox("Sentido do Modelo:", ["VOLTA", "IDA"], key="model_dir")
        
        # Filtrar o log por sentido
        df_log_dir = df_log[df_log['gps_direction'] == direction_model]
        
        if not df_log_dir.empty:
            # Formatar para o PM4Py
            log_pm4py = pm4py.format_dataframe(
                df_log_dir,
                case_id='case:concept:name',
                activity_key='concept:name',
                timestamp_key='time:timestamp'
            )
            
            # Escolha do modelo
            modelo_opcao = st.radio(
                "Selecione o Modelo de Mineração de Processos:",
                ["Directly-Follows Graph (DFG)", "Rede de Petri (Inductive Miner)", "Rede Heurística (Heuristic Miner)"],
                horizontal=True
            )
            
            if modelo_opcao == "Directly-Follows Graph (DFG)":
                st.subheader("Directly-Follows Graph (DFG) do Fluxo Real")
                st.caption("Mostra as conexões diretas entre as paradas e a frequência de passagens.")
                dfg = pm4py.discover_dfg(log_pm4py)[0]
                gviz = dfg_visualizer.apply(dfg, log=log_pm4py)
                st.graphviz_chart(gviz)
                
            elif modelo_opcao == "Rede de Petri (Inductive Miner)":
                st.subheader("Rede de Petri Descoberta via Inductive Miner")
                st.caption("Representa o modelo matemático de concorrência e caminhos (Lugares, Transições e Tokens).")
                net, im, fm = pm4py.discover_petri_net_inductive(log_pm4py)
                gviz = pn_visualizer.apply(net, im, fm)
                st.graphviz_chart(gviz)
                
            elif modelo_opcao == "Rede Heurística (Heuristic Miner)":
                st.subheader("Rede Heurística Descoberta")
                st.caption("Modelo tolerante a ruídos que destaca os fluxos principais e omite caminhos excepcionais.")
                hnet = pm4py.discover_heuristics_net(log_pm4py)
                gviz = hn_visualizer.apply(hnet)
                st.graphviz_chart(gviz)
        else:
            st.warning("Não há dados de GPS para o sentido selecionado.")
            
    # ================= TAB 3: ESTATÍSTICAS DFG =================
    with tab3:
        st.header("📊 Estatísticas e Matriz DFG")
        st.write("Visualização estatística das transições reais de pontos pelos ônibus.")
        
        direction_dfg = st.selectbox("Sentido do Fluxo:", ["VOLTA", "IDA"], key="dfg_dir")
        
        # Filtrar o log por sentido
        df_log_dir = df_log[df_log['gps_direction'] == direction_dfg]
        
        # Rodar descoberta usando pm4py
        log_pm4py = pm4py.format_dataframe(
            df_log_dir,
            case_id='case:concept:name',
            activity_key='concept:name',
            timestamp_key='time:timestamp'
        )
        dfg, start_activities, end_activities = pm4py.discover_dfg(log_pm4py)
        
        # Converter DFG para dataframe para renderizar Plotly bar e tabela
        dfg_list = []
        for (act_a, act_b), freq in dfg.items():
            dfg_list.append({
                'Origem': act_a.replace('PASSAGEM_', ''),
                'Destino': act_b.replace('PASSAGEM_', ''),
                'Frequência': freq
            })
            
        if dfg_list:
            df_dfg = pd.DataFrame(dfg_list).sort_values(by='Frequência', ascending=False)
            
            # Gráfico de barras das transições mais comuns
            fig_dfg = px.bar(
                df_dfg.head(15),
                x='Frequência',
                y='Origem',
                color='Frequência',
                color_continuous_scale=px.colors.sequential.Reds,
                title="Top 15 Transições de Paradas Mais Frequentes",
                labels={'Origem': 'Parada de Origem'},
                orientation='h'
            )
            fig_dfg.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_dark")
            st.plotly_chart(fig_dfg, use_container_width=True)
            
            # Tabela de transições interativa
            st.subheader("📋 Matriz de Transição Detalhada")
            st.dataframe(df_dfg, use_container_width=True)
        else:
            st.warning("Não há transições registradas para o sentido selecionado.")
            
    # ================= TAB 4: CONFORMIDADE =================
    with tab4:
        st.header("🎯 Análise de Conformidade (Conformance Checking)")
        st.write("Verificação de fidelidade com relação à rota estrita e identificação de pontos de parada pulados.")
        
        direction_conf = st.selectbox("Sentido para Conformidade:", ["VOLTA", "IDA"], key="conf_dir")
        
        # Rodar análise de conformidade
        conformance_res = analyze_conformance(df_log, static_data['pontos'])
        
        if direction_conf in conformance_res:
            c_data = conformance_res[direction_conf]
            
            # Métricas
            col_c1, col_c2, col_c3 = st.columns(3)
            with col_c1:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{c_data["avg_fitness"]:.3f}</div><div class="metric-label">Fitness Médio (TBR)</div></div>', unsafe_allow_html=True)
            with col_c2:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{c_data["fit_percentage"]:.1f}%</div><div class="metric-label">Viagens 100% Conformantes</div></div>', unsafe_allow_html=True)
            with col_c3:
                st.markdown(f'<div class="metric-card"><div class="metric-value">{c_data["total_cases"]}</div><div class="metric-label">Total de Viagens Reais</div></div>', unsafe_allow_html=True)
                
            st.markdown("<br/>", unsafe_allow_html=True)
            
            # Gráfico de desvios (skipped stops)
            df_dev = c_data['deviations']
            
            # Contar frequências de cada ponto de parada pulado
            skipped_stops_all = []
            for stops in df_dev['skipped_stops']:
                skipped_stops_all.extend(stops)
                
            st.subheader("❌ Paradas Puladas (Skipped Stops)")
            if skipped_stops_all:
                skipped_counts = pd.Series(skipped_stops_all).value_counts().reset_index()
                skipped_counts.columns = ['Parada', 'Qtd. de Vezes Pulada']
                
                fig_skip = px.bar(
                    skipped_counts,
                    x='Qtd. de Vezes Pulada',
                    y='Parada',
                    color='Qtd. de Vezes Pulada',
                    color_continuous_scale=px.colors.sequential.Oranges,
                    title="Frequência de Pontos Pulados/Ignorados pelos Ônibus",
                    orientation='h'
                )
                fig_skip.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_dark")
                st.plotly_chart(fig_skip, use_container_width=True)
            else:
                st.success("Nenhuma parada foi pulada no período! Excelente conformidade operacional.")
                
            # Exibir logs de maior desvio
            st.subheader("📋 Detalhes de Viagens com Desvios")
            st.dataframe(df_dev[['case_id', 'vehicle', 'tabela', 'total_visited', 'skipped_count', 'skipped_stops', 'interpolated_count']], use_container_width=True)
        else:
            st.warning("Dados de conformidade não disponíveis para o sentido selecionado.")
            
    # ================= TAB 5: DESEMPENHO & GARGALOS =================
    with tab5:
        st.header("⚡ Análise de Desempenho Operational")
        st.write("Identificação de gargalos de velocidade e pontualidade frente à tabela horária planejada.")
        
        # 1. Análise de Gargalos por Segmento
        st.subheader("⏳ Tempos Médios de Viagem por Segmento")
        st.write("Os trechos com maior tempo médio indicam as áreas de maior lentidão/congestionamento da rota.")
        
        direction_perf = st.selectbox("Sentido para Performance:", ["VOLTA", "IDA"], key="perf_dir")
        
        # Filtrar log
        df_log_dir = df_log[df_log['gps_direction'] == direction_perf]
        segment_stats = analyze_segment_performance(df_log_dir)
        
        if not segment_stats.empty:
            fig_seg = px.bar(
                segment_stats.head(10),
                x='mean_time_min',
                y='segment_name',
                color='mean_time_min',
                color_continuous_scale=px.colors.sequential.Viridis,
                title="Top 10 Trechos Mais Lentos da Linha (Tempo em Minutos)",
                labels={'mean_time_min': 'Tempo Médio (min)', 'segment_name': 'Trecho'},
                orientation='h'
            )
            fig_seg.update_layout(yaxis={'categoryorder': 'total ascending'}, template="plotly_dark")
            st.plotly_chart(fig_seg, use_container_width=True)
            
            st.dataframe(segment_stats[['segment_name', 'total_passages', 'mean_time_min', 'median_time_min', 'max_time_min', 'min_time_min']], use_container_width=True)
        else:
            st.warning("Estatísticas de tempo não disponíveis.")
            
        # 2. Análise de Atrasos/Pontualidade
        st.markdown("---")
        st.subheader("🕒 Pontualidade (Comparação com a Tabela Horária Planejada)")
        st.write("Análise dos atrasos e adiantamentos das saídas dos ônibus em relação aos horários programados pela URBS.")
        
        df_delays = analyze_schedule_delays(df_log, static_data['tabela'], start_date, static_data['pontos'])
        
        if not df_delays.empty:
            # Gráfico de Pizza de Status de Pontualidade
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                status_counts = df_delays['status'].value_counts().reset_index()
                status_counts.columns = ['Status', 'Quantidade']
                
                # Mapeamento de cores: No Horário (Verde), Atrasado (Vermelho), Adiantado (Amarelo/Laranja)
                color_map = {'NO HORÁRIO': '#2ecc71', 'ATRASADO': '#e74c3c', 'ADIANTADO': '#f1c40f'}
                
                fig_pie = px.pie(
                    status_counts,
                    values='Quantidade',
                    names='Status',
                    color='Status',
                    color_discrete_map=color_map,
                    title="Distribuição de Pontualidade das Saídas"
                )
                fig_pie.update_layout(template="plotly_dark")
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_p2:
                # Histograma de minutos de atraso
                fig_hist = px.histogram(
                    df_delays,
                    x='delay_minutes',
                    color='direction',
                    nbins=20,
                    title="Distribuição dos Desvios Horários (em minutos)",
                    labels={'delay_minutes': 'Minutos de Desvio (positivo = atraso)'}
                )
                fig_hist.update_layout(template="plotly_dark")
                st.plotly_chart(fig_hist, use_container_width=True)
                
            st.dataframe(df_delays[['case_id', 'vehicle', 'tabela', 'direction', 'planned_departure', 'actual_departure', 'delay_minutes', 'status']], use_container_width=True)
        else:
            st.info("Nenhuma partida programada coincidiu na janela horária avaliada.")
else:
    st.info("Use o botão na barra lateral para carregar e processar os dados de Process Mining.")
