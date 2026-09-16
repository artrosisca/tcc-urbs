# Guia do Dashboard e Mapeamento de Visualizadores

Este documento detalha o funcionamento de cada tela da interface (UI) do projeto TCC URBS, focando na integração com a **PM4Py** e na usabilidade técnica, além de trazer sugestões valiosas para a defesa perante a banca.

## 1. Visão Geral das Abas (Telas da UI)

O painel foi desenhado com o conceito de abas para separar a visão executiva da visão puramente algorítmica.

### 1.1 Auditoria Diária (CCO)
* **Objetivo:** Fornecer uma visão executiva agregada no estilo "Centro de Controle Operacional". Mostra a conformidade média da frota, total de viagens realizadas e um ranking (Top 10) de ônibus que mais apresentaram desvios ou pularam pontos de parada.
* **Mecanismo:** Tabelas React padrão conectadas ao JSON de saída do algoritmo de *Token-Based Replay* da PM4Py.
* **Interatividade (Drill-down):** Clicar em qualquer viagem desviante salta diretamente para o Mapa de Replay, exibindo a trajetória individual isolada para auditoria.

### 1.2 Mapa de Replay
* **Objetivo:** Visualização geoespacial (GIS) de alto desempenho do trânsito dos ônibus no mundo real.
* **Mecanismo:** Utiliza a biblioteca **Deck.gl** (padrão ouro em big-data espacial do Uber) para sobrepor camadas no mapa.
* **Componentes Exclusivos:**
  * **Barra de Tempo Dinâmica:** Varre os dados reais de log e se ajusta à janela de operação (min/max do GPS).
  * **Modo Teórico vs Executivo:** Alterna a posição dos eventos entre o traçado geográfico real das ruas (Executivo) e o alinhamento lógico direto aos pontos de parada (Teórico).

### 1.3 Descoberta (Rede de Petri)
* **Objetivo:** Exibir o **Processo Normativo/Descoberto**, ilustrando a sequência lógica de paradas que a linha deveria realizar (o modelo "ideal" ou "padrão" da operação).
* **Visualizador:** **100% Nativo PM4Py** (`pm4py.discover_petri_net`). O Graphviz gera a Rede de Petri, e o SVG resultante é renderizado de forma responsiva pela biblioteca `svg-pan-zoom`.

### 1.4 Conformidade
* **Objetivo:** Exibir os diagnósticos de fitness gerados matematicamente. Se um ônibus pulou paradas, qual a porcentagem métrica (0 a 100%) da adesão dele à Rede de Petri.
* **Visualizador:** Tabela textual.

### 1.5 Desempenho (DFG - Directly-Follows Graph)
* **Objetivo:** Perfilador de gargalos operacionais. Revela o tempo consumido nas transições.
* **Visualizador:** **100% Nativo PM4Py** (`pm4py.discover_performance_dfg`). Exibe o grafo direcionado anotado nativamente com estatísticas de tempo (médio/mediana) nas arestas (arcos do grafo). Controlado perfeitamente via `svg-pan-zoom`.

---

## 2. Há Outros Visualizadores da PM4Py para Usar?

No contexto atual, **nós já esgotamos e migramos com sucesso todos os visualizadores baseados em grafos para o motor nativo da PM4Py!**

* **Grafo de Rede de Petri:** Era JSON customizado, migramos para PM4Py.
* **Grafo DFG de Desempenho:** Era D3.js customizado, migramos para PM4Py.

**Outros visualizadores da PM4Py existentes (porém não aplicáveis no momento):**
* **Process Trees (Árvores de Processos):** É uma visão acadêmica puramente estrutural, gerada pelo *Inductive Miner*. Como já estamos plotando a conversão dessa árvore para Rede de Petri, plotar a árvore seria redundante para a operação de ônibus.
* **Heuristics Nets:** Exige o uso do Heuristics Miner. Nós optamos rigorosamente pelo Inductive Miner para garantir *Soundness* (ausência de deadlocks na simulação do trânsito).
* **SNA (Social Network Analysis):** Voltado para Handover de recursos (ex: analista A passou o ticket para o analista B). Não tem cabimento no contexto URBS (ônibus não repassam viagens entre si).

**Veredito:** Estamos utilizando o estado da arte e o pacote exato que a banca espera ver!

---

## 3. Sugestões para Apresentação na Banca

1. **Abreviação Rápida:** Comece a demonstração mostrando a aba de **Auditoria (CCO)**. É ela que justifica o valor do projeto para o painel gerencial.
2. **O Momento "Uau":** Utilize o novo "Drill-down" (F2.8). Com a banca assistindo, localize na lista de Auditoria um ônibus com 2 ou 3 pontos "pulados", clique nele e mostre o mapa trocando para o **Modo Replay Isolado**. Aperte Play e veja a "prova do crime" geoespacial. Isso vende a união da Inteligência Computacional com GIS!
3. **Mencione as Ferramentas Oficiais:** Ao abrir as abas de "Descoberta" e "Desempenho", ressalte que **não são desenhos arbitrários**, mas sim instâncias exatas renderizadas e validadas pelo framework **PM4Py / Graphviz**, garantindo alto rigor metodológico.
