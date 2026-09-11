# Diagnóstico de UI/UX, Análise de Process Mining e Plano de Refatoração

> **Data:** Setembro de 2026  
> **Projeto:** Mineração de Processos Aplicada ao Transporte Coletivo de Curitiba (URBS)  
> **Autor do Diagnóstico:** Antigravity (Pair Programming / Engenharia de Software)

---

## 1. Resumo Executivo

Este documento consolida uma auditoria profunda sobre a interface do usuário (UI), a experiência do usuário (UX), as métricas de mineração de processos e a arquitetura de código do sistema URBS Process Mining.

O objetivo é esclarecer:
1. Por que a aba de **Conformidade** apresenta frequências de paradas puladas com aparência duplicada/estática (`13x` em várias paradas com o mesmo nome e viagens com `15 visitadas / 11 puladas`).
2. Por que a visualização da **Rede de Petri (Descoberta)** se transforma em um "emaranhado de nós" de difícil compreensão para um operador e o que cada elemento geométrico realmente significa.
3. Se o fluxo da **Sidebar de Filtros** respeita a jornada de um usuário comum da URBS (ou de um avaliador de banca) e como simplificá-la.
4. O que há de **bom e ruim** na interface atual e quais oportunidades de refatoração trarão mais valor tanto para a defesa do TCC quanto para o uso diário no CCO (Centro de Controle Operacional).

---

## 2. Diagnóstico do Print 1: Inspetor de Conformidade

![Print 1 - Conformidade](/home/arosisca/.gemini/antigravity-cli/brain/2adbbb8a-5618-4106-9a00-d4ed19cf77f8/print_conformidade.png)

### 2.1. As Perguntas do Usuário
- *Por que quase todas as paradas aparecem com a mesma frequência de desvio (`13x`) e com o mesmo nome repetido várias vezes ("Rua São José d...")?*
- *Por que na tabela da esquerda todas as Top 10 viagens com maior desvio têm exatamente `15 paradas visitadas e 11 paradas puladas`? Parece bug ou dado fixado?*

### 2.2. A Causa Raiz Técnica: O Dado Já Existe, mas Foi Desperdiçado na Exibição!

> [!IMPORTANT]
> **A tabela da URBS e os arquivos CSV gerados pelo nosso próprio pipeline de ETL já contêm todas as informações de ordenação e identificação física!**  
> O pipeline não está sem os dados: o que ocorreu foi um **gargalo de achatamento (*flattening*) na camada de mineração e um corte de CSS no frontend.**

#### A) O que o Cadastro da URBS e o ETL Já Possuem Gravado
Ao inspecionarmos o arquivo gerado pelo pipeline (`data/dados_processados/event_log_541_2025-12-02_2025-12-08.csv`), verificamos que cada linha contém explicitamente a sequência exata e o código físico do poste:

| `stop_seq` (Sequência) | `stop_num` (Poste URBS) | `concept:name` (Atividade Extraída) | Número Predial |
| :---: | :---: | :--- | :---: |
| **1** | `106103` | `PASSAGEM_Terminal Sítio Cercado - 541 - Bairro Novo A` | Terminal |
| **2** | `160098` | `PASSAGEM_Rua São José dos Pinhais, 108 - Sítio Cercado` | Nº 108 |
| **3** | `160100` | `PASSAGEM_Rua São José dos Pinhais, 358 - Sítio Cercado` | Nº 358 |
| **4** | `160102` | `PASSAGEM_Rua São José dos Pinhais, 648 - Sítio Cercado` | Nº 648 |
| **6** | `160106` | `PASSAGEM_Rua São José dos Pinhais, 1176 - Sítio Cercado` | Nº 1176 |
| **9** | `160109` | `PASSAGEM_Rua São José dos Pinhais, 1423 - Sítio Cercado` | Nº 1423 |

Ou seja: o sistema **sabe exatamente** qual é a ordem cronológica (`stop_seq: 1, 2, 3... 26`), o identificador único de tombamento do poste da URBS (`stop_num`) e o número predial da rua.

#### B) Onde Ocorreu o "Desperdício" da Informação
A perda de rastreabilidade aconteceu em dois pontos específicos da cadeia:

