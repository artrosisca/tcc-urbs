# Capítulo 5 — Conclusão

> Rascunho para revisão. Estrutura: retomada dos objetivos, contribuições, limitações e trabalhos futuros.

## 5.1 Retomada dos Objetivos e Síntese das Contribuições

O objetivo geral — transformar dados brutos de GPS da API pública da URBS em logs de eventos estruturados por Mineração de Processos — foi atingido via engenharia de pipeline composta por: limpeza de telemetria, segmentação de cases por inversão de `SENT`/gap temporal, projeção HMM/Viterbi sobre shape e estimativa temporal com PCHIP monotônico, e exportação em XES para PM4Py.

Contribuições principais:

1. **Engenharia do event log com qualidade explícita** — cada evento `PASSAGE` carrega `interpolated`, permitindo segregar incerteza de sensor da conformidade operacional; paradas sem evidência são omitidas.
2. **Descoberta (Inductive Miner)** do modelo real por viagem e direção.
3. **Conformidade (token replay)** com modelo normativo sequencial derivado do cadastro URBS, quantificando desvios com chaves canônicas de atividade que evitam ambiguidade.
4. **Desempenho (DFG)** com segmentos críticos saudáveis no Regime B e ranking de gargalos imune à poluição de interpolação não observada.
5. **Plataforma operacional completa** (backend FastAPI + frontend geoespacial), demonstrável.
6. **Reprodutibilidade** com 89 testes automatizados cobrindo o pipeline e o dashboard.

## 5.2 Limitações do Trabalho

- Escopo restrito à **conformidade topológica normativa** — o pipeline não audita tempo de embarque físico no patamar de abertura/fechamento de portas.
- Sensibilidade à taxa de amostragem; o Regime A (120s) produz fitness reduzido por limiar de geocerca.
- Validade externa limitada a uma linha (541) e dois períodos; a comparação entre regimes por *downsampling* é suscetível ao paradoxo de Simpson em desenho subótimo.
- O raw do Regime B não está presente fisicamente no repositório por volume.
- A associação viagem–TABELA ancora no horário planejado, o que pode induzir premissa de conformismo na associação das viagens.

## 5.3 Propostas de Trabalhos Futuros

1. Construção de um *sweep* metodológico automatizado para os parâmetros de Map Matching (σ_z ∈ [10,50]m × β ∈ [20,100]m), correlacionando-os à estabilidade topológica do gargalo.
2. Ampliação para mais rotas e consolidação do painel como ferramenta preditiva.
3. Obtenção de validação externa em campo ou cruzamento com dados reais de bilhetagem eletrônica.