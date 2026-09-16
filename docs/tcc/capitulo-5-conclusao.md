# Capítulo 5 — Conclusão

> Rascunho para revisão. Estrutura: retomada dos objetivos, contribuições, limitações e trabalhos futuros.

## 5.1 Retomada dos Objetivos e Síntese das Contribuições

O objetivo geral — transformar dados brutos de GPS da API pública da URBS em logs de eventos estruturados por Mineração de Processos — foi atingido via engenharia de pipeline composta por: limpeza de telemetria, segmentação de cases por inversão de `SENT`/gap temporal, projeção HMM/Viterbi sobre shape e estimativa temporal com PCHIP monotônico, e exportação em XES para PM4Py.

Contribuições principais:

1. **Engenharia do event log com qualidade explícita** — cada evento `PASSAGE` carrega `interpolated`, permitindo segregar incerteza de sensor da conformidade operacional; paradas sem evidência são omitidas.
2. **Descoberta (Inductive Miner)** do modelo real por viagem e direção.
3. **Conformidade (token replay)** com modelo normativo sequencial derivado do cadastro URBS, quantificando desvios.
4. **Desempenho (DFG)** com segmentos críticos saudáveis no Regime B e ranking de gargalos.
5. **Plataforma operacional completa** (backend FastAPI + frontend geoespacial), demonstrável.
6. **Reprodutibilidade** com 82 testes automatizados cobrindo o pipeline e o dashboard.

## 5.2 Limitações do Trabalho

- Escopo restrito à **conformidade topológica normativa** — o pipeline não audita tempo de embarque físico no patamar de abertura/fechamento de portas.
- Sensibilidade à taxa de amostragem; o Regime A (120s) produz fitness reduzido por limiar de geocerca.
- Validade externa limitada a uma linha (541) e dois períodos; a comparação entre regimes por *downsampling* é suscetível ao paradoxo de Simpson em desenho subótimo.
- O sweep σz/β está pendente como anexo metodológico; o raw do Regime B não está no repositório.
- A associação viagem–TABELA ancora no horário planejado, o que pode induzir premissa de conformismo na associação das viagens.
- O filtro de outliers por **distância à parada** (500m) pode descartar pings legítimos em trechos esparsos e censurar viagens em desvio real; a métrica mais correta — distância ao traçado físico — fica como melhoria (tarefa F1.7).

## 5.3 Propostas de Trabalhos Futuros

1. Sweep σz ∈ [10,50]m × β ∈ [20,100]m com medidas de estabilidade de gargalos, publicado como anexo.
2. Chave canônica de atividade por identidade de parada (`PASSAGEM_{SEQ}_{NOME}`), eliminando colisão latente de nomes.
3. Propagar `interpolated` ao motor PM: excluir/ponderar eventos interpolados no timing DFG e na detecção de atraso.
4. Correção de encoding na gravação do CSV (remover `_fix_encoding`).
5. Taxa de Censura Operacional reportada como métrica de qualidade do pipeline.
6. Ampliação para mais linhas e validação externa com fontes AVL/autenticação, mediante aporte da URBS.