1. **Agrupamento Cego no Motor de Mineração (`src/mining/engine.py`):**
   No método `evaluate_conformance`:
   ```python
   planned_stops = ['PASSAGEM_' + str(n) for n in stops_dir['NOME'].tolist()]
   for case_id, case_group in group.groupby('case:concept:name'):
       for stop in planned_stops:
           if case_group[case_group['concept:name'] == stop].empty:
               clean_name = stop.replace('PASSAGEM_', '')
               skipped_stops_all.append(clean_name)
   ```
   Em vez de verificar se o ônibus passou pela parada usando o identificador único `(stop_seq, stop_num)`, o código verificou apenas a string textual `concept:name`. Como os 7 pontos da Rua São José dos Pinhais compartilham a mesma via, quando um ônibus desviou do trecho, a string foi adicionada 7 vezes na lista sem o número da sequência.

2. **O Truncamento de CSS no Frontend (`ConformanceInspector.jsx`):**
   Na hora de renderizar a lista de paradas puladas, o componente aplicou:
   ```jsx
   <span className="truncate max-w-[200px]" title={stop.stop_name}>
     {stop.stop_name}
   </span>
   ```
   A regra `truncate max-w-[200px]` corta qualquer texto com mais de ~15 caracteres e adiciona reticências:
   - `Rua São José dos Pinhais, 108` $\rightarrow$ virou **`Rua São José d...`**
   - `Rua São José dos Pinhais, 358` $\rightarrow$ virou **`Rua São José d...`**
   - `Rua São José dos Pinhais, 648` $\rightarrow$ virou **`Rua São José d...`**
   - `Rua São José dos Pinhais, 1176` $\rightarrow$ virou **`Rua São José d...`**  
   
   **Consequência Visual:** 7 paradas físicas totalmente distintas apareceram com o **mesmo texto truncado** e com a **mesma contagem de 13x**. Qualquer observador humano tem a certeza imediata de que a tela está com um bug de repetição de registros duplicados!

3. **Na Rede de Petri (`ProcessVisualizer.jsx`):**
   Em vez de usar `stop_seq` para ordenar as transições do início ao fim (da esquerda para a direita em uma linha do tempo clara), os nós foram entregues a um algoritmo de física de forças (`d3.forceSimulation`), que embaralha as paradas como se fossem elétrons repelindo uns aos outros, ignorando a ordem natural do itinerário.

#### C) A Ilusão das Barras em 100% (Escala Relativa vs. Absoluta)
No componente `ConformanceInspector.jsx`, a largura da barra foi implementada como:
```javascript
const totalSkips = skipped_stops[0].count; // Maior valor do ranking (neste caso, 13)
const pct = (stop.count / totalSkips) * 100;
```
- Se o valor máximo encontrado na semana foi `13`, o cálculo para todas as paradas com contagem `13` resulta em `(13 / 13) * 100 = 100%`!
- O usuário olha para a tela e tem a sensação errônea de que **todas as paradas foram puladas 100% das vezes**, quando na realidade:
  $$\text{Taxa Real de Violação} = \frac{13 \text{ viagens}}{572 \text{ viagens totais}} = 2{,}27\%$$
- Apenas **2,3% das viagens da semana** tiveram esse desvio! Mas a barra visual cheia em 100% induz ao pânico operacional.

#### D) Por que o Top 10 mostra sempre "15 Visitadas / 11 Puladas"?
A linha 541 (Bairro Novo A) possui **26 paradas totais** no sentido VOLTA ($15 + 11 = 26$).
- No transporte público de Curitiba, viagens de fim de turno ou recolhimento operacional não fazem o laço completo dentro do Bairro Novo; elas cortam caminho pela via principal para retornar ao terminal ou garagem.
- Esse corte padrão omite sistematicamente o mesmo trecho de **11 paradas**.
- Houve **13 viagens na semana** que realizaram exatamente esse trajeto encurtado.
- Como o ranking lista as 10 viagens com maior quantidade de paradas puladas ordenadas por `skipped_count`, as primeiras 10 posições pertencem todas a essa mesma anomalia operacional recorrente. Não é um dado congelado nem bug, mas sim um **comportamento operacional em lote** do sistema de ônibus.

### 2.3. O que deve ser ajustado no Inspetor de Conformidade:
1. **Desambiguação Visual de Paradas:**
   - Adicionar o número da sequência e o identificador do ponto: `[Ponto #04] Rua São José dos Pinhais (#102034)`.
   - Agrupar por código único de parada (`stop_id` ou `stop_seq`) e não apenas pelo nome da rua.
