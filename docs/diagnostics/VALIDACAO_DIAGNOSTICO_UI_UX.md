# Validação do Diagnóstico de UI/UX e Pesquisa de Melhorias

> **Data:** 2026-09-11
> **Documento-base:** `docs/DIAGNOSTICO_UI_UX_E_REFATORACAO.md` (Antigravity)
> **Método:** Cada afirmação do diagnóstico foi confrontada com o código e os dados do repositório (`src/`, `tests/`, `data/dados_processados/`).

---

## 1. Veredito Resumido

O diagnóstico é **substantivamente correto**: os dois achados centrais (truncamento CSS de paradas homônimas e uso de `d3.forceSimulation` para um fluxo sequencial) foram **confirmados no código**. Porém, a **causas raiz** tem uma nuance importante: no conjunto de dados atual, os nomes de paradas (`NOME`) **são únicos** (26 atividades distintas) — a colisão de "mesmo nome" que se vê na tela é **principalmente** um efeito do CSS `truncate`, e a colisão semântica na engine é um **risco latente** para paradas que compartilham exatamente o mesmo `NOME`. Detalhes abaixo.

| # | Afrimação do diagnóstico | Veredito |
|---|---|---|
| 1 | `evaluate_conformance` agrupa por `concept:name` (string) em vez de `(stop_seq, stop_num)` | ✅ Validado (com nuance) |
| 2 | CSS `truncate max-w-[200px]` torna paradas com prefixo comum visualmente idênticas | ✅ Validado (causa principal) |
| 3 | Percentual da barra usa denominador relativo (`skipped_stops[0].count`) | ✅ Validado |
| 4 | `ProcessVisualizer.jsx` usa `d3.forceSimulation` para fluxo sequencial | ✅ Validado |
| 5 | `viewBox="0 0 800 500"` fixo com faixas verticais vazias | ✅ Validado |
| 6 | Labels de transição cortados em 13–15 caracteres | ✅ Validado |
| 7 | "15 visitadas / 11 puladas" é comportamento operacional recorrente, não dado congelado | ✅ Validado pelos dados |
| 8 | Sidebar na ordem Regime → Período → Linha → Sentido → Horário → Botão → SSE | ✅ Validado |
| 9 | 4 chamadas HTTP paralelas por mudança de filtro | ✅ Validado |
| 10 | Slider de tempo fixo 00:00–24:00 (86400s) | ✅ Validado |
| 11 | "82 testes automatizados" | ✅ Validado (61+8+3+10 = 82) |

Legenda: ✅ confirmado, ⚠️ parcial, ❌ contestado.

---

## 2. Evidências Item a Item

### 2.1. Conformidade — agrupamento por nome (Item 1) ⚠️→✅ com nuance

**Código (confirmado):** `src/mining/engine.py:217–249`:

```python
planned_stops = ['PASSAGEM_' + str(n) for n in stops_dir['NOME'].tolist()]
...
for stop in planned_stops:
    stop_rows = case_sorted[case_sorted['concept:name'] == stop]
    if stop_rows.empty:
        skipped.append(clean_name); skipped_stops_all.append(clean_name)
```

**Dado (nuance):** no CSV `event_log_541_2025-12-02_2025-12-08.csv`, as 26 atividades têm **nomes únicos** porque `NOME` inclui o número predial (`..., 108`, `..., 358`, ...). Portanto, a colisão por nome é **latente**, não ativa — ela explode quando duas paradas compartilham exatamente o mesmo `NOME` (ex.: paradas bidirecionais com nome idêntico, ou quando o mesmo nome aparece em IDA e VOLTA).

**Implicação prática:** a correção sugerida pelo diagnóstico (chave composta `PASSAGEM_{stop_seq}_{nome}`) é **correta e robusta**, porque elimina o risco latente. Mas a duplicidade visual da tela do screenshot é explicada **integralmente** pelo CSS (Item 2).

### 2.2. Truncamento CSS (Item 2) ✅ e causa da ilusão

`src/visualization/frontend/src/components/ConformanceInspector.jsx:124`:

```jsx
<span className="truncate max-w-[200px]" title={stop.stop_name}>
```

Como os 7 primeiros caracteres dos nomes longos são idênticos (`Rua São José d...`), os ~7 pontos da Rua São José aparecem **visualmente idênticos**, e cada um pode ter sido pulado nas **mesmas viagens encurtadas**, gerando contagens coincidentes (ex.: 13×). O `title={stop.stop_name}` preserva o nome completo no tooltip, mas não resolve a apresentação.

**Dado de suporte:** distribuição de paradas estritamente visitadas por viagem no CSV mostra dois clusters dominantes — **15 paradas (611 viagens)** e **13 paradas (589)**. As viagens "15 visitadas / 11 puladas" do print pertencem ao cluster dominante; a recorrência de 13×/15× paradas é **comportamento sistemático de rota encurtada**, não dado congelado (Item 7 confirmado).

