# Sumário do TCC — Versão 2 (Enxuta e Equilibrada)

Este documento registra a **Versão 2 (v2)** do Sumário Geral do TCC. Esta versão equilibra perfeitamente o texto que já foi redigido nos capítulos iniciais do `TCC_DEFINITIVO` com a maturidade técnica e rigor algorítmico do pipeline implementado (Capítulos 3, 4 e 5).

---

## 1. Estrutura Canônica do Sumário (Normas ABNT / UTFPR)

```text
1 INTRODUÇÃO .................................................................... 15
  1.1 OBJETIVOS ................................................................. 17
      1.1.1 Objetivo Geral ...................................................... 17
      1.1.2 Objetivos Específicos ............................................... 17
  1.2 JUSTIFICATIVA ............................................................. 18
  1.3 ESTRUTURA DO TRABALHO ..................................................... 20

2 FUNDAMENTAÇÃO TEÓRICA E REVISÃO DA LITERATURA ................................. 21
  2.1 CONCEITOS FUNDAMENTAIS DA MINERAÇÃO DE PROCESSOS ........................... 21
      2.1.1 Os Três Pilares: Descoberta, Conformidade e Desempenho .............. 22
      2.1.2 Algoritmos de Descoberta: Alpha Miner e Inductive Miner ............. 23
      2.1.3 Ferramentas para Mineração de Processos: ProM e PM4Py ............... 25
  2.2 ANÁLISE DE DADOS EM TRANSPORTE PÚBLICO: CONCEITOS E TÉCNICAS ............... 26
      2.2.1 Mobilidade Urbana e Dados de GPS .................................... 26
      2.2.2 APIs de Transporte Público como Fonte de Dados ...................... 28
      2.2.3 Reconstrução de Trajetórias: Map Matching e Interpolação ............ 29
  2.3 TRABALHOS RELACIONADOS .................................................... 31
      2.3.1 Aplicações de Mineração de Processos ................................ 31
      2.3.2 Análise de Dados de Transporte Urbano ............................... 32
      2.3.3 Interseção: Mineração de Processos Aplicada ao Transporte ........... 33
  2.4 SÍNTESE DO CAPÍTULO ....................................................... 35

3 METODOLOGIA E ENGENHARIA DE DADOS ............................................. 37
  3.1 VISÃO GERAL DA ARQUITETURA DA SOLUÇÃO ..................................... 37
  3.2 OBTENÇÃO E ACESSO AOS DADOS DA API DA URBS ................................ 39
  3.3 PROTOCOLO DE COLETA CONTÍNUA E REGIMES OPERACIONAIS (REGIMES A E B) ........ 41
  3.4 PRÉ-PROCESSAMENTO E FILTRAGEM COM RESTRIÇÃO NA MALHA VIÁRIA (SHAPE) ....... 44
  3.5 RECONSTRUÇÃO DE TRAJETÓRIAS E GERAÇÃO DO LOG DE EVENTOS ................... 47
      3.5.1 Segmentação Semântica de Viagens (Cases) ............................ 47
      3.5.2 Projeção Espacial HMM/Viterbi sobre o Traçado Físico ................ 49
      3.5.3 Estimação Temporal Monotônica via PCHIP e Limiar de Geocerca (150m) . 52
      3.5.4 Padronização com Chaves Canônicas e Incerteza de Sensoriamento ...... 55
      3.5.5 Mecanismo de Qualidade e Taxa de Censura Operacional ................ 57
  3.6 ESTRUTURAÇÃO E EXPORTAÇÃO DO LOG DE EVENTOS (PADRÃO IEEE 1849 / OPENXES) .. 59
  3.7 ARQUITETURA DA PLATAFORMA INTEGRADA DE AUDITORIA OPERACIONAL (FASTAPI E CCO) 62
  3.8 PROTOCOLO DE VALIDAÇÃO E SUÍTE DE TESTES AUTOMATIZADOS (89 TESTES) ........ 66

4 RESULTADOS E DISCUSSÃO ........................................................ 69
  4.1 CARACTERIZAÇÃO DOS DATASETS OPERACIONAIS DA URBS .......................... 69
  4.2 AVALIAÇÃO DO IMPACTO DA CADÊNCIA DE AMOSTRAGEM (REGIME A VS. REGIME B) .... 72
  4.3 DESCOBERTA DE PROCESSOS: IDENTIFICAÇÃO DOS MODELOS REAIS DE OPERAÇÃO ...... 75
  4.4 VERIFICAÇÃO DE CONFORMIDADE: QUANTIFICAÇÃO DE DESVIOS E PARADAS OMITIDAS .. 79
  4.5 ANÁLISE DE DESEMPENHO: MAPEAMENTO DE GARGALOS OPERACIONAIS NO DFG ......... 84
  4.6 PLATAFORMA DE AUDITORIA OPERACIONAL NO CCO E REPLAY ESPAÇOTEMPORAL ....... 89
  4.7 DISCUSSÃO DOS RESULTADOS E IMPACTOS NA FISCALIZAÇÃO DO TRANSPORTE ......... 94

5 CONSIDERAÇÕES FINAIS E CONCLUSÕES ............................................. 98
  5.1 SÍNTESE DAS CONTRIBUIÇÕES CIENTÍFICAS E METODOLÓGICAS ..................... 98
  5.2 CONTRIBUIÇÕES PRÁTICAS PARA A GESTÃO DO TRANSPORTE PÚBLICO DE CURITIBA .... 100
  5.3 LIMITAÇÕES METODOLÓGICAS DO TRABALHO ...................................... 102
  5.4 RECOMENDAÇÕES E TRABALHOS FUTUROS ......................................... 104

REFERÊNCIAS ..................................................................... 107
```