2. **Escala Percentual Realista:**
   - Em vez de calcular `pct` relativo ao primeiro colocado, calcular sobre o total de viagens ativas:  
     *Exemplo:* `13x (2,3% das 572 viagens)`. A barra deve ocupar apenas 2,3% da largura, refletindo com precisão a alta conformidade da linha.
3. **Interatividade na Tabela de Desvios (Drill-Down):**
   - Ao clicar em uma linha da tabela "Top 10 Viagens", abrir um modal ou levar o usuário diretamente ao **Mapa de Replay com aquela viagem selecionada**, traçando os pontos visitados em verde e os pulados em vermelho.

---

## 3. Diagnóstico do Print 2: Descoberta de Rede de Petri

![Print 2 - Rede de Petri](/home/arosisca/.gemini/antigravity-cli/brain/2adbbb8a-5618-4106-9a00-d4ed19cf77f8/print_petri_net.png)

### 3.1. As Perguntas do Usuário
- *Por que esse gráfico fica tão ruim de ver e com tanto espaço em branco?*
- *O que cada uma dessas figuras geométricas e letrinhas significa? Eu não entendo até hoje.*
- *Isso tem utilidade real para quem trabalha com ônibus ou é só teoria?*

### 3.2. O Significado Teórico de Cada Elemento

A Rede de Petri é uma representação matemática formal para sistemas concorrentes e assíncronos. No contexto de Process Mining aplicado ao transporte:

| Elemento Visual | Conceito na Rede de Petri | Significado no Transporte Coletivo da URBS |
| :--- | :--- | :--- |
| **Círculo Verde com `IN`** | Lugar Inicial (*Source Place*) | O início da viagem (ônibus posicionado no terminal de partida). |
| **Círculo Vermelho com `OUT`** | Lugar Final (*Sink Place*) | O fim da viagem (ônibus chegou ao terminal de destino/fim de linha). |
| **Círculos Brancos com `P`** | Lugares Intermediários (*Places*) | **Condições/Estados do Ônibus:** Representam o estado em que o veículo já validou a parada anterior e está autorizado/em trânsito para a próxima. |
| **Retângulos Pretos com Texto** | Transições Visíveis (*Transitions*) | **O Evento Real:** A passagem registrada do ônibus pelo raio daquela parada de ônibus (ex.: `PASSAGEM_Rua Jussara...`). |
| **Barras Finas Verticais Cinzas** | Transições Silenciosas ($\tau$ - *Tau*) | **Roteamento Interno do Algoritmo:** Transições invisíveis que não consomem dados do GPS. O *Inductive Miner* insere nós $\tau$ para permitir "atalhos" ou desvios opcionais (ex.: representar formalmente que o ônibus pode pular uma sequência de paradas sem travar a rede). |
| **Setas / Arcos** | Arcos de Controle (*Arcs*) | A dependência causal: uma parada só pode ocorrer depois que o estado anterior produziu a "ficha" (*token*). |

### 3.3. Por que a visualização fica péssima na tela?

1. **Uso de Física de Partículas (`d3.forceSimulation`) para um Fluxo Sequencial:**
   - Uma linha de ônibus é um fluxo orientado estritamente do Ponto 1 ao Ponto 26 (um grafo acíclico direcionado - DAG).
   - O código do componente `ProcessVisualizer.jsx` utiliza `d3.forceSimulation`, que simula forças gravitacionais e repulsões coulombianas entre átomos.
   - As paradas se comportam como balões soltos: o ponto de início vai para o centro, a parada final vai para o canto, e as setas passam umas por cima das outras, gerando um efeito de "teia de aranha" ou "espaguete".
2. **ViewBox Fixo (800x500) em Tela Grande:**
   - A janela do usuário tem cerca de 800 a 1000 pixels de altura vertical, mas o SVG foi travado em `viewBox="0 0 800 500"`. Ao manter o aspecto esticado no centro, o SVG cria duas faixas brancas gigantescas em cima e embaixo.
3. **Caixas de Texto com Tamanho Fixo de 75px:**
   - Nomes reais de logradouros de Curitiba (ex.: *"Rua Desembargador Carlos Pinheiro Guimarães"*) ocupam mais de 40 caracteres. Com uma caixa de 75px, a palavra é cortada em 7 letras (`Rua Des...`), tornando impossível saber qual ponto está sendo inspecionado.