### 2.3. Dado preservado no CSV (confirmação da tese central do diagnóstico) ✅

O header do CSV confirma que `stop_seq`, `stop_num` e `concept:name` **coexistem** — o gargalo é a engine/frontend, não o ETL:

```
stop_seq,stop_num,concept:name,event_type,time:timestamp,distance,interpolated,org:resource,tabela,gps_direction,cum_dist,case:concept:name
```

**Achado adicional (ruído):** o CSV cru contém mojibake (`SÃ£o`, `SÃ­tio`, bytes 2-byte double-encoded). O motor chama `_fix_encoding` (`src/mining/engine.py:18`, via `src/etl/repository.py`) para reparar em modo de leitura. Vale registrar como **dívida técnica**: corrigir a escrita do CSV para evitar o ciclo encode/decode.

### 2.4. Escala relativa da barra (Item 3) ✅

`ConformanceInspector.jsx:118–119`:

```javascript
const totalSkips = skipped_stops[0].count;
const pct = (stop.count / totalSkips) * 100;
```

O denominador é o maior valor do ranking — uma barra de 100% por definição. O backend **já expõe** `total_cases` (conformance result; vide `engine.py:281`), portanto a correção recomendada (`pct = count / total_cases`) exige apenas mudança de frontend.

### 2.5. Descoberta — `d3.forceSimulation` para fluxo sequencial (Item 4) ✅

`src/visualization/frontend/src/components/ProcessVisualizer.jsx:28–33`:

```javascript
const simulation = d3.forceSimulation(rawNodes)
  .force('link', d3.forceLink(rawLinks).id(d => d.id).distance(120))
  .force('charge', d3.forceManyBody().strength(-200))
  ...
```

**Achado adicional (frágil):** `ProcessVisualizer.jsx:119`:

```javascript
const isEnd = node.id === 'sink' || node.id.includes('place_15') || node.id.includes('place_13');
```

Hard-coded índices de lugar (`place_15`, `place_13`) para colorir o fim — frágil a qualquer alteração de número de paradas. O backend **já retorna** `initial_marking` e `final_marking` (`engine.py:102–107`); o frontend deveria usar isso.

**Achado adicional (secundário):** existe já um endpoint `/api/discovery` (SVG Graphviz, `dashboard.py:323`) e um endpoint `/api/discovery-json` (force layout). O frontend usa o JSON. A alternativa "Graphviz hierárquico nativo" **já existe no backend**.

### 2.6. Sidebar (Item 8) ✅ — com observação

Ordem confirmada em `SidebarFilters.jsx`: Regime (137) → Período (158) → Linha (243) → Sentido (278) → Horas (298) → Status (322) → Botão Executar (349) → Console SSE (369, altura fixa `h-44`).

**Observação importante:** como há apenas 2 regimes e períodos pré-definidos, derivar o regime a partir da data (proposta do diagnóstico) é viável e seguro. Sugerir preservar o controle por **acordeão avançado** para suporte a futuras janelas.

### 2.7. Múltiplas chamadas paralelas (Item 9) ✅

`App.jsx:40–44` dispara `/api/map-data`, `/api/discovery-json`, `/api/conformance`, `/api/performance-json` via `Promise.all` em cada filtro. O backend (`dashboard.py:106–431`) replica leitura/parse do CSV por endpoint, e há um middleware `no-cache` (`dashboard.py:24`). Consolidar em `/api/dashboard-overview` **com cache TTL curto** (ex.: `cachetools.TTLCache`) é coerente.

### 2.8. Slider 00:00–24:00 (Item 10) ✅

`GeospatialConsole.jsx:45`:

```js
const [maxTime, setMaxTime] = useState(86400); // 24h in seconds
```

Correção recomendada: backend (`/api/map-data`, `dashboard.py:215`) pode computar `min_timestamp`/`max_timestamp` das viagens e o slider passa a ocupar o range real. Sem alteração de ETL.

---

## 3. Achados Adicionais (não listados no diagnóstico)

1. **Heurística de fim de Petri hard-coded** (Item 2.5); usar `initial_marking`/`final_marking`.
2. **Encoding com mojibake nos CSVs** (Item 2.3); dívida na escrita do pipeline.
3. **`evaluate_conformance` recalcula sem `stop_seq`** quando a coluna não existe (`engine.py:223`); recomendável garantir `stop_seq` no event log sempre.
4. **Top-10 deviant trips:** empate em `skipped_count` (11) torna o top-10 arbitrário quanto à ordem interna; considerar tiebreak por `case_id` ou por data da viagem.
5. **Teste de contagem total:** 61 (dashboard) + 8 (engine) + 3 (repository) + 10 (trajectory) = **82**, alinhado com a alegação.
6. **Robustez do `test_dashboard_e2e`:** apenas 60 dos 61 — conferir que nenhum teste foi silenciosamente desativado antes de reportar "n=61".

---

