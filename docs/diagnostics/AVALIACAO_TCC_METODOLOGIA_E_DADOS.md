# Avaliação do TCC, Decisão de Metodologia e Origem dos Dados Comparados

> **Data:** 2026-09-11
> **Contexto:** Responder a três pontos — (1) avaliação da ideia do TCC; (2) porção (a) da decisão de metodologia textual; (3) a questão sobre qual data se compara com qual ("histórico vs minerado pela API"). Insumo para o futuro **Plano de Implementação** do TCC/code.

---

## A. Avaliação da Ideia do TCC (API URBS → Process Mining)

A ideia é **forte e bem escolhida**, por cinco motivos:

1. **Operação de ônibus é naturalmente um processo** — a sequência planejada e repetível de passagens permite usar `case/activity/timestamp` com honestidade.
2. **Dados verdadeiramente abertos** — coletar a própria telemetria da API (`data/dados_em_tempo_real_2026`, `data/dados_c3sl`) confere reprodutibilidade real.
3. **A contribuição é engenharia do event log** — reconstrução de pings ruidosos/esparsos em eventos `PASSAGE` discretos — e não mais um dashboard.
4. **Escopo defensável** — sem ground truth de AVL, as alegações se circunscrevem a **conformidade topológica normativa** e reconstrução trajetória; além disso, não valem alegações de pontualidade fina.
5. **A plataforma excede o escopo típico de TCC** — backend FastAPI + frontend geoespacial com replay lógico/físico, o que aumenta o valor demonstrativo.

**Ressalva do agente:** escolher, para validação, sempre a **metodologia implementada** (ver B abaixo).

---

## B. Decisão de Metodologia: manter a implementada (HMM/PCHIP) — OPINI FINAL

**Decisão aprovada (opção a):** o texto do TCC deve descrever a **metodologia realmente implementada**:

```
Limpeza de telemetria → segmentação do case por inversão de SENT/gap=10min
→ Map Matching HMM/Viterbi no shape → interpolação temporal PCHIP
→ evento PASSAGE → modelo normativo sequencial → token replay (Trace Fitness)
→ DFG de performance → atraso vs Tabela.
```

**Justificativa:**
- As citações do referencial (Borges 2023 = interpolação; Martins 2022 = map matching) **suportam essa metodologia**;
- Meu desenho de referência (pensado antes de ler o código) coincide com a solução implementada — ou seja, a solução faz sentido;
- "Geofencing/junção espacial" (como aparece no sumário do PDF) seria *downgrade* artificial.

**Pendente:** reescrever o Cap. 3 (Metodologia) e 4 (Resultados) com essa descrição e os números reais do repositório (82 testes, 541, Regime A/B).

---

## C. Origem dos Dados Comparados (a dúvida)

**Sim — e esclarecida a semântica da comparação:**

O pipeline compara **planejado (cadastro estático da URBS)** com **executado (telemetria minerada da API)**.

| Lado | Origem | Conteúdo | Papel no PM |
|---|---|---|---|
| **Planejado / Dados "históricos"** | `data/dados_c3sl/*.json.xz` (backup histórico da URBS arquivado pelo C3SL), com fallback na própria API/cache `data/static_cache` | `pontosLinha` (SEQ/NUM/NOME/SENTIDO georreferenciado), `tabelaLinha` (DIA, PONTO, HORA, TABELA), `shapeLinha` (geometria) | Modelo normativo (`create_normative_petri_net`) |
| **Executado / Minerado "pela API"** | `data/dados_em_tempo_real_2026/YYYY-MM-DD/*.csv` (coletado via API em tempo real) | `COD, REFRESH, LAT, LON, CODIGOLINHA, TABELA, SITUACAO, SENT, request_timestamp` | Reconstrução da Execução (`trajectory.py`) → `PASSAGE` events conformes/omitidos |

**Observação:** se a intenção era comparar **bruto arquivado (API) vs. minerado** — auditoria de qualidade da reconstrução — isso **não está automatizado** (o dashboard serve o log minerado direto). É um experimento ótimo para a seção 3.5 ("Validação da Metodologia") do capítulo.

---

## D. Comparativo do Agente vs. Código (itens de mudança propostos)

| Prioridade | Mudança | Status na vcpu |
|:---:|:---|:---:|
| P0 | Não fabricar eventos para paradas fora do geofence (omitir) | ✅ implementado (TDD green phases) |
| P1 | Chave canônica `PASSAGEM_{SEQ:02d}_{NOME}` | Pendente |
| P1 | Fallback de segmentação por reversão de `cum_dist` se `SENT` faltar | Pendente |
| P2 | Propagar `interpolated` ao PM (excluir de DFG/atraso ou ponderar) | Pendente |
| P2 | Sweep σz/β no HMM e publicação como anexo | Pendente |
| P0 | Capítulos 3–5 do PDF (atualmente VAZIOS) | **Crítico** |

---

## E. Próximos Passos (entrada para o Plano de Implementação)

1. **Escrever o Cap. 3 (Metodologia)** com a descrição real do pipeline (itens de B).
2. **Escrever o Cap. 4 (Resultados)** com os números do repositório (82 testes, Regime A/B, linha 541, gargalos do DFG).
3. **Corrigir o sumário** do PDF (retirar "Geofencing/Junção Espacial" e placeholders: ilustrções de pré-escola/glândulas, lista de ilustrações template, folha de aprovação).
4. **Aplicar as mudanças P1/P2** para eliminar o gap metodológico remanescente.