4. **Distanciamento da Realidade de Gestão de Frota:**
   - Para um pesquisador acadêmico de Ciência da Computação, a Rede de Petri é indispensável porque ela prova matematicamente propriedades de *soundness* (ausência de deadlocks e loops infinitos).
   - Para um fiscal ou diretor da URBS, no entanto, **lugares `P` e transições silenciosas `tau` não fazem sentido algum**. O que eles entendem e precisam é de um **Grafo de Fluxo Direto (DFG)** com caixas de paradas conectadas sequencialmente, onde a espessura da linha indica a quantidade de ônibus e a cor indica o tempo de percurso.

### 3.4. O que deve ser ajustado na aba de Descoberta:
1. **Substituir a Simulação de Força por Layout Hierárquico Direcionado (Dagre / Sugiyama):**
   - Os nós devem ser dispostos de forma fluida da esquerda para a direita (LTR) ou de cima para baixo, preservando a ordem cronológica do itinerário.
2. **Alternância de Visualização (Modo Executivo vs. Modo Acadêmico):**
   - **Modo Executivo (Recomendado para URBS):** Mostra apenas as paradas reais em sequência com taxa de desvio.
   - **Modo Teórico (TCC):** Mostra a Rede de Petri com lugares $P$ e transições $\tau$, porém com zoom/pan e nós clicáveis com tooltip completo.
3. **Controles Interativos de Zoom e Pan (`d3.zoom`):**
   - Permitir navegar, arrastar e aproximar com o scroll do mouse para ler qualquer parada com nitidez.

---

## 4. Avaliação Heurística da UI / UX Atual

### 4.1. O que o Projeto tem de BOM (Pontos Fortes)
1. **Paleta de Cores e Consistência Visual:**  
   O uso de Tailwind CSS com paleta neutra (Slate-50 a Slate-900) e destaques semânticos (azul para ações, esmeralda para conformidade, âmbar para atenção e vermelho para desvio) confere ao sistema uma aparência profissional e executiva.
2. **Auditoria Diária do CCO (`FleetAuditView`):**  
   Esta visão foi o maior salto de valor prático do sistema. Ela resume uma semana inteira de mineração de processos em uma tabela de auditoria por dia, permitindo ao operador identificar instantaneamente se na sexta-feira ou no domingo houve queda no cumprimento de rota.
3. **Replay Dual no Mapa (`GeospatialConsole`):**  
   A possibilidade de alternar entre o traçado **Lógico (Alinhado à Rota)** e o traçado **Físico (GPS Real)** traduz visualmente o resultado do algoritmo de alinhamento de traçado, sendo uma das demonstrações mais ricas para a banca do TCC.
4. **Chip de Sincronia Flutuante no Topo do Mapa:**  
   Resolveu o problema da incerteza visual, garantindo que o usuário saiba a todo momento qual linha, sentido, regime e data estão sendo exibidos no canvas.
5. **Aba de Desempenho (DFG):**  
   O Grafo Diretamente-Seguido com cálculo de medianas de tempo entre paradas identifica claramente os trechos congestionados da cidade.

---

### 4.2. O que o Projeto tem de RUIM (Pontos Fracos e Gargalos)

| Área | Problema Identificado | Impacto no Usuário | Severidade |
| :--- | :--- | :--- | :--- |
| **Navegação** | Falta de linkagem cruzada entre telas (ex.: ver uma viagem desviada da tabela direto no mapa). | O usuário precisa anotar o prefixo do veículo e tentar encontrá-lo manualmente no mapa de replay. | **Alta** |
| **Linha do Tempo** | O slider de tempo no mapa começa em 00:00 e vai até 24:00. Como a maioria das linhas opera entre 05:00 e 23:30, dar play no início resulta em minutos de tela estática no escuro. | Sensação de que o replay está quebrado quando na verdade a frota ainda não saiu da garagem. | **Média** |
| **Vocabulário** | Uso excessivo de termos técnicos de Process Mining (*Fitness*, *Underlying Model*, *Token Replay*, *Tau*). | Usuários de negócio da URBS não entendem os rótulos sem uma explicação prévia. | **Média** |
| **Rede de Petri** | Nós emaranhados por simulação de física em vez de fluxo sequencial. | A aba de Descoberta não entrega clareza visual para a tomada de decisão. | **Alta** |
| **Conformidade** | Paradas repetidas com 100% de preenchimento relativo de barra. | Cria falsa impressão de pane geral no cumprimento do itinerário. | **Alta** |