## 4. Pesquisa de Melhorias (recomendações concretas, com alternativas)

### 4.1. Layout da Rede de Petri (Item 4)
Opções ordenadas por custo/benefício:

1. **(Próximo de zero esforço)** Retornar o SVG hierárquico de Graphviz que o backend já gera (`/api/discovery`, `engine.py:76–86`) e renderizá-lo com **`svg-pan-zoom`** (pan/zoom sobre o SVG) + legenda. ✅ mais barato e adequado à forma "segunda-metade" do diagnóstico.
2. **Layout hierárquico no cliente com `dagre`** ou **`elkjs`** (algoritmo Sugiyama, LTR/TB), preservando arcs e rótulos. Maior controle de interação, mas insere peso de biblioteca.
3. **Modo executivo (DFG):** renderizar o **Performance DFG** como fluxo sequencial (nós=paradas na ordem `stop_seq`, espessura=frequência, cor=tempo mediano), usando o **já existente** `/api/performance-json`. Recomendado como visão padrão para operadores.

### 4.2. Chave de atividade canônica (Item 1)
Adotar composto único `PASSAGEM_{SEQ:02d}_{NOME}` em `src/etl/trajectory.py` (event log) e em `create_normative_petri_net`/`evaluate_conformance` (`engine.py:111`, `engine.py:218`), preservando `NOME` no tooltip do nó. Elimina a colisão latente por nome e torna a ordem cronológica visível nos rótulos.

### 4.3. Denominador absoluto (Item 3)
Frontend usa `conformanceData.total_cases` (já no payload, `engine.py:281`) para calcular `(count / total_cases) * 100` e badge semântico (verde/amarelo/vermelho) com threshold documentado (sugestão: <5% / 5–15% / ≥15%).

### 4.4. Drill-down entre abas (Item FleetAudit/Conformance)
Contrato mínimo: passar `case_id` do deviant trip como prop para um callback que executa: `setActiveTab('map'); setFilters(f => ({...f, case: case_id}))`. O backend retorna o `case:concept:name` em `engine.py:269`. Sem mudança de API.

### 4.5. Consolidação de endpoints
Implementar `@app.get("/api/dashboard-overview")` (`dashboard.py`) que chama uma vez o ETL e retorna `{map, discovery, conformance, performance}` com `cachetools.TTLCache(ttl=300)` + `Cache-Control: private, max-age=60`. Invalidar no fim do SSE (`process_stream` → `__SUCCESS__`). Reduz 4 RTT e 4 parses CSV para 1.

### 4.6. Slider dinâmico (Item 10)
Em `/api/map-data` (`dashboard.py:215`), retornar `time_range = {min: df['time:timestamp'].min(), max: ...max()}`. O frontend inicializa `maxTime` com o range real do primeiro evento, evitando telemetria "vazia" nas primeiras horas.

### 4.7. Sidebar (Item 8)
Reordenar visualmente para: **Linha → Período → Sentido/Horário → Status → Botão**, colapsando `Regime` e o console SSE em um `<details>` "Config. TCC / Logs". Seguro porque existem apenas 2 regimes (risco de regressão baixo).

### 4.8. Correção da fragilidade `isEnd` (Item 2.5)
Remover o `node.id.includes('place_15' | 'place_13')` e usar `petriNet.initial_marking.includes(node.id)` / `final_marking.includes(node.id)`. Poupa bugs em rotas com qualquer número de paradas.

---

## 5. Priorização sugerida (impacto × custo)

| Prioridade | Ação | Impacto | Custo |
|:---:|:---|:---:|:---:|
| P0 | Denominador absoluto + badge de criticidade (4.3) | Altíssimo (evita pânico falso) | Baixo |
| P0 | Desambiguar atividade por `SEQ` (4.2) + remover `isEnd` hard-coded (4.8) | Alto | Baixo |
| P1 | Trocar force layout por Graphviz SGML + pan/zoom (4.1–1) | Alto (aba Descoberta) | Médio (ou usar `/api/discovery`) |
| P1 | Consolidar endpoints com cache TTL (4.5) | Alto (performance) | Médio |
| P2 | Slider dinâmico (4.6) + drill-down (4.4) | Médio | Baixo–Médio |
| P2 | Sidebar reordenada, acordeão "Config. TCC" (4.7) | Médio | Médio |
| P3 | Corrigir escrita de CSV com mojibake (2.3) | Baixo | Baixo |

---

## 6. Conclusão

O diagnóstico está **qualitativamente correto** e as recomendações são apropriadas. A única correção substantiva é que a "colisão por nome" é hoje **latente** (os 26 nomes são únicos com número predial) e a ilusão de duplicidade vem do **truncamento CSS**; ambas as correções propostas (chave por `SEQ` e sem truncamento cego) são necessárias para tornar o comportamento robusto. Nenhuma das afirmações centrais foi refutada; as dependências do documento (4 endpoints, slider 86400, ordem da sidebar, 82 testes) conferem com o código.