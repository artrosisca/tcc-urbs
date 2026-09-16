# Capítulo 3 — Metodologia: Engenharia do Log de Eventos e Ferramentas

> Rascunho para revisão. **Nota:** o Cap. 3 descreve a metodologia *efetivamente implementada* (Map Matching HMM/Viterbi + interpolação PCHIP), na decisão aprovada em `docs/diagnostics/AVALIACAO_TCC_METODOLOGIA_E_DADOS.md`. Substituir a seção incompleta do PDF.

## 3.1 Visão Geral da Solução Proposta

A solução proposta estrutura-se em um pipeline de engenharia de dados com três estágios: (i) aquisição e curadoria de dados brutos da API pública da URBS; (ii) reconstrução de trajetórias com Map Matching probabilístico; e (iii) geração de um registro de eventos (event log) compatível com ferramentas de Mineração de Processos. O estágio (ii) é o responsável por transformar coordenadas GPS esparsas, potencialmente ruidosas e com lacunas temporais, em eventos discretos de passagem por pontos de ônibus, base para a descoberta, a verificação de conformidade e a análise de desempenho.

A execução do pipeline ocorre através de uma plataforma de análise com backend REST (Python/FastAPI) e frontend interativo, que permite selecionar linha, sentido, período e faixa horária, acionar o processamento (com rastreamento de progresso via Server-Sent Events) e inspecionar descoberta, conformidade e desempenho em visualizações dedicadas.

## 3.2 Aquisição e Armazenamento de Dados

### 3.2.1 Coleta Contínua de Dados via API da URBS e Construção do Dataset Histórico

A telemetria dinâmica de veículos da URBS é coletada por consultas sucessivas ao endpoint público de dados em tempo real, sendo persistida em arquivos CSV particionados por hora e dia (`data/dados_em_tempo_real_2026/YYYY-MM-DD/YYYY-MM-DD_HH-00.csv`). Cada registro bruto contém, entre outros, o identificador do veículo (`COD`), a linha (`CODIGOLINHA`), coordenadas geográficas (`LAT`, `LON`), sentido operacional (`SENT`), tabela de escala (`TABELA`), situação operacional (`SITUACAO`) e o `request_timestamp` da coleta.

Os dados estáticos de cadastro — pontos de parada com sequência geográfica (`pontosLinha`), tabela horária planejada (`tabelaLinha`) e traçado físico da linha (`shapeLinha`) — são obtidos de um backup histórico mantido pelo Centro de Computação Científica e Software Livre (C3SL) e arquivado em `data/dados_c3sl`, com fallback direto à API URBS e cache local (`data/static_cache`) na ausência do backup (`src/etl/repository.py`).

Foram coletados dois grandes regimes operacionais conforme a cadência temporal: Regime A (outubro/2025, ~120s entre amostras, 5,08 milhões de registros em seis dias, 24 a 29/10) e Regime B (dezembro/2025, ~20s entre amostras, de 02 a 08/12, ~7 dias). Os dados brutos do Regime B não estão versionados no repositório; para este regime, a análise utiliza o event log processado completo (16.822 eventos e 1.200 viagens da linha 541). Essa divisão permite avaliar a sensibilidade da reconstrução à taxa de amostragem.

### 3.2.2 Pré-processamento e Estruturação dos Dados Brutos

O pré-processamento codificado em `clean_telemetry` realiza, por veículo: (i) remoção de coordenadas nulas; (ii) exclusão de registros marcados como garagem/`REC`; (iii) remoção de estados operacionais nulos (`SITUACAO`, `SENT`); (iv) remoção de duplicatas exatas (veículo+timestamp); (v) filtro de *jitter* estacionário (distância mínima de 5m em relação ao ponto anterior); e (vi) rejeição de posições geográficas anômalas (*outliers*).

Nesta última etapa (vi), para evitar o descarte incorreto de pings válidos em trechos expressos (onde paradas consecutivas distam mais de 1 km), a distância de cada ping é mensurada preferencialmente em relação aos vértices contínuos do traçado da linha (`shapeLinha`). Apenas leituras de GPS a mais de 500 metros de qualquer ponto do *shape* planejado são consideradas espúrias e definitivamente descartadas. Em abordagens legadas (sem dados do *shape*), o filtro limitava-se a medir a distância aos pontos fixos de parada, resultando em falsos positivos em vias arteriais, problema que nossa metodologia resolveu.

## 3.3 Construção do Log de Eventos via Map Matching HMM e Interpolação Temporal

### 3.3.1 Segmentação de Viagens (Cases)

Após a limpeza, os pings são segmentados em viagens (process *cases*) por veículo e dia, com corte por inversão de sentido operacional (`SENT`) ou por lacuna temporal superior a 10 minutos entre amostras — na ausência/fragilidade de `SENT`, a reversão de progresso na coordenada curvilínea do shape pode ser empregada como fallback.

### 3.3.2 Map Matching com Hidden Markov Model (Viterbi)

Cada viagem é projetada sobre o traçado físico (`shapeLinha`) utilizando um Hidden Markov Model resolvido pelo algoritmo de Viterbi. O modelo de emissão penaliza a distância GPS–candidato com σ_z = 30m; o modelo de transição penaliza divergências entre a distância geográfica e a distância acumulada no shape com β = 50m, na formulação seminal de Newson e Krumm (2009). A projeção devolve, para cada ping, o índice do nó do shape e a coordenada curvilínea acumulada *s*.

### 3.3.3 Interpolação Temporal com PCHIP Monotônico

Com $(s, t)$ dos pings projetados, estimamos o tempo de passagem em paradas com interpolador PCHIP (Piecewise Cubic Hermite Interpolating Polynomial), escolhido por garantir monotonicidade temporal (dt/ds ≥ 0), evitando *overshoots* e causalidades invertidas dos splines cúbicos naturais. Paradas cuja distância mínima ao trajeto excede o limiar de aceitação (150m) não são interpoladas: são **omitidas** do log, para que o *conformance checking* detecte legitamente a parada pulada.

### 3.3.4 Qualidade dos Eventos

Cada evento `PASSAGE` carrega metadados de qualidade, incluindo a distância mínima observada e o indicador booleano `interpolated` (verdadeiro quando o ping mais próximo está a mais de 100m da parada), permitindo separar conformidade operacional de incerteza de sensoriamento.

## 3.4 Estruturação Final e Exportação do Log de Eventos

O log estruturado segue as convenções do PM4Py: colunas `case:concept:name` (viagem identificada por veículo, linha, tabela e data), `concept:name` (atividade `PASSAGEM_{NOME}`), `time:timestamp` e atributos contextuais (`org:resource` = veículo, `tabela`) e de qualidade. A exportação ocorre em CSV e no formato padrão XES, permitindo o uso direto de algoritmos de descoberta e conformidade.

## 3.5 Análise Exploratória e Validação da Metodologia

A corretude do pipeline é garantida por suíte automatizada de 82 testes (61 E2E do dashboard, 8 do motor PM, 3 do repositório e 10 do reconstrutor de trajetórias) cobrindo limpeza, projeção HMM, PCHIP, omissão de paradas sem evidência e preservação de índices em rotas circulares. Adicionalmente, a qualidade da reconstrução é validada visualmente por replay geoespacial alternando traçado **lógico** (eventos projetados) e **físico** (pings brutos).