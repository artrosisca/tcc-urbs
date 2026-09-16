# Plano de Implementação — Alinhamento TCC ↔ Código ↔ UI/UX

> **Data:** 2026-09-11
> **Fontes (rastreabilidade):**
> - `docs/DIAGNOSTICO_UI_UX_E_REFATORACAO.md` (diagnóstico original Antigravity)
> - `docs/diagnostics/VALIDACAO_DIAGNOSTICO_UI_UX.md` (validação com vereditos por item)
> - `docs/diagnostics/AVALIACAO_TCC_METODOLOGIA_E_DADOS.md` (decisões de metodologia e origem dos dados)
>
> **Objetivo:** fechar o gap entre (a) a metodologia descrita no texto do TCC, (b) o pipeline de mineração real e (c) a experiência do usuário, sem regressões nos 82 testes atuais.

---

## Organização

- **F0 — Escrita do TCC (BLOQUEADOR PRINCIPAL):** Caps. 3, 4 e 5 do PDF estão vazios.
- **F1 — Alinhamento metodológico-código (P1/P2):** mudanças no pipeline com validação por testes.
- **F2 — Refatoração UI/UX (P1–P3):** tradução do diagnóstico de UI/UX.
- **F3 — Higiene/regressão final:** limpar template, reexecutar suíte completa e rebuild do frontend.

Orde da marcha recomendada: **F0 (contrato textual) → F1 (código) → F2 (UI) → F3 (ciatação).** Itens dentro de cada fase são independentes, salvo os marcados "depende".

---

## F0 — Escrita do TCC (prioridade máxima)

| ID | Tarefa | Critério de aceite |
|---|---|---|
| F0.1 | Remover placeholders do template (listas de ilustrações/tabelas, folha de aprovação, agradecimentos) | PDF sem itens de pré-escola/glândulas/empréstimos; folha de aprovação preenchida |
| F0.2 | Reescrever Cap. 3 (Metodologia) para descrever pipeline **implementado**: limpeza → segmentação (SENT/gap=10min) → HMM/Viterbi → PCHIP → evento `PASSAGE` → normativo sequencial → token replay | Título das seções 3.3/3.4 condiz com o pipeline (não mais "Geofencing/Junção Espacial") |
| F0.3 | Redigir Cap. 4 (Resultados) com números do repositório (linha 541, Regime A/B, gargalos DFG, 82 testes, taxa de censura) | Pelo menos uma tabela/figura por seção 4.2–4.4 com dados reais |
| F0.4 | Redigir Cap. 5 (Conclusão), Limitações e Trabalhos Futuros | Ressalva escopada: conformidade topológica (não pontualidade fina) |
| F0.5 | Atualizar resumo/abstract para refletir a decisão de metodologia | Palavras "Geofencing" substituídas por "Map Matching/pchip" |

> O que sai daqui define o contrato com F1/F2 (termos e escopo) — por isso é F0.

---

## F1 — Alinhamento metodologia ↔ código (P0 e P1)

### F1.A — Já implementado nesta sessão (baseline verde)
- ✅ Paradas fora do geofence **omitidas** da log (`match_trip`, `src/etl/trajectory.py:387`) — validado por `test_match_trip_omits_skipped_stops_exceeding_threshold`.
- ✅ `n.maximum.accumulate` removido (colapso de rotas circulares) — validado por `test_stop_shape_idx_does_not_collapse_in_circular_route`.
- ✅ Suíte local 100%: 10 testes em `test_trajectory_reconstruction.py`; E2E do dashboard 60/60.

### F1.B — A fazer (ordem sugerida)

| ID | Tarefa | Arquivo(s) | Critério de aceite |
|---|---|---|---|
| F1.1 | ✅ **CONCLUÍDO** — **Chave canônica de atividade** por identidade: `PASSAGEM_{SEQ:02d}_{NOME}` + helpers `activity_name_for_stop`/`strip_activity_name` em `repository.py`; conformidade e map-data passam a casar por `stop_seq` (log legado normalizado em memória). **Efeito:** eliminou "pulas fantasma" — Regime B passou de fitness 0,98/0,99 (com 572 pulas espúrias) para 0,9966/1,0000 com 0 pulas em VOLTA; Cap. 4 atualizado. Suíte: 83/83. |
| F1.2 | ✅ **CONCLUÍDO** — **Fallback de segmentação** por reversão de progresso curvilíneo (`_segment_group_trips` com máquina de estados arma/desarma; sem corte em cascata). `SENT` ausente/nulo não quebra mais o pipeline (`KeyError` eliminado). Teste `test_segmentation_fallback_progress_reversal` verde; suíte 84/84. |
| F1.3 | ✅ **CONCLUÍDO** — **`interpolated` propagado ao PM:** `analyze_segment_performance` exclui segmentos com endpoints fabricados e reporta `interp_ratio`/`observed_passages`; `analyze_performance` (DFG PM4Py) filtra eventos fabricados; `analyze_schedule_delays` exclui partidas fabricadas. **Efeito:** arco crítico Regime B passou de 5,23 min (n=611 contam.) para 7,12 min em n=186 observados (69,6% interp) — Cap. 4 atualizado. Suíte: 86/86. |
| F1.4 | **Sweep σz/β do HMM** como anexo metodológico: grid 10–50m × 20–100m e estabilidade de gargalos | Notebooks/experiment; relatório em anexo | ρ/ICC por combinação, documentado |
| F1.5 | ✅ **CONCLUÍDO** — **Corrigir escrita do CSV** (mojibake `SÃ£o`/`SÃ­tio`): `_fix_encoding` aplicado em `concept:name` antes de `to_csv` em `reconstruct_event_log`. Teste `test_reconstruct_event_log_writes_clean_utf8` verde; suíte: 87/87. |
| F1.6 | **Taxa de Censura Operacional** reportada (viagens descartadas >90% interpoladas) — já pontuada pela banca | `reconstruct_event_log` | CSV/metadado com percentual descartado por linha/faixa horária |
| F1.7 | **Revisar filtro de outliers 500m**: substituir "distância à parada" por "distância ao shape" (evita descartar pings legítimos em trechos esparsos e censurar desvios reais) | `clean_telemetry` (`trajectory.py:71-86`) | Teste unitário com paradas esparsas >1km; pings do meio do trecho não são descartados |