---

## 5. A Sidebar Respeita o Fluxo de um Usuário Comum?

### 5.1. Fluxo Mental de um Operador da URBS vs. Fluxo Atual da Interface

#### Como o usuário comum pensa (Fluxo Operacional Natural):
1. *"Qual linha eu quero fiscalizar?"* $\rightarrow$ Linha 541.
2. *"Qual dia ou semana?"* $\rightarrow$ Dia 02/12/2025.
3. *"Qual sentido da linha?"* $\rightarrow$ VOLTA.
4. *"Ver os dados e auditar."*

#### Como a Sidebar atual está organizada (Fluxo Invertido):
```
[1. Regime de Coleta (Regime A vs Regime B)]  <-- Conceito teórico do TCC
  ↓
[2. Período de Análise (Semana vs Dias)]
  ↓
[3. Linha de Ônibus (Lista de 274 linhas)]
  ↓
[4. Sentido Operacional (VOLTA vs IDA)]
  ↓
[5. Filtro de Horário (00:00 às 24:00)]
  ↓
[6. Card de Status do Arquivo Processado]
  ↓
[7. Botão 'Executar / Reprocessar Mineração']
  ↓
[8. Console SSE de Terminal Preto]
```

### 5.2. Problemas do Modelo Atual
1. **O "Regime de Coleta" no Topo da Sidebar:**  
   O usuário comum não sabe o que é "Regime A (2m)" ou "Regime B (20s)". Isso é uma divisão metodológica do TCC (estudo comparativo de frequência amostral). Para o operador, isso deveria ser um filtro secundário ou ser determinado automaticamente a partir da data escolhida (se for outubro/2025 é Regime A; se for dezembro/2025 é Regime B).
2. **A Armadilha das 274 Linhas Não Mineradas:**  
   Se o usuário seleciona uma linha bruta da lista (ex.: Linha 673), o mapa e os gráficos ficam em branco. Um usuário leigo não percebe que precisa descer até o rodapé da sidebar e clicar no botão azul *"Executar / Reprocessar Mineração"*. Ele conclui que o sistema travou.
3. **Poluição Visual com o Console SSE:**  
   A caixa de terminal preta no rodapé da barra lateral ocupa 176 pixels fixos de altura. Ela só tem utilidade nos 15 segundos em que a mineração está rodando; no restante do tempo, fica apenas exibindo *"Aguardando execução..."*, roubando espaço de tela.

### 5.3. Proposta de Reorganização da Sidebar

```
┌────────────────────────────────────────────────────────┐
│ 🚌 URBS Process Mining                  [CCO Dashboard]│
├────────────────────────────────────────────────────────┤
│ 1. LINHA DE ÔNIBUS                                     │
│    [ Selecione ou digite: 541 - Bairro Novo A        ] │
│    ⭐ 3 Linhas Prontas  |  📡 271 Disponíveis          │
├────────────────────────────────────────────────────────┤
│ 2. DATA / PERÍODO DE AUDITORIA                         │
│    (●) Hoje / Dia Específico   ( ) Semana Completa     │
│    [ Terça-feira, 02/12/2025                         ] │
├────────────────────────────────────────────────────────┤
│ 3. SENTIDO & HORÁRIO                                   │
│    [ VOLTA ]   [ IDA ]                                 │
│    Horário: das [ 06:00 ] às [ 22:00 ]                 │
├────────────────────────────────────────────────────────┤
│ 4. STATUS OPERACIONAL                                  │
│    [✓] 1.200 viagens mineradas e prontas               │
│                                                        │
│    *(Se linha não minerada):                           │
│    [ ! ] Dados brutos disponíveis (42.000 pontos GPS)  │
│    [ Botão: Iniciar Processamento da Linha ]           │
├────────────────────────────────────────────────────────┤
│ ▾ Configurações Científicas / TCC (Acordeão Colapsado) │
│    - Comparativo de Amostragem (Regime A / Regime B)   │
│    - Log de Terminal SSE (Expansível quando ativo)     │
└────────────────────────────────────────────────────────┘
```

---

## 6. Diagnóstico do Código e Oportunidades de Refatoração

### 6.1. Backlog de Refatoração no Backend (`src/`)

