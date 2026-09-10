# Mineração de Processos Aplicada ao Transporte Público (URBS / Curitiba)

Sistema de reconstrução de trajetórias, análise de conformidade normativa e governança operacional para o transporte público de Curitiba utilizando **Mineração de Processos** (*Process Mining*) sobre telemetria GPS e dados abertos da URBS.

---

## 🎯 Objetivo do Trabalho (TCC)

Transformar dados brutos, ruidosos e esparsos de telemetria veicular GPS em **Logs de Eventos Estruturados** no padrão internacional **IEEE XES**, permitindo:

1. **Reconstrução Topológica de Trajetórias:** Projeção de pings GPS contínuos sobre o traçado viário planejado (*shapes*) e interpolação de passagens por paradas via **Splines Cúbicas Monotônicas (PCHIP)**.
2. **Detecção de Omissão de Paradas:** Identificação de paradas suprimidas ou desvios de itinerário utilizando limiar de proximidade geográfica ($d \le 150\,\text{m}$).
3. **Auditoria Diária do CCO:** Painel executivo consolidado para operadores do Centro de Controle Operacional (CCO) inspecionarem conformidade de contrato e pontualidade ao encerramento do dia.
4. **Comparação Inter-Regimes de Coleta:** Estudo do impacto da taxa de amostragem no erro de interpolação e na detecção de anomalias:
   * **Regime A (Amostragem Padrão - 120s):** Coleta contínua em out/2025 (~5,08 milhões de registros brutos).
   * **Regime B (Alta Frequência - 20s):** Coleta de alta taxa em dez/2025 (~167 horas contínuas).

---

## 🚀 Funcionalidades do Dashboard

O dashboard web interativo é composto por 5 visões integradas:

* **Auditoria Diária (CCO):** Visão executiva de encerramento do expediente com status das linhas (Conforme, Atenção, Crítico), conformidade média da frota, paradas puladas e atalho para inspeção direta.
* **Mapa de Replay Espacial:** Visualização geoespacial acelerada por hardware (**Deck.gl v9 + OpenStreetMap**) com suporte a **Replay Dual** (Lógico alinhado vs. Físico GPS real) e animação de linha do tempo.
* **Descoberta de Processos (Petri Net):** Síntese automática do modelo operacional de transições entre paradas utilizando **PM4Py** (Algoritmo Inductive Miner).
* **Conformidade Normativa Topológica:** Cálculo de *Trace Fitness*, percentual de viagens aderentes, identificação do ranking de paradas mais puladas e quantificação da incerteza de sensores (*pings* interpolados).
* **Desempenho Operacional (DFG):** *Directly-Follows Graph* interativo com tempos médios de trânsito entre pontos, destacando segmentos críticos de lentidão e gargalos estruturais (> 2 min).

---

## 📁 Estrutura do Repositório

```text
tcc-urbs/
├── README.md               # Apresentação do projeto, arquitetura e instruções
├── CONTEXT.md              # Modelo de domínio, terminologias canônicas e decisões da banca
├── AGENTS.md               # Regras operacionais para agentes de IA
├── data/
│   ├── dados_em_tempo_real_2026/  # Amostragens de telemetria GPS bruta por hora (CSV)
│   ├── dados_processados/         # Logs de eventos consolidados (CSV e XES)
│   └── static_cache/              # Geometrias (shapes) e paradas cacheadas da URBS
├── src/
│   ├── coleta/             # Scripts de ingestão contínua da API getVeiculos.php da URBS
│   ├── etl/                # TrajectoryReconstructor, snapping topológico e PCHIP spline
│   ├── mining/             # ProcessMiningEngine (PM4Py, Petri Nets, Conformance, DFG)
│   └── visualization/      # Servidor FastAPI e aplicação React/Vite/Tailwind
│       ├── dashboard.py    # Endpoints REST e streaming SSE do pipeline
│       ├── frontend/       # Código-fonte da SPA React com Deck.gl
│       └── static/         # Bundle compilado de produção servido pelo FastAPI
└── tests/                  # Suíte de testes automatizados (81 testes unitários, integração e E2E)
```

---

## 🛠️ Instalação e Execução

### Pré-requisitos
* Python 3.12+ (recomendado 3.14 via `.venv`)
* Node.js 20+ e npm

### 1. Preparar Ambiente Python
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Compilar Frontend
```bash
cd src/visualization/frontend
npm install
npm run build
cd ../../..
```

### 3. Iniciar Servidor do Dashboard
```bash
.venv/bin/python -m uvicorn src.visualization.dashboard:app --host 127.0.0.1 --port 8000 --reload
```
Acesse a aplicação no navegador em: **`http://127.0.0.1:8000/`**.

---

## 🧪 Executando os Testes Automatizados

A suíte conta com **81 testes automatizados**, cobrindo o pipeline completo de ETL, mineração de processos e contratos E2E da interface web:

```bash
# Executar todos os testes
.venv/bin/pytest tests/ -q
```
