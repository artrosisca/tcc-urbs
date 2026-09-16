# Capítulo 4 — Resultados: Aplicação da Mineração de Processos

> Rascunho para revisão com números extraídos do repositório em 2026-09-11 (`/tmp/opencode/tcc_metrics.py` usando `src/etl/repository.py` e `src/mining/engine.py`).

## 4.1 Descrição dos Cenários de Análise e Taxa de Censura Operacional

A avaliação empregou a linha 541 (Bairro Novo A → Centro) da URBS em dois regimes: Regime A (24 a 30/10/2025, ~120s) e Regime B (02 a 08/12/2025, ~20s). O volume bruto do Regime A soma ~5,08 milhões de registros (~0,53M–1,0M/dia). Para o Regime B, utilizou-se o event log processado completo (`data/dados_processados/event_log_541_2025-12-02_2025-12-08{.csv,.xes}`). 

Graças à introdução do filtro geoespacial baseado no traçado (Shape) do ônibus (e não estritamente nos pontos de parada), pings ao longo de vias expressas esparsas não são mais erroneamente descartados como anomalias. 

| Regime | Eventos | Viagens (cases) | Veículos | Pings IDA / VOLTA | % eventos interpolados | Taxa de Censura |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| A (120s) | 5.092 | 956 | 26 | 2.821 / 2.271 | 23,1% | ~20,3% |
| B (20s) | 16.822 | 1.200 | 30 | 9.360 / 7.462 | 47,8% | ~2,1% |

> O percentual de eventos marcados como `interpolated=True` (distância mínima > 100m) é exposto como **metadado de qualidade**. Além disso, viagens candidatas que apresentam menos de 3 pings ou mais de 90% dos eventos interpolados são barradas pela Taxa de Censura Operacional para não poluírem o modelo.

## 4.2 Descoberta de Processos e Análise do Modelo Real de Operação

A descoberta utilizou o Inductive Miner do PM4Py (`discover_petri_net_inductive`) sobre o log XES, produzindo a Rede de Petri real de cada regime. No Regime A, a reconstrução de menor cadência disfardece o acesso exato às geocercas, induzindo mais eventos marcados como interpolados; no Regime B, a viagem típica é recuperada com alta fidelidade topológica. O regulamento da sequência de atividades (ordem de passagem) é garantido pela ordem cronológica (`stop_seq`) e não por `n.maximum.accumulate`, o que preserva rotas circulares.

## 4.3 Análise de Conformidade: Diagnóstico de Desvios

O modelo normativo foi construído sequencialmente a partir do cadastro (`create_normative_petri_net`) e a conformidade avaliada por *token-based replay* (PM4Py).

### 4.3.1 Identificação e Quantificação de Desvios de Rota

A linha 541 possui **13 paradas** no sentido "Bairro Novo A" e **15 paradas** no sentido "Terminal Sítio Cercado" (cadastro estático). Após a correção da chave de atividade para casamento por identidade da parada (`stop_seq`, tarefa F1.1), os resultados são:

| Regime | Sentido | Fitness médio | Casos conformes | Total de casos |
| :--- | :--- | ---: | ---: | ---: |
| A | IDA | 0,4564 | 0,0% | 488 |
| A | VOLTA | 0,3798 | 0,0% | 468 |
| B | IDA | 0,9966 | 95,2% | 628 |
| B | VOLTA | 1,0000 | 100,0% | 572 |

**Correção metodológica relevante:** antes do casamento por `stop_seq`, a comparação por nome de via produzia **pulas fantasma** — todas as 572 viagens do Regime B VOLTA apareciam pulando as mesmas ~13 paradas, por ambiguidade na detecção de sentido e por diferenças de encoding entre o log e o cadastro. O achado operacional recorrente real, após a correção, é pontual: no Regime B IDA, duas paradas ("Rua São José dos Pinhais, 121" e o terminal) somam 30 omissões cada (~4,8% das 628 viagens).

**Regime A:** os mesmos pontos dominam as omissões (ex.: "Rua São José dos Pinhais, 369/669", ~97% das viagens IDA), mas a leitura correta é de **reconstrução esparsa** (a 120s poucas paradas caem dentro do geofence de 150m), não necessariamente desvio operacional.

## 4.4 Análise de Desempenho: Identificação de Gargalos

O grafo diretamente-seguido (DFG) de performance mede tempos entre passagens consecutivas e os agende atrasos assumem as partidas na tabela (`TABELA`).

### 4.4.1 Segmentos Críticos por Regime

Regime B — com propagação de qualidade (F1.3): o tempo é calculado **apenas com passagens observadas** (endpoints não interpolados); a razão interpolada é divulgada por arco:

| Arco | Tempo médio | Tempo mediano | n total | n observado | % interpolado |
| :--- | ---: | ---: | ---: | ---: | ---: |
| "Rua São José dos Pinhais, 121 → Terminal Sítio Cercado" | 7.12 min | 4.89 min | 611 | 186 | 69,6% |
| "Terminal Sítio Cercado → Rua São José dos Pinhais, 108" | 2.53 min | 1.76 min | 589 | 86 | 85,4% |
| "Rua São José dos Pinhais, 1176 → Rua Cidade de Palmas" | 1.53 min | 1.45 min | 589 | 234 | 60,3% |

> Antes do F1.3, tempos sintéticos do PCHIP contaminavam as estatísticas (o arco crítico marcava 5,23 min sobre n=611). Os arcos à saída dos terminais continuam como gargalos estruturais — mas apenas fração das passagens é efetivamente observada.

Regime A: o arco crítico top-3 registrou 8.19 min em "Rua Jussara, 2306 → Terminal Sítio Cercado" (n=6). Amostras pequenas limitam a comparabilidade absoluta entre regimes — o ranking permanece como evidência estrutural.

### 4.4.2 Análise de Atraso e Pontualidade por Período

| Regime | Delay médio (min) | NO HORÁRIO | ADIANTADO | ATRASADO |
| :--- | ---: | ---: | ---: | ---: |
| A | +3.98 | 35 | 4 | 15 |
| B | +0.66 | 180 | 34 | 22 |

## 4.5 Discussão dos Resultados

- O Regime B (alta cadência) obteve fitness médio 0,9966 (IDA) e 1,0000 (VOLTA), com 95,2% e 100,0% de casos conformes. Como paradas sem evidência geográfica são **omitidas** do log de eventos, os desvios quantificados por *token replay* correspondem a omissões legítimas e não a artefatos de interpolação.
- No Regime A (baixa cadência), o fitness baixo (~0,38–0,46) reflete a impossibilidade de associar pings às paradas em <150m — e não, necessariamente, desvio operacional real.
- Os gargalos estruturais (arcos de saída dos terminais/bairros) persistem no Regime B com n elevado, indicando gargalo operacional e não ruído amostral.
- O casamento por identidade da parada eliminou **pulas fantasma** que, na versão anterior, eram interpretadas como "rota encurtada" recorrente — a diferença 13 vs 15 reflete simplesmente a contagem de paradas de cada sentido, não desvio operacional.
- Limitações do Regime A: n reduzido por arco compromete inferência; o raw do Regime B não está no repositório (usa-se log processado); nomes de segmentos no texto de análise de desempenho exibem mojibake residual a corrigir na escrita do CSV (tarefa F1.5 do plano).