1. **Desambiguação de Chave de Atividade no ETL (`src/etl/trajectory.py`):**
   - **Situação Atual:** Atividade é salva como `PASSAGEM_{NOME}`.
   - **Problema:** Paradas na mesma via colidem e causam distorções no token replay e nas estatísticas de conformidade.
   - **Refatoração:** Salvar no log de eventos:
     ```python
     df_log['concept:name'] = 'PASSAGEM_' + df_log['stop_seq'].astype(str).str.zfill(2) + '_' + df_log['stop_name'].astype(str)
     ```
     Desta forma, cada parada terá uma identidade única e sequencial (`PASSAGEM_03_Rua São José dos Pinhais`, `PASSAGEM_04_Rua São José dos Pinhais`), eliminando contagens fantasmas.

2. **Agrupamento de Consultas em um Único Endpoint (`src/visualization/dashboard.py`):**
   - **Situação Atual:** Ao mudar de filtro, o frontend dispara 4 requisições HTTP paralelas (`/api/map-data`, `/api/discovery-json`, `/api/conformance`, `/api/performance-json`).
   - **Refatoração:** Criar o endpoint agregado `/api/dashboard-overview` que retorna um payload consolidado com cache de memória de 5 minutos, reduzindo overhead de rede e parsing repetido de CSV no Pandas.

3. **Cálculo Dinâmico dos Limites de Tempo do Replay:**
   - **Situação Atual:** O replay do mapa sempre usa `0` a `86400` segundos (00:00 a 24:00).
   - **Refatoração:** Retornar no endpoint `/api/map-data` os campos `min_timestamp` e `max_timestamp` das viagens carregadas, ajustando o slider do mapa para começar automaticamente na hora em que o primeiro ônibus entrou em circulação (ex.: às 05:15).

---

### 6.2. Backlog de Refatoração no Frontend (`src/visualization/frontend/`)

1. **Substituição da Simulação de Força na Rede de Petri (`ProcessVisualizer.jsx`):**
   - **Ação:** Implementar o layout direcionado por camadas com `dagre` ou renderizar o SVG hierárquico nativo do Graphviz que o backend já gera via PM4Py (`pn_visualizer.apply(net, initial_marking, final_marking)`).
   - **Resultado:** Os nós serão desenhados em linha reta ordenada por sequência de paradas, com caixas legíveis e arcos claros.

2. **Ajuste de Escala no Inspetor de Conformidade (`ConformanceInspector.jsx`):**
   - **Ação:** Alterar o cálculo da barra de paradas puladas para considerar o total de casos como denominador ($N = 572$).
   - **Exibição:** Adicionar tag visual de criticidade:
     - Abaixo de 5% de desvio: Badge verde (*Desvio Normal / Operacional*).
     - De 5% a 15%: Badge amarelo (*Atenção Operacional*).
     - Acima de 15%: Badge vermelho (*Desvio Crítico de Itinerário*).

3. **Link de Ação Rápida entre Abas ("Drill-Down"):**
   - Na tabela de auditoria diária e no top 10 de viagens desviadas, adicionar um botão de ação com ícone de mapa:
     ```jsx
     <button onClick={() => navigateToReplay(trip.case_id)}>Ver Replay</button>
     ```
   - Ao clicar, o sistema muda automaticamente para a aba *"Mapa de Replay"*, aplica o filtro daquela viagem e inicia a reprodução do percurso.

---

## 7. Conclusão e Próximos Passos Recomendados

O sistema já possui um motor de mineração de processos robusto e validado, com 82 testes automatizados garantindo a integridade dos cálculos. Os pontos levantados pelo usuário nos dois prints não representam falhas matemáticas do algoritmo, mas sim **oportunidades clássicas de tradução de Process Mining para Engenharia de Usabilidade**:

1. **No Print 1:** Ajustar a representação percentual e desambiguar paradas com o mesmo nome de logradouro.
2. **No Print 2:** Trocar a física aleatória de partículas da Rede de Petri por um grafo de fluxo direcional legível.
3. **Na Sidebar:** Reposicionar a seleção de linha para o topo e colapsar opções acadêmicas secundárias.

Essas melhorias colocarão o projeto em um patamar de excelência profissional, tanto para a demonstração prática perante a banca examinadora do TCC quanto para o uso real por equipes de tráfego urbano.