---

## F2 — Refatoração UI/UX (diagnóstico validado)

### F2.A — Conformidade (P0 de UI)
| ID | Tarefa | Arquivo | Critério de aceite |
|---|---|---|---|
| F2.1 | **Denominador absoluto** da barra: `(count / total_cases) * 100` + badge semântico | `ConformanceInspector.jsx` | Nenhuma barra chega a 100% por ser a maior; 13/572 ⇒ 2,3%; badges verde/amarelo/vermelho |
| F2.2 | **Desambiguar visualmente** paradas: `[#$SEQ]` e nome completo (ou coluna `stop_num`) | `ConformanceInspector.jsx`; payload passa a trazer `stop_seq`/`stop_num` | Paradas da mesma via deixam de aparecer idênticas |

### F2.B — Descoberta (Petri)
| ID | Tarefa | Arquivo(s) | Critério de aceite |
|---|---|---|---|
| F2.3 | **Substituir force layout** por (a) SVG Graphviz já existente em `/api/discovery` com `svg-pan-zoom` ou (b) `dagre/elkjs` LTR | `ProcessVisualizer.jsx`; escolha documentada | Fluxo sequencial legível; nós não sobrepostos; arcos direcionais |
| F2.4 | Remover **hardcoded** `node.id.includes('place_15'/'place_13')` e usar `initial/final_marking` do backend | `ProcessVisualizer.jsx` | Fim/início coloridos corretamente para qualquer número de paradas |
| F2.5 | **Alternância Modo Executivo (DFG)/Modo Teórico (Petri)** | `ProcessVisualizer.jsx` + aba | Default executivo sequencial; modo teórico com legenda e pan/zoom |

### F2.C — Consolidação e desempenho (P1–P2)
| ID | Tarefa | Critério de aceite |
|---|---|---|
| F2.6 | **`/api/dashboard-overview`** e `TTLCache(ttl=300)` com invalidação no fim do SSE | `dashboard.py` | 1 RTT consolidado; endpoints individuais continuam verdes |
| F2.7 | **Slider dinâmico** via `time_range` do `/api/map-data` em vez de 0–86400 ffx | `GeospatialConsole.jsx` + backend | Slider inicia no primeiro evento real; sem "horas vazias" |
| F2.8 | **Drill-down** tabela deviant fleet/auditoria → mapa com `case_id` | `FleetAuditView.jsx`, `ConformanceInspector.jsx`, `GeospatialConsole.jsx` | Clicar na linha abre replay da viagem |

### F2.D — Sidebar (P2)
| ID | Tarefa | Critério de aceite |
|---|---|---|
| F2.9 | Reordenar: Linha → Período → Sentido/Horário → Status → Botão; regime e SSE em `<details>` "Config. TCC / Logs" | `SidebarFilters.jsx` | Fluxo operacional no topo |
| F2.10 | Auto-derivar regime por data (opcional, consultar usuário) | `SidebarFilters.jsx` | Se futuro não-uso do regime, o seletor pode virar "Visualização" |

---

## F3 — Higiene/Regressão

| ID | Tarefa | Critério de aceite |
|---|---|---|
| F3.1 | `npm --prefix src/visualization/frontend run build` | Build verde |
| F3.2 | `.venv/bin/pytest tests/` | **82 testes passam** (61 E2E + 8 engine + 3 repository + 10 trajectory + F1 novos) |
| F3.3 | Lint rápido (`oxlint`) sem novos erros | Sem warnings bloqueantes |
| F3.4 | Rodada com a banca (roote de verificação) | Checklist de aceite por fase |
| F3.5 | **Ressincronizar texto/números** dos Caps. 3–5 após F1/F2 (reexecutar `tcc_metrics.py` e atualizar tabelas) | `docs/tcc/*.md` batem com o código final |

---

## Riscos e observações

1. **F1.1 (chave canônica)** pode alterar rótulos de atividades visíveis nos gráficos — exige passagem e re-teste da suíte completa.
2. **F2.6** deve manter endpoints individuais funcionando (não remover) e validar na suíte E2E (61).
3. **F1.4 (sweep)** pode ser conduzido em paralelo com a escrita (F0), sem bloquear a banca.
4. A escolha em **F2.3** (Graphviz nativo vs. dagre) deve ser registrada; recomendado Graphviz nativo por custo.

## Anexos dos documentos-fonte
- Diagnóstico e causas raiz: `docs/DIAGNOSTICO_UI_UX_E_REFATORACAO.md`
- Validação/evidência/vereditos: `docs/diagnostics/VALIDACAO_DIAGNOSTICO_UI_UX.md`
- Decisão de metodologia e origem dos dados: `docs/diagnostics/AVALIACAO_TCC_METODOLOGIA_E_DADOS.md`